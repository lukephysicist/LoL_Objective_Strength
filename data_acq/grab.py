import json
import os
import numpy as np
import re
import math

script_dir = os.path.dirname(os.path.realpath(__file__))

#########################
##  JSON REFFERENCES   ##
#########################

def get_cc_score_from_champ(champ_name):

    json_path = os.path.join(script_dir, 'json_references\\cc_ratings.json')
    
    with open(json_path, 'r', encoding='utf-8') as file:
        mapping = json.load(file)
    
    return mapping[champ_name]


def is_champ_frontline(name):
    json_path = os.path.join(script_dir, 'json_references\\is_frontline.json')
    
    with open(json_path, 'r', encoding='utf-8') as file:
        mapping = json.load(file)
    
    return mapping[name]


########################
##  TEAM COMPOSITION  ##
########################

# calculated by adding up the cc rating of every champ on the team
def get_aggregate_cc_rating(match, team):
    players = pick_team(match, team)
    cc_score = 0
    for player in players:
        cc_score += get_cc_score_from_champ(player['championName'])

    return cc_score


# A team is squishy IF: They have less than two fronliners/bruisers AND they have no tanks
def team_is_squishy(match, team):
    champs = pick_team(match, team)

    team_frontline_score = sum([is_champ_frontline(champ['championName']) for champ in champs])

    return 1 if team_frontline_score < 2 else 0


def damage_type_ratio(snapshot, team):
    if team == 100:
        blue_magic = sum([value['damageStats']["magicDamageDoneToChampions"] for value in list(snapshot.values())[:5]])
        blue_phys = sum([value['damageStats']["physicalDamageDoneToChampions"] for value in list(snapshot.values())[:5]])
        return blue_phys/blue_magic
    else:
        red_magic = sum([value['damageStats']["magicDamageDoneToChampions"] for value in list(snapshot.values())[5:]])
        red_phys = sum([value['damageStats']["physicalDamageDoneToChampions"] for value in list(snapshot.values())[5:]])
        return red_phys/red_magic


##################
##### STATS ######
##################

def blue_gold_from_kill(event, blue_killed):

    gold_diff = event["bounty"] + event["shutdownBounty"]
    assist_pool = (.7*event["bounty"]) + (.28*event["shutdownBounty"])
    n_assistants = len(event['assistingParticipantIds'])
    if (assist_pool/n_assistants) > 150:
        gold_diff += (n_assistants*150)
    else:
        gold_diff += (assist_pool)
    
    return gold_diff if blue_killed else -gold_diff

def get_gold_difference(snapshot, intra_minute, team):
    blue = sum([value['totalGold'] for value in list(snapshot.values())[:5]])
    red = sum([value['totalGold'] for value in list(snapshot.values())[5:]])

    difference = blue - red + intra_minute['blue_gold_diff'] if team == 100 else red - blue - intra_minute['blue_gold_diff']

    return difference

def get_avg_level(inter_minute, team):
    if team == 100:
        return np.mean(inter_minute['blue_levels'])
    else:
        return np.mean(inter_minute['red_levels'])


def avg_distance_to_fountain(snapshot):
    positions = np.array([list(p['position'].values()) for p in snapshot.values()])
    
    blue_fountain = np.array([499.4, 386])
    blue_distances = np.linalg.norm(positions[:5] - blue_fountain, axis=1)
     
    red_fountain = np.array([14445.4, 14316])
    red_distances = np.linalg.norm(positions[5:] - red_fountain, axis=1)
    
    return (np.mean(blue_distances), np.mean(red_distances))


