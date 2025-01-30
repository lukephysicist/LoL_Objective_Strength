import grab as gb
import numpy as np



def master(timeline, team):
    frames = timeline['info']['frames']

    inter_minute = {}

    for frame in frames:
        events = frame['events']
        stat_snapshot = frame['participantFrames']

        for event in events:
            intra_minute = {
                "kill_diff": 0,
                "gold_diff": 0,
                "allied_lvl_ups": 0,
                "enemy_lvl_ups": 0,

            }
            if event['type'] == "CHAMPION_KILL":
                gold_diff, kill_diff = gb.champ_kill_update(event, team)
                intra_minute["gold_diff"] += gold_diff
                intra_minute["kill_diff"] += kill_diff

            elif event['type'] == "LEVEL_UP":
                leveler = 100 if event["participantId"] < 6 else 200
                if leveler == team:
                    intra_minute["allied_lvl_ups"] += 1
                else:
                    intra_minute["enemy_lvl_ups"] += 1

            elif event['type'] == "ELITE_MONSTER_KILL":
                

            

                
