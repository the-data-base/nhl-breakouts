# Library imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

# Module imports
from app.utils.extract import get_season_data
from app.utils.transform import get_shot_goal_data
from app.utils.extract import get_player_headshot
from app.utils.visualize import create_rink

def normalize_xg_dataframe():
    xg_df = pd.read_csv('.bq_xg/202202_test.csv', delimiter= ',')

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

    # Set vars
    image_path = '.output/img.png'

    # Create data
    all_xg = create_xg_array(ev_data, is_smooth = True)
    player_xg = create_xg_array(ev_data[ev_data['player_name'] == player_name], is_smooth = True)
    new_diff = player_xg - all_xg

    # Assuming you have an image file at '.output/mcd.png'
    filter = ev_data[ev_data['player_name'] == player_name]
    player_id = np.unique(filter[['player_id']])
    rows = [get_player_headshot(player_id) for player_id in player_id]
    headshots_df = pd.DataFrame(rows)
    headshots_df['img'].iloc[0].save(image_path, format = 'PNG')
    print("Saved image to {}".format(image_path))

    # Load the image
    mcd_image = Image.open(image_path)

    # Create the OffsetImage object
    mcd_imagebox = OffsetImage(mcd_image, zoom=0.9)

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

    fig, ax = plt.subplots(1, 1, figsize=(10, 12), facecolor='w', edgecolor='k')

    # Add the image to the plot
    ab = AnnotationBbox(mcd_imagebox, (image_x, image_y), frameon=False, xycoords='axes fraction')
    ax.add_artist(ab)

    create_rink(ax, plot_half=True, board_radius=25, alpha=1.0)

    ax = ax.contourf(
        new_diff, alpha=0.8, cmap='bwr',
        extent=(0, 89, -42.5, 42.5),
        levels=np.linspace(data_min, data_max, 12),
        vmin=data_min,
        vmax=data_max,
        # norm = mpl.colors.Normalize(vmin = -0.05, vmax = 0.05),
    )

    # Set the title and subtitle with manual padding
    title_text = f'{player_name} vs League xGoal'
    subtitle_text = 'Is that gud???'

    plt.title(title_text, fontsize=22, pad=75)  # Adjust the pad value for title padding
    plt.suptitle(subtitle_text, y=.95, fontsize=16)

    fig.colorbar(ax, orientation="horizontal", pad=0.05)
    plt.axis('off')
    plt.show()

def main(
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
    player_name = 'Connor McDavid'
    plot_comparisons(normalized_df, player_name)

if __name__ == '__main__':
    main()
