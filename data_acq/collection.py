import grab as gb
import json
import os
from dotenv import load_dotenv
from pulsefire.clients import RiotAPIClient
import pandas as pd
import random
import asyncio
load_dotenv()
API_KEY = os.getenv("RIOTAPI")
script_dir = os.path.dirname(os.path.abspath(__file__))

df = pd.read_parquet(f"{script_dir}/objective_data.parquet")         

player_dict = {}
for rank in ["platinum", "emerald", "diamond", "master", "grandmaster", "challenger"]:
    with open(f'{script_dir}/json_references/{rank}.json', 'r', encoding='utf-8') as file:
        player_dict[rank] = json.load(file)



def write_row_vector(array, statics, team, snapshot, event, inter_minute, intra_minute, objective, rank, region):
    row = gb.create_dynamic_features(team, snapshot, event, inter_minute, intra_minute) + statics[0:5] + tuple(objective) + statics[5:] + tuple(rank, region)
    array.append(row)
    print(f"event written: {objective}")


def save_data(old_df, new_rows):
    temp_df = pd.DataFrame(new_rows, columns=df.columns)
    new_df = pd.concat([old_df,temp_df], ignore_index=True)

    new_df.to_parquet('objective_data.parquet')
    print('data saved')


def calc_match_stats(match_rows, match, timeline, rank, region):

    frames = timeline['info']['frames']
    inter_minute = {
        #static match variables
        "blue_cc_rating": gb.get_aggregate_cc_rating(match, 100),
        "red_cc_rating": gb.get_aggregate_cc_rating(match, 200),
        "blue_is_squishy": gb.team_is_squishy(match, 100),
        "red_is_squishy" : gb.team_is_squishy(match, 200),
        "winner": 100 if match['info']['teams'][0]['win'] == True else 200, 
        "matchId": match['metadata']['matchId'],
        "patch" : gb.get_patch(match),

        #dynamic match variables
        "blue_dragons": 0,
        "red_dragons": 0,
        "blue_grubs": 0,
        "red_grubs": 0,
        "blue_top_turrets_taken": 0,
        "red_top_turrets_taken": 0,
        "blue_mid_turrets_taken": 0,
        "red_mid_turrets_taken": 0,
        "blue_bot_turrets_taken": 0,
        "red_bot_turrets_taken": 0,
        "blue_inhibitors_taken": 0,
        "red_inhibitors_taken": 0,
        "feats_of_strength": 0,
        "atakhan": 0,
        "has_soul": 0,   
        "killed_herald": 0,

        "baron_exp_at": 0,          # timestamp when runs out, negative if red team has
        "elder_exp_at": 0,          # timestamp when runs out, negative if red team has

        "grubs_up_at": 360000,           ##############
        "herald_up_at": 960000,     
        "baron_up_at": 1500000,           # Timestaps which can then be subtracted from timestamp of the event to calculate: objective_up_in (x seconds)
        "dragon_up_at": 300000,
        "elder_up_at": 0,           #############

        "blue_nexus_turrets_respawn": [0,0],   ### lists that hold respawn timestamps for nexus turrets
        "red_nexus_turrets_resawn": [0,0],

        "blue_respawns": [0,0,0,0,0], ###### lists that will hold respawn timestamps used to calculate: average_team_respawn (x seconds)
        "red_respawns": [0,0,0,0,0],  ######

        "blue_distance_fountain" : [],
        "red_distance_fountain" : []
    }
    prev_snapshot = frames[0]['participantFrames']

    # loop through minutes
    for frame in frames[1:]:
        events = frame['events']
        snapshot = prev_snapshot

        # update distance to fountain
        new_distances = gb.avg_distance_to_fountain(snapshot)

        blue_dist = inter_minute["blue_distance_fountain"]
        red_dist = inter_minute["red_distance_fountain"]

        blue_dist.append(new_distances[0])
        red_dist.append(new_distances[1])
        if len(blue_dist) > 3:
            blue_dist.pop(0)
        if len(red_dist) > 3:
            red_dist.pop(0)

        intra_minute = {
                "blue_kill_diff": 0,
                "blue_gold_diff": 0,
                "blue_lvl_ups": 0,
                "red_lvl_ups": 0
                }
        
        # loop through events in minute
        for event in events:
            now = event['timestamp']
            etype = event['type']
            
            # updating gold, kills, levels
            if etype == "CHAMPION_KILL":
                blue_killed = True if event['killerId'] < 6 else False
                intra_minute["blue_gold_diff"] += gb.blue_gold_from_kill(event, blue_killed)
                intra_minute["blue_kill_diff"] += 1 if blue_killed else -1

                victim_index = event['victimId']-1 if blue_killed else event['victimId']-6
                    

            elif etype == "LEVEL_UP":
                leveler = 100 if event["participantId"] < 6 else 200
                if leveler == team:
                    intra_minute["allied_lvl_ups"] += 1
                else:
                    intra_minute["enemy_lvl_ups"] += 1


            # Objective events where row writes occur

            elif etype == "ELITE_MONSTER_KILL":
                if event['monsterType'] == "HORDE":
                    write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'grub', rank, region)

                    if event['killerTeamId'] == team:
                        inter_minute['allied_grubs'] += 1
                    elif event['killerTeamId'] == enemy_team:
                        inter_minute['enemy_grubs'] += 1

                    c1 = inter_minute['allied_grubs'] + inter_minute['enemy_grubs'] == 3
                    c2 = now < 705000
                    if c1 and c2:
                        inter_minute["grubs_up_at"] = now + 240000


                elif event['monsterType'] == "DRAGON":
            
                    if event["monsterSubType"] != "ELDER_DRAGON":
                        write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, event["monsterSubType"], rank, region)
                        if event['killerTeamId'] == team:
                            inter_minute['allied_dragons'] += 1
                        else:
                            inter_minute['enemy_dragons'] += 1


                        if inter_minute['allied_dragons'] == 4:
                            inter_minute['has_soul'] = 1

                        elif inter_minute['enemy_dragons'] == 4:
                            inter_minute["has_soul"] = -1
                            
                    
                        if inter_minute['has_soul'] != 0: 
                            inter_minute["dragon_up_at"] = now + 300000
                        else:
                            inter_minute["elder_up_at"] = now + 360000
                    
                    else:
                        write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'elder', rank, region)
                        if event['killerTeamId'] == team:
                            inter_minute["elder_exp_at"] = now + 150000

                        elif event['killerTeamId'] == enemy_team:
                            inter_minute['killerTeamId'] = -(now+150000)
                    


                elif event['monsterType'] == "ATAKHAN":
                    write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'atakhan', rank, region)

                    if event['killerTeamId'] == team:
                        inter_minute['atakhan'] = 1
                    else:
                        inter_minute['atakhan'] = -1

                elif event['monsterType'] == "RIFTHERALD":
                    write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'riftHerald', rank, region)
                    
                    if event['killerTeamId'] == team:
                        inter_minute['killed_herald'] = 1
                    elif event['killerTeamId'] == enemy_team:
                        inter_minute['killed_herald'] = -1


            elif etype == "DRAGON_SOUL_GIVEN":
                
                    

        prev_snapshot = frame["participantFrames"]