def till_thing(inter_minute, event, thing, team=100):
    now = event['timestamp']
    if thing == "nt":
        blue_nt1_respawn, blue_nt2_respawn = inter_minute['blue_nexus_turrets_respawn']
        red_nt1_respawn, red_nt2_respawn = inter_minute['red_nexus_turrets_respawn']

        till_blue_nt1 = seconds_till(blue_nt1_respawn, now)
        till_blue_nt2 = seconds_till(blue_nt2_respawn, now)
        till_red_nt1 = seconds_till(red_nt1_respawn, now)
        till_red_nt2 = seconds_till(red_nt2_respawn, now)

        if team == 100:
            return (till_blue_nt1, till_blue_nt2, till_red_nt1, till_red_nt2)
        else:
            return (till_red_nt1, till_red_nt2, till_blue_nt1, till_blue_nt2)
    
    if thing == 'inhibs':
        blue_inhib1, blue_inhib2, blue_inhib3 = inter_minute["blue_inhibs_respawn"]
        red_inhib1, red_inhib2, red_inhib3 = inter_minute["red_inhibs_respawn"]

        if team == 100:
            return (seconds_till(blue_inhib1, now), seconds_till(blue_inhib2, now), seconds_till(blue_inhib3, now))
        else:
            return (seconds_till(red_inhib1, now), seconds_till(red_inhib2, now), seconds_till(red_inhib3, now))

    
    if thing == "avg_allied_respawn":
        if team == 100:
            avg = sum(inter_minute["blue_respawns"]) / 5
            return seconds_till(avg, now)
        else:
            avg = sum(inter_minute["red_respawns"]) / 5
            return seconds_till(avg, now)
    
    elif thing == "avg_enemy_respawn":
        if team == 100:
            avg = sum(inter_minute['red_respawns']) / 5
            return seconds_till(avg, now)
        else:
            avg = sum(inter_minute['blue_respawns']) / 5
            return seconds_till(avg, now)
    
    elif thing in ["baron_exp_at", "elder_exp_at"]:
        timestamp = inter_minute[thing]
        enemy_has = ((team == 100 and timestamp<0) or (not team == 100 and timestamp>0))
        timestamp = abs(timestamp)
       
        if enemy_has:
            return -seconds_till(timestamp, now)
        else:
            return seconds_till(timestamp, now) 
    
    # this is for obj_up_at
    else:
        timestamp = inter_minute[f'{thing}']
        return seconds_till(timestamp,now)
        
def get_death_timer(level, now):
    level_to_base = {
        1:10, 2:10, 3:12, 4:12, 5:14, 6:16, 7:20, 8:25, 9:28, 
        10:32.5, 11:35, 12:37.5, 13:40, 14:42.5, 15:45, 16:47.5, 17:50, 18:52.5
    }
    base = level_to_base[level]
    if now < 900000:
        multiplier = 0
    elif now < 1800000:
        multiplier = math.ceil(2*((now/60000)-15))*.00425
    elif now < 2700000:
        multiplier =  12.5 + math.ceil(2*((now/60000)-30))*.003
    else:
        multiplier = 21.75 + math.ceil(2*((now/60000)-45))*.0145
    multiplier = .5 if multiplier > .5 else multiplier
    seconds = base + (base*multiplier)
    
    return seconds*60000
        

def inter_minute_grabber(inter_minute, team, thing):
    if thing == "distance_fountain":
        if team == 100:
            return np.mean(inter_minute[f'blue_{thing}'])
        else:
            return np.mean(inter_minute[f'red_{thing}'])
        
    elif thing in ["feats_of_strength", "atakhan", "has_soul", "killed_herald"]:
        if inter_minute[thing] == 0:
            return 0
        elif inter_minute[thing] == team:
            return 1
        else:
            return -1
        
    else:
        if team == 100:
            return inter_minute[f'blue_{thing}']
        else:
            return inter_minute[f'red_{thing}']


###################
## MISCELLANEOUS ##
###################


