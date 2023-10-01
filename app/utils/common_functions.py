import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO
from matplotlib import pyplot
from PIL import Image
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

"""
Initialization
"""
pyplot.ioff()
pyplot.switch_backend('Agg')

"""
Hockey rink related functions
- create_rink_figure: Create a hockey rink figure
- normalize_shot_coordinates: Normalize shot coordinates so that all shots are shooting "right"
- normalize_xg_dataframe_by_chunk: Normalize the xG dataframe by chunk
- get_player_xg: Get the xG for a specific player
- get_league_xg: Get the xG for the entire league
- plot_comparisons: Plot the xG comparisons
"""
def create_rink_figure(
    plot_half = True,
    board_radius = 25,
    alpha = 1,
):

    # Create a new figure
    fig, ax = plt.subplots(1, 1, figsize=(10, 12), facecolor='none', edgecolor='none')

    #Cornor Boards
    ax.add_artist(mpl.patches.Arc((100-board_radius , (85/2)-board_radius), board_radius * 2, board_radius * 2 , theta1=0, theta2=89, edgecolor='Black', lw=4.5,zorder=0, alpha = alpha)) #Top Right
    ax.add_artist(mpl.patches.Arc((-100+board_radius+.1 , (85/2)-board_radius), board_radius * 2, board_radius * 2 ,theta1=90, theta2=180, edgecolor='Black', lw=4.5,zorder=0, alpha = alpha)) #Top Left
    ax.add_artist(mpl.patches.Arc((-100+board_radius+.1 , -(85/2)+board_radius-.1), board_radius * 2, board_radius * 2 ,theta1=180, theta2=270, edgecolor='Black', lw=4.5,zorder=0, alpha = alpha)) #Bottom Left
    ax.add_artist(mpl.patches.Arc((100-board_radius , -(85/2)+board_radius-.1), board_radius * 2, board_radius * 2 ,theta1=270, theta2=360, edgecolor='Black', lw=4.5,zorder=0, alpha = alpha)) #Bottom Right

    #[x1,x2],[y1,y2]
    #Plot Boards
    ax.plot([-100+board_radius,100-board_radius], [-42.5, -42.5], linewidth=4.5, color="Black",zorder=0, alpha = alpha) #Bottom
    ax.plot([-100+board_radius-1,100-board_radius+1], [42.5, 42.5], linewidth=4.5, color="Black",zorder=0, alpha = alpha) #Top
    ax.plot([-100,-100], [-42.5+board_radius, 42.5-board_radius], linewidth=4.5, color="Black",zorder=0, alpha = alpha) #Left
    ax.plot([100,100], [-42.5+board_radius, 42.5-board_radius], linewidth=4.5, color="Black",zorder=0, alpha = alpha) #Right

    #Goal Lines
    adj_top = 4.6
    adj_bottom = 4.5
    ax.plot([89,89], [-42.5+adj_bottom, 42.5 - adj_top], linewidth=3, color="Red",zorder=0, alpha = alpha)
    ax.plot([-89,-89], [-42.5+adj_bottom, 42.5 - adj_top], linewidth=3, color="Red",zorder=0, alpha = alpha)

    #Plot Center Line
    ax.plot([0,0], [-42.5, 42.5], linewidth=3, color="Red",zorder=0, alpha = alpha)
    ax.plot(0,0, markersize = 6, color="Blue", marker = "o",zorder=0, alpha = alpha) #Center FaceOff Dots
    ax.add_artist(mpl.patches.Circle((0, 0), radius = 33/2, facecolor='none', edgecolor="Blue", linewidth=3,zorder=0, alpha = alpha)) #Center Circle

    #Zone Faceoff Dots
    ax.plot(69,22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(69,-22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(-69,22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(-69,-22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)

    #Zone Faceoff Circles
    ax.add_artist(mpl.patches.Circle((69, 22), radius = 15, facecolor='none', edgecolor="Red", linewidth=3,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Circle((69,-22), radius = 15, facecolor='none', edgecolor="Red", linewidth=3,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Circle((-69,22), radius = 15, facecolor='none', edgecolor="Red", linewidth=3,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Circle((-69,-22), radius = 15, facecolor='none', edgecolor="Red", linewidth=3,zorder=0, alpha = alpha))

    #Neutral Zone Faceoff Dots
    ax.plot(22,22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(22,-22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(-22,22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)
    ax.plot(-22,-22, markersize = 6, color="Red", marker = "o",zorder=0, alpha = alpha)

    #Plot Blue Lines
    ax.plot([25,25], [-42.5, 42.5], linewidth=2, color="Blue",zorder=0, alpha = alpha)
    ax.plot([-25,-25], [-42.5, 42.5], linewidth=2, color="Blue",zorder=0, alpha = alpha)

    #Goalie Crease
    ax.add_artist(mpl.patches.Arc((89, 0), 6,6,theta1=90, theta2=270,  facecolor="Blue", edgecolor='Red', lw=2,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Arc((-89, 0), 6,6, theta1=270, theta2=90, facecolor="Blue", edgecolor='Red', lw=2,zorder=0, alpha = alpha))

    #Goal
    ax.add_artist(mpl.patches.Rectangle((89, 0 - (4/2)), 2, 4, lw=2, color='Red',fill=False,zorder=0, alpha = alpha))
    ax.add_artist(mpl.patches.Rectangle((-89 - 2, 0 - (4/2)), 2, 4, lw=2, color='Red',fill=False,zorder=0, alpha = alpha))

    if plot_half == False:
        # Set axis limits
        ax.set_xlim(-101, 101)
        ax.set_ylim(-43, 43)

    elif plot_half == True:
        # Set axis limits
        ax.set_xlim(-0.5, 100.5)
        ax.set_ylim(-43, 43)

    # Remove axis labels
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Remove axis ticks
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')

    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['top'].set_visible(False)

    return fig

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
    raw_filename = 'app/assets/csv/bigquery/202202_player_shots.csv'
    normalized_filename = 'app/assets/csv/bigquery/202202_player_shots_normalized.csv'
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
    normalized_filename = 'app/assets/csv/bigquery/202202_player_shots_normalized.csv'

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
    # rink = create_rink_figure()
    # rink.savefig('dashapp/images/rink_img.png', format='png', dpi=300, transparent=True)

    # Load the images
    rink_img = Image.open('app/assets/images/rink.png')

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
        height=650,
        width=650,
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

"""
API related functions
- get_api: Generic function to call an API and return the response
- get_player_headshot: Get a player's headshot from the NHL API
"""
def get_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for HTTP errors
        return response
    except requests.exceptions.RequestException as e:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error calling {url}: {e}")
    except Exception as e:
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - An unexpected error occurred: {e}")

def get_player_headshot(player_id, file_path = 'app/assets/csv/bigquery/2022_player_current_team.csv'):
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