async def pick_match(rank, table):
    player = random.choice(player_dict[rank])
    pre_region = player['Region']
    match pre_region:
        case 'na1':
            region = 'americas'
        case 'euw1':
            region = 'europe'
        case 'kr':
            region = 'asia'

    async with RiotAPIClient(default_headers={"X-Riot-Token": API_KEY}) as client: 

        summoner = await client.get_lol_summoner_v4_by_id(region=pre_region, id=player['summonerId'])

        matches = await client.get_lol_match_v5_match_ids_by_puuid(region=region,
                                                               puuid=summoner['puuid'],
                                                               queries = {'count':100})
    while True:
        match_id = random.choice(matches)
        if not match_id in table['MatchID']:
            break

    choice = (match_id, region, pre_region)
    return choice            


async def main():
    new_data = []
    try:
        while True:
            for rank in ["platinum", "emerald", "diamond", "master", "grandmaster", "challenger"]:
                try:
                    matchID, region, player_region = await pick_match(rank,df)

                    async with RiotAPIClient(default_headers={"X-Riot-Token": API_KEY}) as client: 
                        league_match = await client.get_lol_match_v5_match(region=region,
                                                                        id=matchID)
                        timeline = await client.get_lol_match_v5_match_timeline(region=region,
                                                                        id=matchID)
                except Exception:
                    continue
                if not gb.is_valid_game(league_match):
                    continue
                calc_match_stats(new_data, league_match, timeline, rank, player_region)
    except KeyboardInterrupt:
        print('interupt')
    except Exception as e:
        print(f'errored out: {e}')
    finally:
        save_data(old_df=df, games=new_data)
        


asyncio.run(main())