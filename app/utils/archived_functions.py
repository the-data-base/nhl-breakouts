# def get_shot_goal_data(player_names=[], season = None):
#     """For each play resulting in a shot or goal, get the player name, event type, and the x y coordinates of the shot"""

#     # Match files with glob pattern
#     pattern = os.path.join(f'.output/api_results/{season}', 'livefeed_*.jsonl')
#     matching_files = glob.glob(pattern)

#     # Set the event types of interest
#     event_types = ['Shot','Goal']

#     # Coordinates D1
#     play_coordinates = {}
#     play_coordinates['Shot'] = {}
#     play_coordinates['Shot']['x'] = []
#     play_coordinates['Shot']['y'] = []
#     play_coordinates['Goal'] = {}
#     play_coordinates['Goal']['x'] = []
#     play_coordinates['Goal']['y'] = []

#     # Coordinates D2
#     play_coordinates_for_dataframe = {
#         "game_id": [],
#         "play_id": [],
#         "x_coord":[],
#         "y_coord":[],
#         "event":[],
#         "event_type":[],
#         "event_desc": [],
#         "period": [],
#         "period_time": [],
#         "player_name": [],
#         "player_id": [],
#         "player_type": []
#         }

#     # For each matching file
#     for file_path in matching_files:

#         # Open the file
#         with jsonlines.open(file_path, 'r') as file:

#             # Each line in the file represents a single game
#             for jsonline in file:

#                 # Skip if no live data for current game
#                 if 'liveData' not in jsonline.keys():
#                     continue

#                 # Get the plays from each game
#                 plays = jsonline['liveData']['plays']['allPlays']
#                 game_id = jsonline['gamePk']

#                 # Loop over each play in the current game
#                 for play in plays:

#                     # Look for players in the play
#                     if 'players' in play:

#                         for player in play['players']:

#                             if len(player_names) > 0:

#                                 # If player names are specified, skip any plays that don't involve those players
#                                 if not any(player_name in player['player']['fullName'] for player_name in player_names):
#                                     continue

#                             if player['playerType'] in ['Shooter', 'Scorer']:
#                                 player_type = player['playerType']
#                                 player_id = player['player']['id']
#                                 player_name = player['player']['fullName']

#                                 for event in event_types:
#                                     # Look for Shot and Goal events that have coordinates
#                                     if play['result']['event'] in event and play['coordinates']:
#                                         # Save the coordinates to d1
#                                         play_coordinates[event]['x'].append(play['coordinates']['x'])
#                                         play_coordinates[event]['y'].append(play['coordinates']['y'])
#                                         # Save the coordinates to d2
#                                         play_coordinates_for_dataframe["game_id"].append(game_id)
#                                         play_coordinates_for_dataframe["x_coord"].append(play['coordinates']['x'])
#                                         play_coordinates_for_dataframe["y_coord"].append(play['coordinates']['y'])
#                                         play_coordinates_for_dataframe["event"].append(play['result']['event'])
#                                         play_coordinates_for_dataframe["event_type"].append(play['result'].get('secondaryType', None))
#                                         play_coordinates_for_dataframe["event_desc"].append(play['result']['description'])
#                                         play_coordinates_for_dataframe["period"].append(play['about']['period'])
#                                         play_coordinates_for_dataframe["period_time"].append(play['about']['periodTime'])
#                                         play_coordinates_for_dataframe["play_id"].append(play['about']['eventIdx'])
#                                         play_coordinates_for_dataframe["player_name"].append(player_name)
#                                         play_coordinates_for_dataframe["player_id"].append(player_id)
#                                         play_coordinates_for_dataframe["player_type"].append(player_type)

#     # Convert to pandas dataframe
#     play_coordinates_df = pd.DataFrame.from_dict(play_coordinates_for_dataframe)

#     # Drop dups
#     play_coordinates_dedupe_df = play_coordinates_df.drop_duplicates()

#     # Add some features
#     play_coordinates_dedupe_df['goal'] = np.where(play_coordinates_dedupe_df['event']== 'Goal', 1, 0)
#     play_coordinates_dedupe_df['league'] = 'NHL'

#     # See data
#     return play_coordinates, play_coordinates_dedupe_df
