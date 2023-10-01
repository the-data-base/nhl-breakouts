import numpy as np
import os
import pandas as pd
import plotly.express as px
from PIL import Image
from matplotlib import pyplot
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter


# Modules
from dashapp.utils.visualize.create_rink import create_rink

pyplot.ioff()
pyplot.switch_backend('Agg')

def normalize_shot_coordinates(input_df):
    # Normalize x & y coordinates such that when x is negative, flip x and y to force to be shooting "right"
    normalized_df = input_df.copy()
    normalized_df['adj_x_coord'] = normalized_df.apply(lambda row: -row['x_coord'] if row['x_coord'] < 0 else row['x_coord'], axis=1)
    normalized_df['adj_y_coord'] = normalized_df.apply(lambda row: -row['y_coord'] if row['x_coord'] < 0 else row['y_coord'], axis=1)

    # print("Normalized Dataframe Summary Stats")
    # print(f"Rows: {len(normalized_df)}")
    # print("xGoals Max {:.2f}".format(normalized_df['xg_proba'].max()))
    # print("xGoals Mean {:.2f}".format(normalized_df['xg_proba'].mean()))
    # print("X Cords: {}, {}".format(normalized_df['x_coord'].min(),normalized_df['adj_x_coord'].max()))
    # print("Y Cords: {}, {}".format(normalized_df['y_coord'].min(),normalized_df['adj_y_coord'].max()))

    return normalized_df

def create_xg_array(data, is_smooth = True):
    [x,y] = np.round(np.meshgrid(np.linspace(0,100,100), np.linspace(-42.5, 42.5, 85)))
    xgoals = griddata(
                (data['adj_x_coord'], data['adj_y_coord']),
                data['xg_proba'],
                (x, y),
                method = 'cubic',
                fill_value = 0)
    xgoals = np.where(xgoals < 0, 0, xgoals)

    if is_smooth:
        xgoals = gaussian_filter(xgoals, sigma = 3)

    return xgoals

def normalize_xg_dataframe_by_chunk(chunksize=100000):
    raw_filename = 'data/bq_results/202202_player_shots.csv'
    normalized_filename = 'data/shots_xg/202202_player_shots_normalized.csv'
    if os.path.exists(normalized_filename):
        os.remove(normalized_filename)
    # Read the data in chunks
    raw_df = pd.read_csv(raw_filename, delimiter= ',', chunksize=chunksize)

    # Normalize each chunk, writing it back to a single csv in append mode
    for i, chunk in enumerate(raw_df):
        print(f"Normalizing chunk {i}")
        subset_df = chunk[[
            'player_name',
            'player_id',
            'event_type',
            'play_period',
            'zone_type',
            'zone',
            'xg_strength_state_code',
            'x_goal',
            'xg_proba',
            'play_distance',
            'play_angle',
            'x_coord',
            'y_coord']].copy()
        normalized_df = normalize_shot_coordinates(subset_df)
        normalized_df.to_csv(normalized_filename, mode='a', header=True, index=False)
    return True

def get_player_xg(filename, xg_strength_state_code, player_name, chunksize=100000):
    df = pd.read_csv(filename, delimiter= ',', chunksize=chunksize)
    player_df = pd.DataFrame()
    for i, chunk in enumerate(df):
        print('Processing player chunk: {}'.format(i))
        # concat chunks vertically if chunk player_name matches player_name and xg_strength_state_code matches xg_strength_state_code (both conditions on the same line)
        subset_chunk = chunk.loc[(chunk['player_name'] == player_name) & (chunk['xg_strength_state_code'] == xg_strength_state_code)]
        player_df = pd.concat([player_df, subset_chunk])

    player_xgoals = create_xg_array(player_df, is_smooth = True)

    return player_xgoals

def get_league_xg(filename, xg_strength_state_code, chunksize=100000):
    df = pd.read_csv(filename, delimiter= ',', chunksize=chunksize)
    league_df = pd.DataFrame()
    for i, chunk in enumerate(df):
        print('Processing league chunk: {}'.format(i))
        subset_chunk = chunk.loc[chunk['xg_strength_state_code'] == xg_strength_state_code]
        league_df = pd.concat([league_df, subset_chunk])
        league_xgoals = create_xg_array(league_df, is_smooth = True)

    # save league xgoals to csv file
    league_xgoals = create_xg_array(league_df, is_smooth = True)

    return league_xgoals

