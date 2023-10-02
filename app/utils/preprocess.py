"""
This script is used the perform preprocessing steps on the data. This includes:
    - Normalizing shot coordinates
    - Computing expected goals (xG)
    - Creating comparison plots

All of the plots are saved to a table in the database called "plots" with the following columns:
    - player_id (INTEGER)
    - xg_strength_state_code (VARCHAR)
    - comparison_type (VARCHAR)
    - plot (BLOB)
"""
import ast
import duckdb
import numpy as np
import pandas as pd
import json
import plotly.express as px
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import storage
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from PIL import Image
from io import BytesIO

load_dotenv()

"""
DuckDB related functions
"""
def seed_normalized_shots(conn):
    shots_filepath = 'assets/csv/bigquery/202202_player_shots.csv'

    # read the shots data to a dataframe
    shots_df = pd.read_csv(shots_filepath)

    # normalize the shot coordinates
    normalized_shots_df = normalize_shot_coordinates(shots_df)

    # create table in duckdb called "normalized_shots" as select * from normalized_shots_df
    query = f"""
        CREATE OR REPLACE TABLE normalized_shots AS SELECT * FROM normalized_shots_df
    """
    conn.execute(query)

def drop_all_tables_from_database(conn):
    # query all of the tables
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchdf()

    # if no tables found, return
    if len(tables) == 0:
        print("No tables found")
        return

    # for each table, drop it
    for table in tables['name']:
        if table == 'plots':
            continue
        print(f"Dropping table {table}")
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    print("All tables dropped")
    return

"""
Expected Goals (xG) related functions
"""
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

def plot_comparisons(player_dataframe, league_dataframe, comparison_type):

    # Always fetch the player XG
    player_xg = create_xg_array(player_dataframe)

    # If comparison type is against league, fetch the league XG
    if comparison_type == 'against_league':
        all_xg = create_xg_array(league_dataframe)
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
        'against_league': 'Difference vs. League xG',
        'individual': 'Individual xG'
    }

    # Create the rink
    # rink = create_rink_figure()
    # rink.savefig('dashapp/images/rink_img.png', format='png', dpi=300, transparent=True)

    # Load the images
    rink_img = Image.open('assets/images/rink.png')

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
                    labels={'z': 'xG Difference'},
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
            title_font=dict(color="white", size=18),  # Set the title font color to white and size to 20
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
        height=550,
        width=550,
        plot_bgcolor='white',  # Set plot background color to white
        paper_bgcolor='rgba(0, 0, 0, 0)',
    )

    if comparison_type == 'individual':
        fig.update_layout(coloraxis_showscale=False)


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

def preprocess_gcs():

    conn = duckdb.connect('assets/duckdb/app.db')
    seed_normalized_shots(conn)
    secret = ast.literal_eval(os.getenv('GOOGLE_STORAGE_CREDENTIALS'))
    credentials = service_account.Credentials.from_service_account_info(secret)
    client = storage.Client(project='data-arena', credentials=credentials)
    bucket = client.get_bucket('heroku-nhl-app')

    # initialize variables
    strength_state_codes = ['ev']
    comparison_types = ['against_league', 'individual']
    player_ids = conn.execute("SELECT DISTINCT player_id, player_name FROM normalized_shots").fetchdf()
    progress_counter = 0

    # for each strength state code
    for xg_strength_state_code in strength_state_codes:

        # compute the league xG (expected goals)
        league_df = conn.execute(f"SELECT * FROM normalized_shots WHERE xg_strength_state_code = '{xg_strength_state_code}'").fetchdf()

        # for each player
        for player_id in player_ids['player_id']:

            # for each comparison type
            for comparison_type in comparison_types:

                # print the player id
                print(f"Processing player {player_id} - current iteration:: {progress_counter}")

                # fetch the player dataframe
                player_query = f"""
                    SELECT *
                        FROM normalized_shots
                        WHERE player_id = {player_id}
                        AND xg_strength_state_code = '{xg_strength_state_code}'"""
                conn.execute(player_query)

                player_df = conn.fetchdf()

                # remove players with fewer than 4 rows
                if len(player_df) < 4:
                    progress_counter += 1
                    continue

                # for testing
                if player_id != 8478402:
                    progress_counter += 1
                    continue

                # create the comparison plot
                fig = plot_comparisons(player_df, league_df, comparison_type)

                # write the figure to a file on GCS
                image_bytes = fig.to_image(format='png', scale=1)
                bytestring = BytesIO(image_bytes).read()


                blob = bucket.blob(f"player_shot_plots/{player_id}_{xg_strength_state_code}_{comparison_type}.png")
                blob.upload_from_string(bytestring, content_type='image/png')

                progress_counter += 1
    conn.close()

def get_player_mapping():
    conn = duckdb.connect('assets/duckdb/app.db')

    # initialize variables
    player_ids_1 = conn.execute("SELECT DISTINCT player_id, player_name FROM normalized_shots").fetchdf()
    player_ids_2 = conn.execute("SELECT DISTINCT player_id, player_name FROM read_csv_auto('assets/csv/bigquery/202202_player_ranks.csv')").fetchdf()

    player_map = {}
    counter_1 = 0
    for player_id, player_name in zip(player_ids_1['player_id'], player_ids_1['player_name']):
        player_map[player_id] = player_name
        counter_1 += 1

    print(f"Processed {counter_1} players")

    counter_2 = 0
    for player_id, player_name in zip(player_ids_2['player_id'], player_ids_2['player_name']):
        # if the player_id is not a key in player_map, add it
        if player_id not in player_map.keys():
            player_map[player_id] = player_name
            counter_2 += 1

    print(f"Processed additional {counter_2} players")

    with open('assets/player_map.json', 'w') as f:
        json.dump(player_map, f)

if __name__ == '__main__':
    preprocess_gcs()

    # write json credentials to .env
    # with open('assets/secrets/google_storage_credentials.json', 'r') as f:
    #     credentials = json.load(f)

    # with open('.env', 'a') as f:
    #     f.write(f"\nGOOGLE_STORAGE_CREDENTIALS={credentials}")
