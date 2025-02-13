import json
import os
import numpy as np
import re

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



############
## EVENTS ##
############

def champ_kill_update(event, team): # returns tuple (gold_diff, kill_diff)
    killer = 100 if event['killerId'] < 6 else 200
    kill_diff = 0
    gold_diff = 0
    if team == killer:
        kill_diff += 1
        gold_diff += event["bounty"] + event["shutdownBounty"]
        assist_pool = (.7*event["bounty"]) + (.28*event["shutdownBounty"])
        n_assistants = len(event['assistingParticipantIds'])
        if (assist_pool/n_assistants) > 150:
            gold_diff += (n_assistants*150)
        else:
            gold_diff += (assist_pool)
    else:
        kill_diff -= 1
        gold_diff -= event["bounty"] + event["shutdownBounty"]
        assist_pool = (.7*event["bounty"]) + (.28*event["shutdownBounty"])
        n_assistants = len(event['assistingParticipantIds'])
        if (assist_pool/n_assistants) > 150:
            gold_diff -= (n_assistants*150)
        else:
            gold_diff -= (assist_pool)
    
    return (gold_diff, kill_diff)


##################
##### STATS ######
##################

def get_gold_difference(snapshot, intra_minute, team):
    blue = sum([value['totalGold'] for value in list(snapshot.values())[:5]])
    red = sum([value['totalGold'] for value in list(snapshot.values())[5:]])

    print(red, blue)

    difference = blue - red + intra_minute['gold_diff'] if team == 100 else red - blue + intra_minute['gold_diff']

    return difference

def get_avg_level(snapshot, intra_minute, team):
    if team == 100:
        aggregate = sum([value['level'] for value in list(snapshot.values())[:5]]) 
        aggregate += intra_minute['allied_lvl_ups']
    else:
        aggregate = sum([value['level'] for value in list(snapshot.values())[5:]]) 
        aggregate += intra_minute['enemy_lvl_ups']
    return aggregate / 5
    

def avg_distance_to_fountain(snapshot, team):
    positions = np.array([list(p['position'].values()) for p in snapshot.values()])
    
    if team == 100:
        fountain = np.array([499.4, 386])
        distances = np.linalg.norm(positions[:5] - fountain, axis=1)
    else: 
        fountain = np.array([14445.4, 14316])
        distances = np.linalg.norm(positions[5:] - fountain, axis=1)
    
    return np.mean(distances)


def till_thing(inter_minute, event, thing):
    now = event['timestamp']
    if thing == "nt":
        allied_nt1_respawn, allied_nt2_respawn = inter_minute['nexus_turrets_respawn']
        enemy_nt1_respawn, enemy_nt2_respawn = inter_minute['enemy_nexus_turrets_respawn']

        till_allied_nt1 = seconds_till(allied_nt1_respawn, now)
        till_allied_nt2 = seconds_till(allied_nt2_respawn, now)
        till_enemy_nt1 = seconds_till(enemy_nt1_respawn, now)
        till_enemy_nt2 = seconds_till(enemy_nt2_respawn, now)

        return (till_allied_nt1, till_allied_nt2, till_enemy_nt1, till_enemy_nt2)
    
    if thing == "avg_allied_respawn":
        avg = sum(inter_minute["allied_respawns"]) / 5
        return seconds_till(avg, now)
    
    elif thing == "avg_enemy_respawn":
        avg = sum(inter_minute['enemy_respawns']) / 5
        return seconds_till(avg, now)
    
    else:
        timestamp = inter_minute[f'{thing}']
        enemy_has = True if timestamp < 0 else False
        
        timestamp = abs(timestamp)
        if enemy_has:
            return -seconds_till(timestamp, now)
        else:
            return seconds_till(timestamp,now)
        

###################
## MISCELLANEOUS ##
###################

def grab_static_features(match, team):
    enemy_team = 100 if team==200 else 100
    vector = (
        match['metadata']['matchId'],                               #matchId #
        team,                                                       #team    #
        get_aggregate_cc_rating(match, team),                       #CCScore
        get_aggregate_cc_rating(match, enemy_team),                 #enemyCCScore
        team_is_squishy(match, team),                               #isSquishy
        team_is_squishy(match, enemy_team),                         #vsSquishy
    )
    return vector

def create_dynamic_features(team, snapshot, event, inter_minute, intra_minute):
    enemy_team = 100 if (team == 200) else 100
    till_allied_nt1, till_allied_nt2, till_enemy_nt1, till_enemy_nt2 = till_thing(inter_minute, event, 'nt')

    vector = (
        damage_type_ratio(snapshot, team),                          #damageTypeRatio
        get_gold_difference(snapshot, intra_minute, team),          #goldDifference
        get_avg_level(snapshot, intra_minute, team),                #averageAllyLvl
        get_avg_level(snapshot, intra_minute, enemy_team),          #averageEnemyLvl 
        np.mean(inter_minute["allied_distance_fountain"]),          #averageAllyToFountain
        np.mean(inter_minute['enemy_distance_fountain']),           #averageEnemytoFountain
        inter_minute['allied_dragons'],                             #alliedDragons
        inter_minute['enemy_dragons'],                              #enemyDragons
        inter_minute['allied_grubs'],                               #alliedGrubs
        inter_minute['enemy_grubs'],                                #enemyGrubs
        inter_minute['top_turrets_taken'],                          #topTurrets
        inter_minute["enemy_top_turrets_taken"],                    #enemytopTurrets
        inter_minute['mid_turrets_taken'],                          #midTurrets
        inter_minute['enemy_mid_turrets_taken'],                    #enemyMidTurrets
        inter_minute['bot_turrets_taken'],                          #botTurrets
        inter_minute['enemy_bot_turrets_taken'],                    #enemyBotTurrets
        inter_minute["inhibitors_taken"],                           #inhibsTaken
        inter_minute['enemy_inhibitors_taken'],                     #enemyInhibsTaken
        till_allied_nt1,                                            #tillAlliedNT1
        till_allied_nt2,                                            #tillAlliedNT2
        till_enemy_nt1,                                             #tillEnemyNT1
        till_enemy_nt2,                                             #tillEnemyNT2
        inter_minute['feats_of_strength'],                          #featsOfStrength
        inter_minute['atakhan'],                                    #atakhan
        inter_minute['has_soul'],                                   #hasSoul
        inter_minute['has_shelly'],                                 #hasShelly        
        till_thing(inter_minute, event, "baron_exp_at"),            #untilBaronExp
        till_thing(inter_minute, event, "elder_exp_at"),            #untilElderExp
        till_thing(inter_minute, event, "grubs_up_at"),             #untilGrubsSpawn
        till_thing(inter_minute, event, "herald_up_at"),            #untilHeraldSpawn
        till_thing(inter_minute, event, "baron_up_at"),             #untilBaronSpawn
        till_thing(inter_minute, event, "dragon_up_at"),            #untilDragonSpawn
        till_thing(inter_minute, event, "elder_up_at"),             #untilElderSpawn
        till_thing(inter_minute, event, "avg_allied_respawn"),      #avgAlliedRespawn
        till_thing(inter_minute, event, "avg_enemy_respawn"),       #avgEnemyRespawn
        event['timestamp'] / 60000,                                 #secondsElapsed
        event_objective_map[event['type']]                         #objective        
    )
    
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
    
    return ".".join(patch[0,2])

def seconds_till(timestamp, now):
    till = (timestamp - now)/1000
    return till if till>0 else 0

event_objective_map = {

}
   