def create_dynamic_features(team, snapshot, event, inter_minute, intra_minute):
    team, enemy_team = assign_teams(team)
    till_allied_nt1, till_allied_nt2, till_enemy_nt1, till_enemy_nt2 = till_thing(inter_minute, event, 'nt')
    till_allied_inhib1, till_allied_inhib2, till_allied_inhib3 = till_thing(inter_minute, event, 'inhibs', team)
    till_enemy_inhib1, till_enemy_inhib2, till_enemy_inhib3 = till_thing(inter_minute, event, 'inhibs', enemy_team)

    
    vector = (
        damage_type_ratio(snapshot, team),                                                  #damageTypeRatio
        get_gold_difference(snapshot, intra_minute, team),                                  #goldDifference
        #AM I ADDING KILL DIFF HERE?
        get_avg_level(inter_minute, team),                                                  #averageAllyLvl
        get_avg_level(inter_minute, enemy_team),                                            #averageEnemyLvl 
        inter_minute_grabber(inter_minute, team, 'distance_fountain'),                      #averageAllyToFountain
        inter_minute_grabber(inter_minute, enemy_team, 'distance_fountain'),                #averageEnemytoFountain
        inter_minute_grabber(inter_minute, team, 'dragons'),                                #alliedDragons
        inter_minute_grabber(inter_minute, enemy_team, 'dragons'),                          #enemyDragons
        inter_minute_grabber(inter_minute, team, 'grubs'),                                  #alliedGrubs
        inter_minute_grabber(inter_minute, enemy_team, 'grubs'),                            #enemyGrubs
        inter_minute_grabber(inter_minute, team, 'top_turrets'),                            #topTurrets
        inter_minute_grabber(inter_minute, enemy_team, 'top_turrets'),                      #enemytopTurrets
        inter_minute_grabber(inter_minute, team, 'mid_turrets'),                            #midTurrets
        inter_minute_grabber(inter_minute, enemy_team, 'mid_turrets'),                      #enemyMidTurrets
        inter_minute_grabber(inter_minute, team, 'bot_turrets'),                            #botTurrets
        inter_minute_grabber(inter_minute, enemy_team, 'bot_turrets'),                      #enemyBotTurrets
        till_allied_nt1,                                                                    #tillAlliedNT1
        till_allied_nt2,                                                                    #tillAlliedNT2
        till_enemy_nt1,                                                                     #tillEnemyNT1
        till_enemy_nt2,                                                                     #tillEnemyNT2
        till_allied_inhib1,                                                                 #tillAliledInhib1
        till_allied_inhib2,                                                                 #tillAliledInhib1
        till_allied_inhib3,                                                                 #tillAliledInhib2
        till_enemy_inhib1,                                                                  #tillEnemeyInhib1
        till_enemy_inhib2,                                                                  #tillEnemeyInhib2
        till_enemy_inhib3,                                                                  #tillEnemeyInhib3
        inter_minute_grabber(inter_minute, team, 'feats_of_strength'),                      #featsOfStrength
        inter_minute_grabber(inter_minute, team, 'atakhan'),                                #atakhan
        inter_minute_grabber(inter_minute, team, 'has_soul'),                               #hasSoul
        inter_minute_grabber(inter_minute, team, 'killed_herald'),                          #killedHerald
        inter_minute['soul_type'],                                                          #soulType
        till_thing(inter_minute, event, "baron_exp_at", team),                              #untilBaronExp
        till_thing(inter_minute, event, "elder_exp_at", team),                              #untilElderExp
        till_thing(inter_minute, event, "grubs_up_at"),                                     #untilGrubsSpawn
        till_thing(inter_minute, event, "herald_up_at"),                                    #untilHeraldSpawn
        till_thing(inter_minute, event, "baron_up_at"),                                     #untilBaronSpawn
        till_thing(inter_minute, event, "dragon_up_at"),                                    #untilDragonSpawn
        till_thing(inter_minute, event, "elder_up_at"),                                     #untilElderSpawn
        till_thing(inter_minute, event, "avg_allied_respawn", team),                        #avgAlliedRespawn
        till_thing(inter_minute, event, "avg_enemy_respawn", enemy_team),                   #avgEnemyRespawn
        event['timestamp'] / 60000,                                                         #secondsElapsed      
    )

    return vector


def pick_team(match, team):
    participants = match['info']['participants']
    if team == 100:
        champs = participants[:5]
    else:
        champs = participants[5:]
    return champs


def won_game(match, team):
    outcome = match['info']['teams'][0]['win']

    if team == 100:
        return 1 if outcome else 0
    
    if team == 200:
        return 0 if outcome else 1
    

def timestamp_matcher(timestamp, game_minute):
    if abs(int(timestamp) - (game_minute * 60000)) < 2000:
        return True
    else:
        return False
    

def get_patch(match):
    version = match['info']['gameVersion']
    patch = version.split('.')
    
    return ".".join(patch[0:2])

def seconds_till(timestamp, now):
    till = (timestamp - now)/1000
    return till if till>0 else 0

def is_valid_game():
    pass

def assign_teams(teamId):
    team = teamId
    enemy_team = 100 if teamId == 200 else 200
    
    return team, enemy_team