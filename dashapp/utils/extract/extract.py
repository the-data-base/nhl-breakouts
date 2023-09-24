import datetime
import json
import os
import requests
# from google.oauth2 import service_account
# from google.cloud import storage
from io import BytesIO
from PIL import Image

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

def get_player_headshot(player_id):
    """Summary: Get player headshots from the NHL API and parse them into a DataFrame."""

    # Set the base URL for the player headshots
    # url = "https://cms.nhl.bamgrid.com/images/headshots/current/60x60/{}@2x.jpg".format(player_id)
    url = 'https://assets.nhle.com/mugs/nhl/20222023/EDM/{}.png'.format(player_id)

    # Send an HTTP GET request to fetch the image data
    response = get_api(url.format(player_id=player_id))

    # Convert the response content to bytes
    image_data = BytesIO(response.content)

    # Open the image using PIL
    img = Image.open(image_data)

    return img

if __name__ == '__main__':
    get_players(year=2022)
