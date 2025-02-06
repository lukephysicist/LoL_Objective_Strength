import grab as gb
import numpy as np


def master(match, timeline, team):
    frames = timeline['info']['frames']

    inter_minute = {
        "allied_dragons": 0,
        "enemy_dragons": 0,
        "allied_grubs": 0,
        "enemy_grubs": 0,
        "top_turrets_taken": 0,
        "enemy_top_turrets_taken": 0,
        "mid_turrets_taken": 0,
        "enemy_mid_turrets_taken": 0,
        "bot_turrets_taken": 0,
        "enemy_bot_turrets_taken": 0,
        "inhibitors_taken" :0,
        "enemy_inhibitors_taken": 0,
        "nexus_turrets_taken": 0,
        "enemy_nexus_turrets_taken": 0,
        "feats_of_strength": 0,
        "atakhan": 0,
        "has_soul": 0,
        "has_shelly": 0,
        "has_baron": 0,
        "has_elder": 0,
        "grubs_up_at": 0,   ##############
        "herald_up_at": 0,     
        "baron_up_at": 0,   # Timestaps which can then be subtracted from timestamp of the event to calculate: objective_up_in (x seconds)
        "dragon_up_at": 0,
        "elder_up_at": 0,   #############

        "allied_respawns": [], ###### lists that will hold respawn timestamps used to calculate: average_team_respawn (x seconds)
        "enemy_respawns": [],  ######
    }
    prev_snapshot = None
    for frame in frames:
        events = frame['events']
        snapshot = prev_snapshot

        for event in events:
            intra_minute = {
                "kill_diff": 0,
                "gold_diff": 0,
                "allied_lvl_ups": 0,
                "enemy_lvl_ups": 0
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


            # Objective events where row writes occur
            elif event['type'] == "ELITE_MONSTER_KILL":
                if event['monsterType'] == "HORDE":
                    vector = (
                        timeline["metadata"]["matchId"],
                        team,
                    )
                    vector.extend(gb.create_feature_row_vector(match, team, snapshot, event, inter_minute, intra_minute))
                    

    prev_snapshot = frame["participantFrames"]
            

                
