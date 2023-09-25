import datetime
import json
import os
import requests
# from google.oauth2 import service_account
# from google.cloud import storage
from io import BytesIO
from PIL import Image
import pandas as pd

# service_account_credentials = service_account.Credentials.from_service_account_file('secrets/google_credentials/google_storage_reader_credentials.json')
# client = storage.Client(credentials=service_account_credentials)
# bucket = client.get_bucket('nhl-stats-raw')

# def get_play_by_play(year=None, game_type=None):
#     prefix = 'games/year={}/game_type={}/'.format(year, game_type)
#     blobs = bucket.list_blobs(prefix=prefix)

#     with open('data/play_by_play.json', 'w') as outfile:
#         for blob in blobs:
#             # read each blob into memory as a string
#             blob_string = blob.download_as_string()
#             # parse the string into a python dictionary
#             blob_dict = json.loads(blob_string)
#             # write the dictionary to a file
#             json.dump(blob_dict, outfile)
#             # write a new line
#             outfile.write('\n')

# def get_players(year=None):
#     prefix = 'players/year={}/'.format(year)
#     blobs = bucket.list_blobs(prefix=prefix)

#     with open('data/players.json', 'w') as outfile:
#         for blob in blobs:
#             # read each blob into memory as a string
#             blob_string = blob.download_as_string()
#             # parse the string into a python dictionary
#             blob_dict = json.loads(blob_string)
#             # write the dictionary to a file
#             json.dump(blob_dict, outfile)
#             # write a new line
#             outfile.write('\n')

def get_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for HTTP errors
        return response
    except requests.exceptions.RequestException as e:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error calling {url}: {e}")
    except Exception as e:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - An unexpected error occurred: {e}")

def get_player_headshot(player_id, file_path = 'data/bq_results/2022_player_current_team.csv'):
    """Summary: Get player headshots from the NHL API and parse them into a DataFrame."""

    # Logic to get the current player's team code
    df1 = pd.read_csv(f'{file_path}')
    df2 = df1[df1['player_id'] == player_id]

    # Check if any rows match the filter
    if not df2.empty:
        # Get the value from the "team_code" column (assuming there's only one matching row)
        team_code = df2.iloc[0]['team_code']
        print(f"The team code for player ID {player_id} is {team_code}")
    else:
        team_code = 'NA'
        print(f"No matching rows found for player ID {player_id}")    # Set the base URL for the player headshots

    # Now, make the url
    url = F'https://assets.nhle.com/mugs/nhl/20222023/{team_code}/{player_id}.png'.format(player_id)

    # Send an HTTP GET request to fetch the image data
    response = get_api(url.format(player_id=player_id))

    # Convert the response content to bytes
    image_data = BytesIO(response.content)

    # Open the image using PIL
    img = Image.open(image_data)

    return img

if __name__ == '__main__':
    get_players(year=2022)
