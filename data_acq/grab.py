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


def team_is_heavy_ad(timeline, team, game_minute):
    return 



###################
## MISCELLANEOUS ##
###################

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