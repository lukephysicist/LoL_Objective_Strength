import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_acq.collection import calc_match_stats
import pandas as pd
import json

# test_df = pd.read_parquet('testdata.parquet')

# with open('test_match.json', 'r') as file:
#     league_match = json.load(file)

# with open('test_timeline.json', 'r') as file:
#     timeline = json.load(file)

# data = []
# calc_match_stats(data, league_match, timeline, 'silver', 'na1')

# new_df = pd.DataFrame(data)

# if new_df == test_df:
#     print("Test Passed")
# else:
#     print("Test Failed")
#     new_df.to_parquet('failed_testdata.parquet')