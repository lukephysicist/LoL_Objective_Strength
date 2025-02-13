import grab as gb

def write_row_vector():
    pass

def combine_features(statics, dynamics, misc):
    return statics + dynamics + misc

def master(match, timeline, team):
    # get static features
    statics = gb.grab_static_features(match, team)
    # get misc cols
    misc = None

    frames = timeline['info']['frames']
    enemy_team = 200 if team==100 else 100
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
        "inhibitors_taken": 0,
        "enemy_inhibitors_taken": 0,
        "enemy_nexus_turrets_taken": 0,
        "feats_of_strength": 0,
        "atakhan": 0,
        "has_soul": 0,         
        "has_shelly": 0,
        
        "baron_exp_at": 0,          # timestamp when runs out, negative if enemy team has
        "elder_exp_at": 0,          # timestamp when runs out, negative if enemy team has

        "grubs_up_at": 0,           ##############
        "herald_up_at": 0,     
        "baron_up_at": 0,           # Timestaps which can then be subtracted from timestamp of the event to calculate: objective_up_in (x seconds)
        "dragon_up_at": 0,
        "elder_up_at": 0,           #############

        "nexus_turrets_respawn": [0,0],   ### lists that hold respawn timestamps for nexus turrets
        "enemy_nexus_turrets_resawn": [0,0],

        "allied_respawns": [0,0,0,0,0], ###### lists that will hold respawn timestamps used to calculate: average_team_respawn (x seconds)
        "enemy_respawns": [0,0,0,0,0],  ######

        "allied_distance_fountain" : [],
        "enemy_distance_fountain" : []
    }
    prev_snapshot = frames[0]['participantFrames']

    # loop through minutes
    for frame in frames[1:]:
        events = frame['events']
        snapshot = prev_snapshot

        # update distance to fountain
        ally_dist = inter_minute["allied_average_distance_fountain"]
        enemy_dist = inter_minute["enemy_average_distance_fountain"]
        
        ally_dist.append(gb.avg_distance_to_fountain(snapshot, team))
        enemy_dist.append(gb.avg_distance_to_fountain(snapshot, enemy_team))
        if len(ally_dist) > 3:
            ally_dist.pop(0)
        if len(enemy_dist) > 3:
            enemy_dist.pop(0)

        # loop through events in minute
        for event in events:
            etype = event['type']
            intra_minute = {
                "kill_diff": 0,
                "gold_diff": 0,
                "allied_lvl_ups": 0,
                "enemy_lvl_ups": 0
            }
            # updating gold, kills, levels
            if etype == "CHAMPION_KILL":
                gold_diff, kill_diff = gb.champ_kill_update(event, team)
                intra_minute["gold_diff"] += gold_diff
                intra_minute["kill_diff"] += kill_diff

            elif etype == "LEVEL_UP":
                leveler = 100 if event["participantId"] < 6 else 200
                if leveler == team:
                    intra_minute["allied_lvl_ups"] += 1
                else:
                    intra_minute["enemy_lvl_ups"] += 1


            # Objective events where row writes occur

            elif etype == "ELITE_MONSTER_KILL":
                if event['monsterType'] == "HORDE":
                    pass

                if event['monsterType'] == "DRAGON":
                    dynamic = gb.create_dynamic_features(team, snapshot, event, inter_minute, intra_minute, etype)
                    vector = combine_features(statics, dynamic, misc)
                    write_row_vector(vector)
                    
                    if event['killerTeamId'] == team:
                        inter_minute['allied_dragons'] += 1
                    else:
                        inter_minute['enemy_dragons'] += 1

                    

    prev_snapshot = frame["participantFrames"]
            

                
