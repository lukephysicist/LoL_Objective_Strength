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

################################
## WORKS FOR PATCH 15.2 OR NEWER
################################

df = pd.read_parquet(f"{script_dir}/objective_data.parquet")         

player_dict = {}
for rank in ["platinum", "emerald", "diamond", "master", "grandmaster", "challenger"]:
    with open(f'{script_dir}/json_references/{rank}.json', 'r', encoding='utf-8') as file:
        player_dict[rank] = json.load(file)


def write_row_vector(array, statics, team, snapshot, event, inter_minute, intra_minute, objective, rank, region):
    row = gb.create_dynamic_features(team, snapshot, event, inter_minute, intra_minute) + statics[0:5] + tuple([objective,team]) + statics[5:] + tuple([rank, region])
    array.append(row)
    


def save_data(old_df, new_rows):
    temp_df = pd.DataFrame(new_rows, columns=df.columns)
    new_df = pd.concat([old_df,temp_df], ignore_index=True)

    new_df.to_parquet('data_acq/objective_data.parquet')
    print('data saved')


def calc_match_stats(match_rows, match, timeline, rank, region):
    blue_statics = (
        gb.get_aggregate_cc_rating(match, 100),         #CCScore
        gb.get_aggregate_cc_rating(match, 200),         #enemyCCScore
        gb.team_is_squishy(match, 100),                 #isSquishy
        gb.team_is_squishy(match, 200),                 #vsSquishy
        1 if match['info']['teams'][0]['win'] else 0,   #won
        match['metadata']['matchId'],                   #matchId
        gb.get_patch(match)                             #patch
    )
    red_statics = (
        gb.get_aggregate_cc_rating(match, 200),         #CCScore
        gb.get_aggregate_cc_rating(match, 100),         #enemyCCScore
        gb.team_is_squishy(match, 200),                 #isSquishy
        gb.team_is_squishy(match, 100),                 #vsSquishy
        0 if match['info']['teams'][0]['win'] else 1,   #won
        match['metadata']['matchId'],                   #matchId
        gb.get_patch(match)                             #patch
    )
    frames = timeline['info']['frames']
    inter_minute = {
        "blue_dragons": 0,
        "red_dragons": 0,
        "blue_grubs": 0,
        "red_grubs": 0,
        "blue_top_turrets": 3,
        "red_top_turrets": 3,
        "blue_mid_turrets": 3,
        "red_mid_turrets": 3,
        "blue_bot_turrets": 3,
        "red_bot_turrets": 3,
        "feats_of_strength": 0,
        "atakhan": 0,
        "has_soul": 0,   
        "killed_herald": 0,
        "herald_deployed": 0,

        "baron_exp_at": 0,          # timestamp when runs out, negative if red team has
        "elder_exp_at": 0,          # timestamp when runs out, negative if red team has

        "grubs_up_at": 360000,      ##############
        "herald_up_at": 960000,     
        "baron_up_at": 1500000,     # Timestaps which can then be subtracted from timestamp of the event to calculate: objective_up_in (x seconds)
        "dragon_up_at": 300000,
        "elder_up_at": -1,           #############
        "soul_type": "Unknown",

        "blue_nexus_turrets_respawn": [0,0],   ### lists that hold respawn timestamps for nexus turrets
        "red_nexus_turrets_respawn": [0,0],
        "blue_inhibs_respawn": [0,0,0],
        "red_inhibs_respawn": [0,0,0],

        "blue_levels": [1,1,1,1,1],
        "red_levels" : [1,1,1,1,1],
        "blue_respawns": [0,0,0,0,0], ###### lists that will hold respawn timestamps used to calculate: average_team_respawn (x seconds)
        "red_respawns": [0,0,0,0,0],  ######

        "blue_distance_fountain" : [],
        "red_distance_fountain" : []
    }
    feats_tracker = {
        "red_epic_kills": 0, 
        "blue_epic_kills": 0,
        "red_champ_kills": 0,
        "blue_champ_kills": 0,
        "blue_grub_batch_kills": 0,

        "fos_first_tower": 0,
        "fos_objectives": 0,  
        "fos_kills": 0,       
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

                victim_index = event['victimId']-6 if blue_killed else event['victimId']-1
                victim_level = (inter_minute["red_levels"][victim_index] if blue_killed 
                                else inter_minute["blue_levels"][victim_index])
                death_timer = gb.get_death_timer(victim_level, now)
                if blue_killed:
                    inter_minute['red_respawns'][victim_index] = death_timer + now
                    feats_tracker['blue_champ_kills'] += 1
                else:
                    inter_minute['blue_respawns'][victim_index] = death_timer + now
                    feats_tracker['red_champ_kills'] += 1

            elif etype == "LEVEL_UP":
                blue_leveled = True if event["participantId"] < 6 else False
                leveler_index = event["participantId"]-1 if blue_leveled else event["participantId"]-6
                if blue_leveled:
                    inter_minute["blue_levels"][leveler_index] += 1
                else:
                    inter_minute["red_levels"][leveler_index] += 1


        # Objective events where row writes occur
            elif etype == "ELITE_MONSTER_KILL":

                if event['monsterType'] == "HORDE":
                    team = event["killerTeamId"]
                    if team == 300:
                        continue
                    statics = blue_statics if team == 100 else red_statics
                    write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'grub', rank, region)

                    if team == 100:
                        inter_minute['blue_grubs'] += 1
                        feats_tracker['blue_grub_batch_kills'] += 1
                    else:
                        inter_minute['red_grubs'] += 1
                        feats_tracker['blue_grub_batch_kills'] -= 1

                    camp_cleared = (inter_minute['red_grubs'] + inter_minute['blue_grubs']) % 3 == 0
                    before_respawn_limit = now < 705000
                    if camp_cleared:
                        if before_respawn_limit and inter_minute['red_grubs'] + inter_minute['blue_grubs'] <= 3:
                            inter_minute["grubs_up_at"] = now + 240000
                        else:
                            inter_minute['grubs_up_at'] = -1

                        if feats_tracker['blue_grub_batch_kills'] == 3:
                            feats_tracker['blue_epic_kills'] += 1
                        elif feats_tracker['blue_grub_batch_kills'] == -3:
                            feats_tracker['red_epic_kills'] += 1
                        feats_tracker['blue_grub_batch_kills'] = 0



                elif event['monsterType'] == "DRAGON":
                    team = event['killerTeamId']
                    team_name = "blue" if team == 100 else "red"
                    if event["monsterSubType"] != "ELDER_DRAGON":
                        gaining_soul = inter_minute[f'{team_name}_dragons'] == 3
                        if gaining_soul:
                            etype = f'{inter_minute['soul_type']}_dragon_soul'
                        else: 
                            etype = event['monsterSubType']
                        statics = blue_statics if team == 100 else red_statics
                        write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, etype, rank, region)
                        
                        if team == 100:
                            inter_minute['blue_dragons'] += 1
                            feats_tracker['blue_epic_kills'] += 1
                        else:
                            inter_minute['red_dragons'] += 1
                            feats_tracker['red_epic_kills'] += 1


                        if inter_minute['blue_dragons'] == 4:
                            inter_minute['has_soul'] = 100
                            inter_minute['dragon_up_at'] = -1
                            inter_minute['elder_up_at'] = now + 360000

                        elif inter_minute['red_dragons'] == 4:
                            inter_minute["has_soul"] = 200
                            inter_minute["dragon_up_at"] = -1
                            inter_minute['elder_up_at'] = now + 360000
                        else:
                            inter_minute['dragon_up_at'] = now + 300000
                    
                    else:
                        statics = blue_statics if team == 100 else red_statics
                        write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'elder', rank, region)
                        if team == 100:
                            inter_minute["elder_exp_at"] = now + 150000
                            feats_tracker['blue_epic_kills'] += 1
                        else:
                            inter_minute['elder_exp_at'] = -(now+150000)
                            feats_tracker['red_epic_kills'] += 1

                        inter_minute["elder_up_at"] = now + 360000
                        
                    

                elif event['monsterType'] == "ATAKHAN":
                    team = event["killerTeamId"]
                    statics = blue_statics if team == 100 else red_statics
                    write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'atakhan', rank, region)

                    if team == 100:
                        inter_minute['atakhan'] = 100
                        feats_tracker['blue_epic_kills'] += 1
                    else:
                        inter_minute['atakhan'] = 200
                        feats_tracker['red_epic_kills'] += 1


                elif event['monsterType'] == "RIFTHERALD":
                    team = event["killerTeamId"]
                    if team == 300:
                        continue
                    statics = blue_statics if team == 100 else red_statics
                    write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'riftHerald', rank, region)
                    if team == 100:
                        inter_minute['killed_herald'] = 100
                        intra_minute['blue_gold_diff'] += 200
                        feats_tracker['blue_epic_kills'] += 1
                    else:
                        inter_minute['killed_herald'] = 200
                        intra_minute['blue_gold_diff'] -= 200
                        feats_tracker['red_epic_kills'] += 1
                    inter_minute['herald_up_at'] = -1


                elif event['monsterType'] == "BARON_NASHOR":
                    team = event["killerTeamId"]
                    statics = blue_statics if team == 100 else red_statics
                    write_row_vector(match_rows, statics, team, snapshot, event, inter_minute, intra_minute, 'baron', rank, region)

                    exp_timestamp = now + 180000
                    inter_minute['baron_exp_at'] = exp_timestamp if team == 100 else -exp_timestamp

                    if team == 100:
                        intra_minute['blue_gold_diff'] += 1500
                        feats_tracker['blue_epic_kills'] += 1
                    else:
                        intra_minute['blue_gold_diff'] -= 1500
                        feats_tracker['red_epic_kills'] += 1
                    inter_minute['baron_up_at'] = now + 360000


            elif etype == "DRAGON_SOUL_GIVEN":
                if event['teamId'] == 0:
                    inter_minute["soul_type"] = event['name']
        


            elif etype == "BUILDING_KILL":
                killer_team = 100 if event["teamId"] == 200 else 200
                killed_team_name = "blue" if killer_team == 200 else "red"
                statics = blue_statics if killer_team == 100 else red_statics
                if event["buildingType"] == "TOWER_BUILDING":
                    if feats_tracker['fos_first_tower'] == 0:
                        feats_tracker['fos_first_tower'] = killer_team
                    lane = gb.lane_mapper[event['laneType']]
                    tier = gb.tower_tier_mapper[event['towerType']]

                    if tier != 'nexus':
                        objective = "".join([lane,tier])
                        write_row_vector(match_rows, statics, killer_team, snapshot, event, inter_minute, intra_minute, objective, rank, region)
                        inter_minute[f"{killed_team_name}_{lane}_turrets"] -= 1
                        if tier == "T1":
                            if killer_team == 100:
                                intra_minute['blue_gold_diff'] += 500
                            else:
                                intra_minute['blue_gold_diff'] -= 500
                        elif tier == "T2":
                            if killer_team == 100:
                                intra_minute['blue_gold_diff'] += 675
                            else:
                                intra_minute['blue_gold_diff'] -= 675
                        elif tier == "T3":
                            if killer_team == 100:
                                intra_minute['blue_gold_diff'] += 500
                            else:
                                intra_minute['blue_gold_diff'] -= 500
                    
                    elif tier == 'nexus':
                        write_row_vector(match_rows, statics, killer_team, snapshot, event, inter_minute, intra_minute, 'nexusTurret', rank, region)
                        x = event['position']['x']
                        index = 0 if x == 1748 or x == 12611 else 1
                        inter_minute[f"{killed_team_name}_nexus_turrets_respawn"][index] = now + 180000

        
                elif event["buildingType"] == "INHIBITOR_BUILDING":
                    lane = gb.lane_mapper[event['laneType']]
                    write_row_vector(match_rows, statics, killer_team, snapshot, event, inter_minute, intra_minute, f'{lane}Inhib', rank, region)
                    timers = inter_minute[f"{killed_team_name}_inhibs_respawn"]
                    if lane == 'top':
                        timers[0] = now + 300000
                    elif lane == 'mid':
                        timers[1] = now + 300000
                    elif lane == 'bot':
                        timers[2] = now + 300000
            

            elif etype == "ITEM_DESTROYED":
                if event["itemId"] == 3513:
                    inter_minute['herald_deployed'] = 1


            # check for feats of strength
            if inter_minute['feats_of_strength'] == 0:
                if feats_tracker['fos_kills'] == 0:
                    if feats_tracker['blue_champ_kills'] == 3:
                        feats_tracker['fos_kills'] = 100
                    elif feats_tracker['red_champ_kills'] == 3:
                        feats_tracker['fos_kills'] = 200
                if feats_tracker['fos_objectives'] == 0:
                    if feats_tracker['blue_epic_kills'] == 3:
                        feats_tracker['fos_objectives'] = 100
                    elif feats_tracker['red_epic_kills'] == 3:
                        feats_tracker['fos_objectives'] = 200
                
                if list(feats_tracker.values()).count(100) == 2:
                    inter_minute['feats_of_strength'] = 100
                    write_row_vector(match_rows, blue_statics, 100, snapshot, event, inter_minute, intra_minute, 'feats', rank, region)
                elif list(feats_tracker.values()).count(200) == 2:
                    inter_minute['feats_of_strength'] = 200
                    write_row_vector(match_rows, red_statics, 200, snapshot, event, inter_minute, intra_minute, 'feats', rank, region)

                            
            prev_snapshot = frame["participantFrames"]
    print(f"game written: {match['metadata']['matchId']}")



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
        matches = await client.get_lol_match_v5_match_ids_by_puuid(region=region,
                                                               puuid=player['puuid'],
                                                               queries = {'count':20})
    for match in matches:
        if not match in table['matchId']:
            return (match, region, pre_region)

             


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
                if not gb.is_valid_game(league_match,'15.2'):
                    continue
                calc_match_stats(new_data, league_match, timeline, rank, player_region)
    except KeyboardInterrupt:
        print('interupt')
    except Exception as e:
        print(f'errored out: {e}')
    finally:
        save_data(old_df=df, new_rows=new_data)
        


if __name__ == "__main__":
    asyncio.run(main())