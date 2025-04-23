import requests
import json
import os
from dotenv import load_dotenv
from pulsefire.clients import RiotAPIClient
import time
import asyncio
load_dotenv()

API_KEY = os.getenv('RIOTAPI')
script_dir = os.path.dirname(os.path.abspath(__file__))

async def fetch_players(client, elo):
    all_players = []
    requests_made = 0
    for region in ['na1', 'euw1', 'kr']:

        for division in ["IV", "III", "II", "I"]:
            page = 1        
            
            while page<42:
                # Fetch players on the current page
                players = await client.get_lol_league_v4_entries_by_division(
                    region=region,
                    queue="RANKED_SOLO_5x5",
                    tier=elo,
                    division=division,
                    queries={'page': page}
                )
                
                if not players:
                    break  # Exit loop if no players are returned
                
                for player in players:
                    player["Region"] = region

                all_players.extend(players)
                page += 1
                requests_made += 1
                
                # Check if rate limits are close to being hit
                if requests_made % 50 == 0:
                    time.sleep(10)

    return all_players   


async def main():
    start_time = time.time()


    async with RiotAPIClient(default_headers={"X-Riot-Token": API_KEY}) as client:
        players = await fetch_players(client, "PLATINUM")
        print(f"Total platinum players retrieved: {len(players)}")

    json_path = os.path.join(script_dir, "platinum.json")
    with open(json_path, 'w') as file:
        json.dump(players, file, indent=4)



    async with RiotAPIClient(default_headers={"X-Riot-Token": API_KEY}) as client:
        players = await fetch_players(client, "EMERALD")
        print(f"Total emerald players retrieved: {len(players)}")

    json_path = os.path.join(script_dir, "emerald.json")
    with open(json_path, 'w') as file:
        json.dump(players, file, indent=4)


    
    async with RiotAPIClient(default_headers={"X-Riot-Token": API_KEY}) as client:
        players = await fetch_players(client, "DIAMOND")
        print(f"Total diamond players retrieved: {len(players)}")

    json_path = os.path.join(script_dir, "diamond.json")
    with open(json_path, 'w') as file:
        json.dump(players, file, indent=4)


    
    async with RiotAPIClient(default_headers={"X-Riot-Token": API_KEY}) as client:
        all_players = []
        for region in ['na1', 'euw1', 'kr']:
            response = await client.get_lol_league_v4_master_league_by_queue(region=region, queue="RANKED_SOLO_5x5")
            for player in response['entries']:
                player["Region"] = region
            all_players.extend(response['entries'])
        print(f"Total master players retrieved: {len(all_players)}")

    json_path = os.path.join(script_dir, "master.json")
    with open(json_path, 'w') as file:
        json.dump(all_players, file, indent=4)


    
    async with RiotAPIClient(default_headers={"X-Riot-Token": API_KEY}) as client:
        all_players = []
        for region in ['na1', 'euw1', 'kr']:
            response = await client.get_lol_league_v4_grandmaster_league_by_queue(region=region, queue="RANKED_SOLO_5x5")
            for player in response['entries']:
                player["Region"] = region
            all_players.extend(response['entries'])
        print(f"Total grandmaster players retrieved: {len(all_players)}")

    json_path = os.path.join(script_dir, "grandmaster.json")
    with open(json_path, 'w') as file:
        json.dump(all_players, file, indent=4)



    async with RiotAPIClient(default_headers={"X-Riot-Token": API_KEY}) as client:
        all_players = []
        for region in ['na1', 'euw1', 'kr']:
            response = await client.get_lol_league_v4_challenger_league_by_queue(region=region, queue="RANKED_SOLO_5x5")
            for player in response['entries']:
                player["Region"] = region
            all_players.extend(response['entries'])
        print(f"Total challenger players retrieved: {len(all_players)}")

    json_path = os.path.join(script_dir, "challenger.json")
    with open(json_path, 'w') as file:
        json.dump(all_players, file, indent=4)
    

    end_time = time.time()
    print(f"Execution_time: {end_time-start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())