from event_names import objective_events, stat_events
import grab as gb

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
                killer = 100 if event['killerId'] < 6 else 200
                if team == killer:
                    intra_minute["kill_diff"] += 1
                    intra_minute["gold_diff"] += event["bounty"] + event["shutdown_bounty"]
                else:
                    intra_minute["kill_diff"] -= 1
                    intra_minute["gold_diff"] -= event["bounty"] - event["shutdown_bounty"]

                
