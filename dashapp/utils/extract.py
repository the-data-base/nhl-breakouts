import datetime
import json
import os
import requests
import shutil
from tqdm import tqdm
from enum import Enum
from io import BytesIO
from PIL import Image

class SeasonType(Enum):
    PRE_SEASON = "01"
    REGULAR_SEASON = "02"
    PLAYOFFS = "03"
    ALL_STAR = "04"

class FileHandler:
    """Class to handle writing JSON data to file(s) based on a maximum file size."""
    def __init__(self, output_folder):
        """Initialize the file handler."""
        # Specify the maximum file size (in bytes) before splitting
        self.max_file_size_bytes = 50 * 1024 * 1024  # 50MB
        self.output_folder = output_folder
        self.current_file_size = 0
        self.current_file_index = 1
        self.output_file = self._create_output_file()

    def _create_output_file(self):
        """Summary: Create a new output file.

        Returns:
            str: The full path to the output file.
        """
        output_file = os.path.join(self.output_folder, f'livefeed_{self.current_file_index}.jsonl')
        with open(output_file, 'w') as file:
            pass  # Create an empty file
        return output_file

    def write_to_file(self, json_data):
        """Write the JSON data to file.

        Args:
            json_data (dict): The JSON data to write to file.

        Returns:
            None
        """
        json_data_str = json.dumps(json_data)
        json_size = len(json_data_str.encode('utf-8'))

        # Check if writing the JSON data would exceed the max file size
        if self.current_file_size + json_size > self.max_file_size_bytes:
            self.current_file_index += 1
            self.current_file_size = 0
            self.output_file = self._create_output_file()
        with open(self.output_file, 'a') as file:
            file.write(json_data_str + '\n')

        self.current_file_size += json_size

def get_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for HTTP errors
        return response
    except requests.exceptions.RequestException as e:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error calling {url}: {e}")
    except Exception as e:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - An unexpected error occurred: {e}")

def get_season_data(season_year, season_types, season_game_ids, if_exists='skip'):
    assert if_exists in ['skip', 'replace'], "if_exists must be one of 'skip' or 'replace'"

    # Specify where output files are written to
    output_folder = f'.output/{season_year}'

    # Check if the folder already exists, and if so, remove it
    if os.path.exists(output_folder) and if_exists == 'replace':
        shutil.rmtree(output_folder)

    # Check if the folder already exists, and if so, skip
    if os.path.exists(output_folder) and if_exists == 'skip':
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Output folder already exists. Skipping...")
        return

    # Create the output folder
    os.makedirs(output_folder, exist_ok=True)

    # Initialize the file handler
    file_handler = FileHandler(output_folder)

    url = "http://statsapi.web.nhl.com/api/v1/game/{year}{season_type}{game_id}/feed/live"

    # Generate a list of URLs for the API
    urls = [url.format(year=season_year, season_type=season_type.value, game_id=game_id)
            for season_type in season_types
            for game_id in season_game_ids]

    # Call the API
    with tqdm(total=len(urls), unit="URL") as progress_bar:
        for url in urls:
            res = get_api(url)

            if not res:
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Reached the end of possible game data.")
                break

            if res:
                data = res.json()
                del data['gameData']
                del data['liveData']['linescore']
                del data['liveData']['boxscore']
                del data['liveData']['decisions']
                file_handler.write_to_file(data)

            progress_bar.update(1)

def get_player_headshot(player_id):
    """Summary: Get player headshots from the NHL API and parse them into a DataFrame."""

    # Set the base URL for the player headshots
    url = "https://cms.nhl.bamgrid.com/images/headshots/current/60x60/{player_id}@2x.jpg"

    # Send an HTTP GET request to fetch the image data
    response = get_api(url.format(player_id=player_id))

    # Convert the response content to bytes
    image_data = BytesIO(response.content)

    # Open the image using PIL
    img = Image.open(image_data)

    return {'player_id': player_id, 'img': img}

def main(player_id = '8478402', season_year = 2018):
    # Get headshot
    print(get_player_headshot(player_id='8478402'))

    # Get season data
    season_types = [SeasonType.REGULAR_SEASON]
    season_game_ids = [str(i).zfill(4) for i in range(1, 1314)]
    get_season_data(season_year, season_types, season_game_ids)

if __name__ == '__main__':
    main()
