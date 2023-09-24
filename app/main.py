# Library imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

# Module imports
from app.utils.extract import get_season_data, get_player_headshot
from app.utils.transform import get_shot_goal_data
from app.utils.visualize import create_rink

def normalize_xg_dataframe():
    xg_df = pd.read_csv('bq_results/202202_player_shots.csv', delimiter= ',')

    # Subset
    normalized_df = xg_df[[
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

    # Normalize x & y coordinates such that when x is negative, flip x and y to force to be shooting "right"
    normalized_df['adj_x_coord'] = normalized_df.apply(lambda row: -row['x_coord'] if row['x_coord'] < 0 else row['x_coord'], axis=1)
    normalized_df['adj_y_coord'] = normalized_df.apply(lambda row: -row['y_coord'] if row['x_coord'] < 0 else row['y_coord'], axis=1)

    # Print summary stats
    print("Normalized Dataframe Summary Stats")
    print(f"Rows: {len(normalized_df)}")
    print("xGoals Max {:.2f}".format(normalized_df['xg_proba'].max()))
    print("xGoals Mean {:.2f}".format(normalized_df['xg_proba'].mean()))
    print("X Cords: {}, {}".format(normalized_df['x_coord'].min(),normalized_df['adj_x_coord'].max()))
    print("Y Cords: {}, {}".format(normalized_df['y_coord'].min(),normalized_df['adj_y_coord'].max()))

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

def plot_comparisons(normalized_df, player_name):
    ev_data = normalized_df[normalized_df['xg_strength_state_code'] == 'ev']

    # Create data
    all_xg = create_xg_array(ev_data, is_smooth = True)
    player_xg = create_xg_array(ev_data[ev_data['player_name'] == player_name], is_smooth = True)
    new_diff = player_xg - all_xg

    # Get the player's headshot
    filter = ev_data[ev_data['player_name'] == player_name]
    player_id = np.unique(filter[['player_id']])
    rows = [get_player_headshot(player_id) for player_id in player_id]
    headshots_df = pd.DataFrame(rows)
    headshots_df['img'].iloc[0].save('player_img.png', format = 'PNG')
    print("Saved image to player_img.png")

    # Create the rink
    rink = create_rink()
    rink.savefig('rink_img.png', format='png', dpi=300, transparent=True)

    # Load the images
    player_img = Image.open('player_img.png')
    rink_img = Image.open('rink_img.png')

    # Calculate the position for the image (adjust as needed)
    image_x = 0.1  # Adjust the x-coordinate
    image_y = 1.15   # Adjust the y-coordinate

    data_min = new_diff.min()
    data_max = new_diff.max()
    mid_val = new_diff.mean()

    if abs(data_min) > data_max:
        data_max = data_min * -1
    elif data_max > abs(data_min):
        data_min = data_max * -1

    x, y = np.meshgrid(np.linspace(0, 89, 100), np.linspace(-42.5, 42.5, 85))
    # fig, ax = plt.subplots(1, 1, figsize=(10, 12), facecolor='w', edgecolor='k')

    meshgrid_df = pd.DataFrame({'x': x.flatten(), 'y': y.flatten(), 'z': new_diff.flatten()})

    # Create a scatter plot using plotly
    fig = px.scatter(meshgrid_df, x='x', y='y', color='z',
                    color_continuous_scale='RdBu_r',
                    title=f'{player_name} vs League xGoal',
                    labels={'z': 'Difference'},
                    range_color=[data_min, data_max])

    # Add the player's image
    fig.add_layout_image(
        source=player_img,
        x=image_x,
        y=image_y,
        xanchor="center",
        yanchor="top",
        xref="paper",
        yref="paper",
        sizex=0.2,
        sizey=0.2,
    )

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
        coloraxis_colorbar=dict(title="Difference"),
        coloraxis_cmin=data_min,
        coloraxis_cmax=data_max,
        height=600,
        width=600,
    )

    # Center the title
    fig.update_layout(title_x=0.5)

    # Remove gridlines and background from scatterplot
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)

    # Remove the background color
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')

    # Remove x and y axis labels
    fig.update_xaxes(title_text='')
    fig.update_yaxes(title_text='')

    # Show the interactive plot
    fig.show()

def main(
    player_name = 'Connor McDavid'
    download_season = False
    ):

    if download_season:
        # Download data for the 2022 season
        get_season_data(season = 2022)

    # League data, pass player_names as an empty list
    league_coordinates, league_coordinates_df = get_shot_goal_data(player_names=[], season = 2022)

    # Play data, specify player_names
    player_coordinates, player_coordinates_df = get_shot_goal_data(player_names=['Connor McDavid', 'Auston Matthews', 'Alex Ovechkin', 'Sidney Crosby', 'Jack Eichel'], season = 2022)

    # Normalize xg dataframe
    normalized_df = normalize_xg_dataframe()

    # Plot comparisons
    plot_comparisons(normalized_df, player_name)

if __name__ == '__main__':
    main()
