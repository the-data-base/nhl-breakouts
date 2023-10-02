import ast
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import os
import pandas as pd
import requests
from base64 import b64encode
from google.cloud import storage
from google.oauth2 import service_account
from dash import html
from io import BytesIO
from matplotlib import pyplot
from PIL import Image

"""
Initialization
"""
pyplot.ioff()
pyplot.switch_backend('Agg')

"""
Hockey rink related functions
- create_rink_figure: Create a hockey rink figure
"""
def create_rink_figure(plot_half = True, board_radius = 25, alpha = 1):
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

"""
Data retrieval related functions
- get_player_shot_plot: Get a player's shot plot from Google Cloud Storage
"""
def get_player_shot_plot(player_id, comparison_type, strength_state_code='ev'):
    try:
        # retrieve the plot from GCS
        secret = ast.literal_eval(os.getenv('GOOGLE_STORAGE_CREDENTIALS'))
        credentials = service_account.Credentials.from_service_account_info(secret)
        client = storage.Client(project='data-arena', credentials=credentials)
        bucket = client.get_bucket('heroku-nhl-app')
        blob = bucket.blob(f'player_shot_plots/{player_id}_{strength_state_code}_{comparison_type}.png')
        plot = blob.download_as_string()
    except Exception as e:
        return f"An error occurred: this likely means that there is no plot for this player."

    # convert the string to bytes
    img_bytes = BytesIO(plot)

    # encode the bytes object to base64
    encoding = b64encode(img_bytes.getvalue()).decode()

    # create the base64 string
    img_b64 = 'data:image/png;base64,{}'.format(encoding)

    return html.Img(src=img_b64, style={'maxWidth': '95%'})

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

def get_player_headshot(player_id, file_path = 'assets/csv/bigquery/2022_player_current_team.csv'):
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
