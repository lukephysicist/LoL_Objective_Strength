import pandas as pd
import numpy as np

def prediction_columns(df: pd.DataFrame):
    return df.drop(columns=['won', 'objective', 'matchId', 'patch', 'region'])


def merge_small_bins(df: pd.DataFrame) -> pd.DataFrame:
    merged = []
    bin_edges = np.linspace(0, 1, 31)
    for obj, group in df.groupby('objective'):

        group = group.copy()
        group['bucket'] = pd.cut(group['pre_pred'], bins=bin_edges)
        counts = group['bucket'].value_counts().sort_index()

        bins = counts.index.tolist()
        merged_bins = []
        current_bin = None
        current_count = 0

        for b in bins:
            if current_bin is None:
                current_bin = b
                current_count = counts[b]  
            else:
                current_count += counts[b]
            
            if current_count < 30:
                continue
            new_bin = pd.Interval(left=current_bin.left, right=b.right, closed='right')
            merged_bins.append((new_bin, current_count))
            current_bin = None
            current_count = 0
        
        if current_bin is not None:
            new_bin = pd.Interval(left=current_bin.left, right=current_bin.right, closed='right')
            merged_bins.append((new_bin, current_count))
        
        # Re-bin the original rows using merged bin edges
        edges = sorted(set([bin[0].left for bin in merged_bins] + [merged_bins[-1][0].right]))
        group['merged_bucket'] = pd.cut(group['pre_pred'], bins=edges, include_lowest=True)

        merged.append(group)
    
    return pd.concat(merged)


def calc_mean_ci(bucket_stats: pd.DataFrame) -> dict:
    stats = {}
    for obj, group in bucket_stats.groupby('objective'):
        # calcaulte weighted mean
        n_observations_obj = group['n'].sum()
        means = group['m']
        n_observations_buckets = group['n']

        bucket_weighted_means = np.sum(n_observations_buckets * means) / n_observations_obj

        # calculate ci
        bucket_variences = group['var'] 
        objective_varience = np.sum(np.multiply(n_observations_buckets, bucket_variences)) / (n_observations_obj ** 2)

        z = 1.96 # for 95% ci

        left = bucket_weighted_means - (z * np.sqrt(objective_varience))
        right = bucket_weighted_means + (z * np.sqrt(objective_varience))
        ci = (left, right)

        stats[obj] = (bucket_weighted_means, ci)
        
    return stats


def analyze(predicted_df: pd.DataFrame) -> dict:

    bin_edges = np.linspace(0, 1, 31)
    predicted_df['bucket'] = pd.cut(predicted_df['pre_pred'], bins=bin_edges)
    
    sample_merged = merge_small_bins(predicted_df)

    bucket_stats = (sample_merged.groupby(['objective','merged_bucket'])['win_delta']
        .agg(n='count', m='mean', var = lambda x: x.var(ddof=1))
        .reset_index()
    )
    return calc_mean_ci(bucket_stats)