def plot_comparisons(player_name, comparison_type):
    xg_strength_state_code = 'ev'
    normalized_filename = 'data/shots_xg/202202_player_shots_normalized.csv'

    # Always fetch the player XG
    player_xg = get_player_xg(normalized_filename, xg_strength_state_code, player_name)

    # If comparison type is against league, fetch the league XG
    if comparison_type == 'against_league':
        all_xg = get_league_xg(normalized_filename, xg_strength_state_code)
        new_diff = player_xg - all_xg
        data_min = new_diff.min()
        data_max = new_diff.max()

    # If comparison type is against individual, use the player XG
    elif comparison_type == 'individual':
        data_min = player_xg.min()
        data_max = player_xg.max()
        new_diff = player_xg

    # Legend header map
    legend_header_map = {
        'against_league': 'Difference vs. League XG',
        'individual': 'Individual XG'
    }

    # Create the rink
    rink = create_rink()
    rink.savefig('dashapp/images/rink_img.png', format='png', dpi=300, transparent=True)

    # Load the images
    rink_img = Image.open('dashapp/images/rink_img.png')

    # Set the min and max values for the color scale
    if abs(data_min) > data_max:
        data_max = data_min * -1
    elif data_max > abs(data_min):
        data_min = data_max * -1

    # Create a meshgrid
    x, y = np.meshgrid(np.linspace(0, 89, 100), np.linspace(-42.5, 42.5, 85))

    meshgrid_df = pd.DataFrame({'x': x.flatten(), 'y': y.flatten(), 'z': new_diff.flatten()})
    meshgrid_df['x'] = meshgrid_df['x'].round(0)
    meshgrid_df['y'] = meshgrid_df['y'].round(0)
    meshgrid_df['z'] = meshgrid_df['z'].round(4)

    # Create a scatter plot using plotly
    fig = px.scatter(meshgrid_df, x='x', y='y', color='z',
                    color_continuous_scale='RdBu_r',
                    labels={'z': 'Difference'},
                    template='plotly',
                    range_color=[data_min, data_max])

    # Add the background rink image
    fig.add_layout_image(
        source=rink_img,
        x=-17, # Bunch of trial and error to figure out
        y=56, # Bunch of trial and error to figure out
        xref="x",
        yref="y",
        sizex=131, # Bunch of trial and error to figure out
        sizey=111, # Bunch of trial and error to figure out
        opacity=1,
        sizing="stretch",
        layer="above"
    )

    # Customize the layout
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=legend_header_map[comparison_type],
            title_side='top',
            title_font=dict(color="white", size=20),  # Set the title font color to white and size to 20
            x=0.5,  # Adjust the horizontal position of the color legend
            y=-0.025,  # Adjust the vertical position of the color legend
            xanchor='center',  # Center the color legend horizontally
            yanchor='top',  # Place the color legend below the plot
            orientation='h',  # Display the color legend horizontally
            tickfont=dict(color="white"),  # Set the tick font color to white
            nticks=10  # Set the number of tick marks on the color legend
            ),
        coloraxis_cmin=data_min,
        coloraxis_cmax=data_max,
        height=650,
        width=650,
        plot_bgcolor='white',  # Set plot background color to white
        paper_bgcolor='rgba(0, 0, 0, 0)',
    )

    # Set x and y axis ranges to match data
    fig.update_xaxes(range=[-0.1, 100], tickfont=dict(color="white"))
    fig.update_yaxes(range=[-42.6, 42.6], tickfont=dict(color="white"), showticklabels=False)

    # Remove gridlines and background from scatterplot
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)

    # Remove x and y axis labels
    fig.update_xaxes(title_text='')
    fig.update_yaxes(title_text='')

    # Set margins to 20 pixels
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))

    # Show the interactive plot
    return fig

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
