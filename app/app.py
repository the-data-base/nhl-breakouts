#-------------------------------------------------
#-1- Dependencies
#-------------------------------------------------


#-- Libraries
from base64 import b64encode
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from datetime import date, datetime
import base64
import numpy as np
import re

#-- Modules
from utils.common_functions import get_player_headshot, plot_comparisons, normalize_xg_dataframe_by_chunk

#-------------------------------------------------
#-2- Helper functions
#-------------------------------------------------

#-- Function to read csvs
def read_data(file_path):
    return pd.read_csv(file_path, delimiter=',')

#-- Function to replace special characters found in player_full_name
def replace_special_chars(input_str):
  special_chars = {
      'á': 'a', 'Á': 'A', 'ä': 'a', 'Ä': 'A', 'é': 'e', 'É': 'E', 'è': 'e', 'È': 'E', 'ê': 'e', 'Ê': 'E',
      'í': 'i', 'Í': 'I', 'ï': 'i', 'Ï': 'I', 'ó': 'o', 'Ó': 'O', 'ö': 'o', 'Ö': 'O', 'ô': 'o', 'Ô': 'O',
      'ú': 'u', 'Ú': 'U', 'ü': 'u', 'Ü': 'U', 'û': 'u', 'Û': 'U', 'ñ': 'n', 'Ñ': 'N', 'ç': 'c', 'Ç': 'C',
      'ß': 'ss', 'Æ': 'AE', 'æ': 'ae', 'Ø': 'O', 'ø': 'o', 'ł': 'l', 'Ł': 'L', 'ń': 'n', 'Ń': 'N',
      'ś': 's', 'Ś': 'S', 'ć': 'c', 'Ć': 'C', 'ź': 'z', 'Ź': 'Z', 'ż': 'z', 'Ż': 'Z', 'ğ': 'g', 'Ğ': 'G',
      'şı': 'si', 'Ş': 'Si', 'ķ': 'k', 'Ķ': 'K', 'š': 's', 'Š': 'S', 'č': 'c', 'Č': 'C', 'ž': 'z', 'Ž': 'Z',
      'ň': 'n', 'Ň': 'N', 'ř': 'r', 'Ř': 'R', 'ý': 'y', 'Ý': 'Y', 'ů': 'u', 'Ů': 'U', 'ţ': 't', 'Ţ': 'T',
      'ă': 'a', 'Ă': 'A', 'ş': 's', 'Ş': 'S', 'ď': 'd', 'Ď': 'D', 'ř': 'r', 'Ř': 'R', 'ť': 't', 'Ť': 'T',
      'ĺ': 'l', 'Ĺ': 'L', 'ć': 'c', 'Ć': 'C', 'đ': 'd', 'Đ': 'D', 'ŕ': 'r', 'Ŕ': 'R', 'ľ': 'l', 'Ľ': 'L',
      'ŝ': 's', 'Ŝ': 'S', 'ĥ': 'h', 'Ĥ': 'H', 'ĵ': 'j', 'Ĵ': 'J', 'ŵ': 'w', 'Ŵ': 'W', 'ŷ': 'y', 'Ŷ': 'Y',
      'ẑ': 'z', 'Ẑ': 'Z', 'ơ': 'o', 'Ơ': 'O', 'ī': 'i', 'Ī': 'I', 'ū': 'u', 'Ū': 'U', 'ț': 't', 'Ț': 'T',
      'ș': 's', 'Ș': 'S'
  }
  # Use a regular expression to match and replace special characters
  pattern = re.compile("|".join(map(re.escape, special_chars.keys())))
  return pattern.sub(lambda match: special_chars[match.group(0)], input_str)

#-- Function to create a new player name based on their first initial + last name to help join names spent differently
def format_player_name(player_name):
    name_parts = player_name.split()
    if len(name_parts) >= 2:
        first_initial = name_parts[0][0].upper()
        last_name = name_parts[-1]
        formatted_name = first_initial + ' ' + last_name
    else:
        formatted_name = player_name.replace('.', '')  # Remove dots if present
    return formatted_name

#-- Function (custom data cleaning) to cleanup cols after joining ranks df to salary cap data
def col_cleanup(df, suffix, keep_cols):
    # Replace column values
    for col in ['Active', 'Contract Start', 'Contract End', 'Term Remaining', 'Cap Hit', 'AAV']:
        col_name = f'{col}{suffix}'
        df[f'{col}'] = df[f'{col_name}']

    # Keep specific columns
    df = df[keep_cols]

    return df

#-- Function to prepare the player ranks dataframe (all)
def prepare_clean_ranks_table(df, sort_col = 'EV XG'):
    df['player_name'] = df['player_name'].apply(replace_special_chars)
    df2 = df[['player_name', 'primary_position_name', 'current_team_code', 'birth_date', 'shoots_catches', 'season', 'season_window', 'gp', 'toi_m', 'EV XG', 'EV Offense', 'EV Defense','Finishing','Gx60', 'A1x60', 'PP','PK', 'Penalty']]
    df2 = df2.rename(columns={'player_name': 'Player Name',
                              'primary_position_name': 'Position',
                              'current_team_code': 'Current Team',
                              'birth_date': 'DOB',
                              'shoots_catches': 'Shoots',
                              'season': 'Season',
                              'season_window': 'Season Window',
                              'toi_m': 'TOI (mins)',
                              'gp':'GP'})
    float_columns = df2.select_dtypes(include=['float64']).columns
    df2[float_columns] = df2[float_columns].round(1)
    return df2.sort_values(by=f'{sort_col}', ascending = False)

#-- Function to prepare the player ranks dataframe (all)
def prepare_clean_cap_table(df):
    df2 = df[['player_full_name', 'active_flag', 'team', 'signing_date', 'exp_year', 'years_left', 'cap_hit_format','aav_format']]
    df2 = df2.rename(columns={'player_full_name': 'Player Name',
                              'active_flag': 'Active',
                              'team': 'Current Team',
                              'signing_date': 'Contract Start',
                              'exp_year': 'Contract End',
                              'years_left': 'Term Remaining',
                              'cap_hit_format': 'Cap Hit',
                              'aav_format': 'AAV'})
    return df2

#-- Function to join cap data to ranks table
def join_ranks_cap_data_raw(df1, df2, keep_cols = ['player_id', 'player_name', 'game_type', 'season', 'season_window',
'primary_position_name', 'primary_position_type', 'birth_date',
'nationality', 'height', 'weight', 'primary_number', 'shoots_catches',
'current_team_id', 'current_team_full_name', 'current_team_name',
'current_team_code', 'Avg TOI', 'TOI', 'EV XG', 'EV Offense',
'EV Defense', 'PP', 'PK', 'Finishing', 'Gx60', 'XGx60', 'A1x60',
'Penalty', 'EV XG 2', 'EV Offense 2', 'EV Defense 2', 'PP 2', 'PK 2',
'Finishing 2', 'Gx60 2', 'A1x60 2', 'Penalty 2', 'Competition',
'Teammates', 'gp', 'xg_diff', 'xg_ev_diff', 'xgf_ev', 'xga_ev',
'xg_pp_diff', 'xg_sh_diff', 'gae', 'goals_per60', 'a1_per60', 'xgf',
'xga', 'goals', 'a1', 'toi_m', 'avg_toi_m', 'xg_ev_diff_per60',
'xgf_ev_per60', 'xga_ev_per60', 'xg_pp_diff_per60', 'xg_sh_diff_per60',
'gae_per60', 'minor_pim_diff_per60','Active', 'Contract Start', 'Contract End', 'Term Remaining', 'Cap Hit', 'AAV'], verbose = False):

    #... remove special chars in player_name
    df1['player_name'] = df1['player_name'].apply(replace_special_chars)

    # ...make a second player name key to join
    df1['join_player_name'] = df1['player_name'].apply(format_player_name)
    df2['join_player_name'] = df2['Player Name'].apply(format_player_name)

    # ...left join df1 to df2 on "player_name" = "player_full_name" and "team_code" = "team_code"
    merged_df1 = pd.merge(df1, df2, how='left', left_on=['player_name', 'current_team_code'], right_on=['Player Name', 'Current Team'], suffixes=('', '_1'))
    matched_df1 = merged_df1[merged_df1['AAV'].notnull()]
    unmatched_df1 = merged_df1[merged_df1['AAV'].isnull()]

    # ...left join df1 to df2 on "player_name" = "player_full_name" and "team_code" = "team_code"
    merged_df2 = pd.merge(unmatched_df1, df2, how='left', left_on=['player_name'], right_on = ['Player Name'], suffixes=('', '_2'))
    matched_df2 = merged_df2[merged_df2['AAV_2'].notnull()]
    unmatched_df2 = merged_df2[merged_df2['AAV_2'].isnull()]

    # ...left join df1 to df2 on "player_name" = "player_full_name" and "team_code" = "team_code"
    merged_df3 = pd.merge(unmatched_df2, df2, how='left', left_on=['join_player_name'], right_on = ['join_player_name'], suffixes=('', '_3'))
    matched_df3 = merged_df3[merged_df3['AAV_3'].notnull()]
    unmatched_df3 = merged_df3[merged_df3['AAV_3'].isnull()]

    # ...run custom function cleaner
    matched_df1_clean = matched_df1[keep_cols]
    matched_df2_clean = col_cleanup(matched_df2, "_2", keep_cols)
    matched_df3_clean = col_cleanup(matched_df3, "_3", keep_cols)
    unmatched_df3_clean = unmatched_df3[keep_cols]

    #... finally...
    final_df = pd.concat([matched_df1_clean, matched_df2_clean, matched_df3_clean, unmatched_df3_clean])

    #... user message
    if verbose == True:
        print(f'rows: {len(final_df)}, actives: {int((final_df["Active"] == 1).sum())}, free_agents: {int((final_df["Active"] == 0).sum())}, inactives: {final_df["AAV"].isna().sum()}')

    return final_df

#-- Function to partition out ranks_df by season & season window
def season_window_partitions(df, sort_col = 'EV XG'):
    df['Season'] = np.where(df['Season Window'] == 'Last 3 seasons', 'Last 3 Seasons', df['Season'])
    ranks_df1 = df[df['Season Window'] == 'Last 3 seasons'].sort_values(by=f'{sort_col}', ascending = False)
    ranks_df2 = df[df['Season Window'] == '1 season'].sort_values(by=f'{sort_col}', ascending = False)
    ranks_df1 = ranks_df1.drop(columns=['Season Window', 'DOB', 'Shoots', 'join_player_name'])
    ranks_df2 = ranks_df2.drop(columns=['Season Window', 'DOB', 'Shoots', 'join_player_name'])

    return ranks_df1, ranks_df2

#-- Function to join cap data to ranks table
def join_ranks_cap_data(df1, df2, keep_cols = ['Player Name', 'Position', 'Current Team', 'DOB', 'Shoots', 'Season', 'Season Window', 'EV XG', 'EV Offense', 'EV Defense', 'Finishing', 'Gx60', 'A1x60', 'PP', 'PK', 'Penalty', 'TOI (mins)', 'GP', 'Active', 'Contract Start', 'Contract End', 'Term Remaining', 'Cap Hit', 'AAV'], verbose = False):

    # ...make a second player name key to join
    df1['join_player_name'] = df1['Player Name'].apply(format_player_name)
    df2['join_player_name'] = df2['Player Name'].apply(format_player_name)

    # ...left join df1 to df2 on "player_name" = "player_full_name" and "team_code" = "team_code"
    merged_df1 = pd.merge(df1, df2, how='left', left_on=['Player Name', 'Current Team'], right_on=['Player Name', 'Current Team'], suffixes=('', '_1'))
    matched_df1 = merged_df1[merged_df1['AAV'].notnull()]
    unmatched_df1 = merged_df1[merged_df1['AAV'].isnull()]

    # ...left join df1 to df2 on "player_name" = "player_full_name" and "team_code" = "team_code"
    merged_df2 = pd.merge(unmatched_df1, df2, how='left', left_on=['Player Name'], right_on = ['Player Name'], suffixes=('', '_2'))
    matched_df2 = merged_df2[merged_df2['AAV_2'].notnull()]
    unmatched_df2 = merged_df2[merged_df2['AAV_2'].isnull()]

    # ...left join df1 to df2 on "player_name" = "player_full_name" and "team_code" = "team_code"
    merged_df3 = pd.merge(unmatched_df2, df2, how='left', left_on=['join_player_name'], right_on = ['join_player_name'], suffixes=('', '_3'))
    matched_df3 = merged_df3[merged_df3['AAV_3'].notnull()]
    unmatched_df3 = merged_df3[merged_df3['AAV_3'].isnull()]

    # ...run custom function cleaner
    matched_df1_clean = matched_df1[keep_cols]
    matched_df2_clean = col_cleanup(matched_df2, "_2", keep_cols)
    matched_df3_clean = col_cleanup(matched_df3, "_3", keep_cols)
    unmatched_df3_clean = unmatched_df3[keep_cols]

    #... finally...
    final_df = pd.concat([matched_df1_clean, matched_df2_clean, matched_df3_clean, unmatched_df3_clean])

    #... user message
    if verbose == True:
        print(f'rows: {len(final_df)}, actives: {int((final_df["Active"] == 1).sum())}, free_agents: {int((final_df["Active"] == 0).sum())}, inactives: {final_df["AAV"].isna().sum()}')

    return final_df

#-- Function to partition out ranks_df by season & season window
def season_window_partitions(df, sort_col = 'EV XG'):
    df['Season'] = np.where(df['Season Window'] == 'Last 3 seasons', 'Last 3 Seasons', df['Season'])
    ranks_df1 = df[df['Season Window'] == 'Last 3 seasons'].sort_values(by=f'{sort_col}', ascending = False)
    ranks_df2 = df[df['Season Window'] == '1 season'].sort_values(by=f'{sort_col}', ascending = False)
    ranks_df1 = ranks_df1.drop(columns=['Season Window', 'DOB', 'Shoots', 'join_player_name'])
    ranks_df2 = ranks_df2.drop(columns=['Season Window', 'DOB', 'Shoots', 'join_player_name'])

    return ranks_df1, ranks_df2


#-- Function to create a card with given title and value
def create_card(title):
    card = dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.H2("Default", className="text-nowrap", id=f"{title.lower().replace(' ', '-')}-card-value"),
                html.H4(title, className="text-nowrap", id=f"{title.lower().replace(' ', '-')}-card-title"),
            ]),
            style={"margin": "0px", "padding": "0px"}  # Remove margin and padding
        ),
        width={"size": 4},
    )
    return card

#-- Function to create stat ring around card
def create_stat_ring(title):
    return dbc.Col(
        html.Center(
        id = f"{title.lower().replace(' ', '-')}-ring-progress-value",
        ))

#-- Function to calculate age
def calculate_age(born):
    born_dt = datetime.strptime(born, "%Y-%m-%d")
    today = date.today()
    return today.year - born_dt.year - ((today.month, today.day) < (born_dt.month, born_dt.day))

#-- Function to get information out of player attributes out of ranks df and store as a dictionary for player cards downstream (raw ranks needed)
def get_player_card1(player_name, df, player_name_col):
    player_df = df[df[player_name_col] == player_name]
    return {
        'id': player_df['player_id'].values[0],
        'name': player_name,
        'age': calculate_age(player_df['birth_date'].values[0]),
        'position': player_df['primary_position_name'].values[0],
        'shoots': player_df['shoots_catches'].values[0],
        'number': player_df['primary_number'].values[0],
        'height': player_df['height'].values[0],
        'weight': player_df['weight'].values[0],
        'team_code': player_df['current_team_code'].values[0],
        'team_name': player_df['current_team_name'].values[0]
    }
#-- Function to get information out of player attributes out of ranks df and store as a dictionary for player cards downstream (joined cap needed)
def get_player_card2(player_name, df, player_name_col):
    player_df = df[df[player_name_col] == player_name]

   # Initialize attributes with "Inactive"
    contract_start = "Inactive"
    contract_end = "Inactive"
    cap_hit = "Inactive"
    aav = "Inactive"
    term = "Inactive"

    # Check if player_df is not empty
    if not player_df.empty:
        # Update attributes if values exist
        contract_start = player_df['Contract Start'].values[0]
        contract_end = player_df['Contract End'].values[0]
        cap_hit = player_df['Cap Hit'].values[0]
        aav = player_df['AAV'].values[0]
        term = player_df['Term Remaining'].values[0]

    return {
        'name': player_name,
        'contract_start': contract_start,
        'contract_end': contract_end,
        'cap_hit': cap_hit,
        'aav': aav,
        'term': term
    }


#-- Function to get information out of player metrics out of ranks df and store as a dictionary for player cards downstream
def get_player_stats(player_name, df):
    player_df = df[df['Player Name'] == player_name]
    stats = {
        'ev_xg': player_df['EV XG'].values[0],
        'ev_offense': player_df['EV Offense'].values[0],
        'ev_defense': player_df['EV Defense'].values[0],
        'finishing': player_df['Finishing'].values[0],
        'gx60': player_df['Gx60'].values[0],
        'a1x60': player_df['A1x60'].values[0],
        'pp': player_df['PP'].values[0],
        'pk': player_df['PK'].values[0],
        'penalty': player_df['Penalty'].values[0],
    }
    # round to 2 decimal places
    for key, value in stats.items():
        stats[key] = round(value, 1)

    return stats

#-- Function to get player attributes from ranks_df
def set_player_dropdown_options(df, player_name_col):
    return sorted([{'label': player, 'value': player} for player in df[player_name_col].unique()], key=lambda x: x['label'])

#-- Function to create a multi-line chart
def create_metric_season_trend_viz(df, x_column='Season', y_columns=['EV Offense', 'EV Defense', 'Finishing'], y_range=[0, 100], player_name='Connor McDavid'):
    df2 = df[df['Player Name'] == player_name].copy()
    df2 = df2.sort_values(by='Season', ascending=True)
    df2['Season'] = df2['Season'].astype(str)

    # Create the figure object
    fig = px.line(df2, x=x_column, y=y_columns)

    # Define custom line colors for each trace (line)
    line_colors = ['#3880bc', '#f7bb7e', '#7630ff ']  # Purple, Blue, Magenta

    # Trend line chart layout and style modifications
    for i, color in enumerate(line_colors):
        fig.update_traces(
            selector=dict(name=y_columns[i]),  # Select the trace by name
            line=dict(width=3, color=color),  # Set line width and color
            marker=dict(size=8),  # Increase marker size
            hovertemplate=f'<b>{y_columns[i]}:</b> %{{y:.2f}}%<extra></extra>',  # Format hover text with '%' at the end
        )

    # Trend line chart layout and style modifications
    fig.update_traces(
        line=dict(width=3),  # Increase line width
        marker=dict(size=8),  # Increase marker size
        hovertemplate='<b>%{y:.2f}%</b><extra></extra>',  # Format hover text with '%' at the end
    )
    fig.update_layout(
        legend_title_text='Metrics',  # Change the legend title to "Metrics"
        xaxis_title="Season",
        yaxis_title="Rating",
        font=dict(family="Calibri", size=12, color='#ffffff'),  # Customize font
        paper_bgcolor="rgba(0,0,0,0)",  # Set background color to transparent (RGBA)
        plot_bgcolor="rgba(0,0,0,0)",  # Set plot background color
        hovermode="x",  # Display hover info for the nearest point along the x-axis
        xaxis=dict(showgrid=False),  # Remove x-axis gridlines
        yaxis=dict(showgrid=False),  # Remove y-axis gridlines
        margin=dict(b=0),  # Reduce the margin at the bottom (adjust as needed)
        height=275,  # Set the height of the visualiza  tion
        )
    # Set the y-axis range
    fig.update_yaxes(range=y_range)

    return fig

#-------------------------------------------------
#-3- Pre-load variables
#-------------------------------------------------

#-- Cap data
#... raw
cap_df_raw = read_data('assets/csv/capfriendly/capfriendly_data_clean.csv')
#... clean
cap_df = prepare_clean_cap_table(cap_df_raw)

#-- Player ranks data
#... raw
ranks_df_raw = read_data('assets/csv/bigquery/202202_player_ranks.csv')
ranks_cap_df_raw = join_ranks_cap_data_raw(ranks_df_raw, cap_df)
#... clean
ranks_df = prepare_clean_ranks_table(ranks_df_raw, "EV XG")
ranks_cap_df = join_ranks_cap_data(ranks_df, cap_df)
#... final
ranks_3y_df, ranks_1y_df = season_window_partitions(ranks_df, "EV XG")

#-- Set colors
colors = {
    'background': '#111111',
    'text': 'f6c1b2',
    'title': '#ffffff'
    }

#-- Calculate the minimum and maximum TOI values from your DataFrame
min_toi_value = ranks_df['TOI (mins)'].min()
max_toi_value = ranks_df['TOI (mins)'].max()

#-- Create a multi-line chart (uses a bunch of defaults)
metric_season_trend = create_metric_season_trend_viz(ranks_1y_df)

#-- Player stat cards
cards = html.Div([
    dbc.Row([
        create_stat_ring("EV XG"),
        create_stat_ring("EV Offense"),
        create_stat_ring("EV Defense"),
        create_stat_ring("Finishing"),
        create_stat_ring("Gx60"),
        create_stat_ring("A1x60"),
        create_stat_ring("PP"),
        create_stat_ring("PK"),
        create_stat_ring("Penalty"),
    ],
    style={'margin-right': '1px'}),  # Adjust the margin-right value to reduce spacing

])

# Define custom CSS for the menu outline
menu_outline_style = {
    'border': '1px solid rgba(255, 255, 255, 0.5)',  # Light border
    'border-radius': '4px',  # Rounded corners
    'padding': '0px',  # Add padding for spacing
}

# Normalize XG shot coordinates when the app starts
normalize_xg_dataframe_by_chunk()

#-------------------------------------------------
#-4- App
#-------------------------------------------------

#-- Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])  # Use the DARKLY theme for dark mode

#-- Initialize the server
server = app.server

#-- Define app layout
app.layout = html.Div([

    #-------------------------------------------------
    #-4.1- App: setup
    #-------------------------------------------------
    dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(
                    html.Img(src=app.get_asset_url('images/the_data_base_logo.jpg'), height="40px"),
                    width="auto",
                ),
                dbc.Col(
                    dbc.NavbarBrand("NHL App", style={'margin': '0', 'padding-left': '10px', 'font-family': 'Calibri', 'font-size': '24px'}),
                    width="auto",
                ),
            ],
            style={'text-align': 'left', 'margin-right': '0'}
            ),
            dbc.Row([
                dbc.Col(
                    dbc.DropdownMenu(
                        label="Menu",
                        children=[
                            dbc.DropdownMenuItem("Home", href="/"),
                            dbc.DropdownMenuItem("About", href="/about"),
                        ],
                        className="ml-auto",  # Align the dropdown menu to the right
                    color = 'dark',
                    style = {'padding-left':'10px', **menu_outline_style},
                    ),
                )
            ],
            style={'text-align': 'right', 'margin-right': '0'}
            ),
        ]),
        color="dark",
        dark=True,
    ),

    # Player headshot
    html.Div(
        id='player-image-div',
        children=html.Img(
            id='player-image'
        )
    ),

    # Player card
    html.Div(
        id='player-info-div',
        style={'text-align': 'center'},
        children=dbc.Row([
            html.Div([
                html.H1(
                    id='player-info-name',
                    style={'white-space': 'nowrap'}
                ),
                html.Div(id='player-info-age', style={'display': 'inline-block'}),
                html.Div(id='player-info-team-name', style={'display': 'inline-block'}),
                html.Div(id='player-info-position', style={'display': 'inline-block'}),
                html.Div(id='player-info-shoots', style={'display': 'inline-block'}),
                html.P(id='player-info-cap')
            ]),
        ])
    ),

    # New row for a searchable dropdown menu containing player names
    dbc.Row([
        # dropdown: player-name
        dbc.Col(
            html.Div([
                html.Label('Player:', style={'color': colors['text'], 'font-weight': 'bold', 'text-align': 'center'}),
                dcc.Dropdown(
                    id='player-name-dropdown',
                    options=set_player_dropdown_options(ranks_3y_df[ranks_3y_df['Position'] != 'Goalie'], "Player Name"),
                    value='Connor McDavid',
                    clearable=False
                )],
            ),
        ),
        # dropdown: season-year
        dbc.Col(
            html.Div([
                html.Label('Season:', style={'color': colors['text'], 'font-weight': 'bold', 'text-align': 'center'}),
                dcc.Dropdown(
                    id='season-year-dropdown',
                    options=[
                        {'label': 'Current', 'value': '2023'}
                    ],
                    value='2023',
                    clearable=False,
                    style={'color': '#000000'}
                )],
            ),
        ), # column
    ],
    justify='center',
    style={'margin': '1px'}  # Add right margin to the position filter
    ), # row

    html.Br(),

    #-------------------------------------------------
    #-4.2- App: Player Summary stats
    #-------------------------------------------------

    # Cards for player-specific metrics
    html.Div(dbc.Container(cards)),

    # Trend line
    dcc.Graph(
        id='metric-season-trend',
        figure=metric_season_trend,
        style={"margin-top": "0px"}  # Remove the margin at the top of the trend line
    ),

    html.Br(),

    #-------------------------------------------------
    #-4.3- App: Shooting Ability
    #-------------------------------------------------

    # Rink image
    dbc.Row(
        # This row is going to contain 2 main columns: the rink image and data table
        dbc.Col(
            html.Div(
                dbc.Spinner(
                    children=[
                        html.Div(
                            dcc.RadioItems(
                                id='rink-image-comparison-type',
                                options=[
                                    {
                                        'label': html.Div('Against League', style={'font-size': 15, 'padding-right': 10, 'display': 'inline'}),
                                        'value': 'against_league',
                                    },
                                    {
                                        'label': html.Div('Individual', style={'font-size': 15, 'padding-right': 10, 'display': 'inline'}),
                                        'value': 'individual',
                                    },
                                ],
                                value='against_league', # Set the default value
                                inline=True, # configure the RadioItems to be displayed horizontally
                                style={'padding': '10px'},  # Add padding to the radio items
                            ),
                            style={'text-align': 'left'}
                        ),
                        html.Div(html.H2(id='rink-image-title'), style={'textAlign': 'center'}),
                        html.Div(id='rink-image'),
                    ]
                ),
                style={'textAlign': 'center'}
            ),
            width=12,
            style={'height': '100%'}
        ),
        justify='center',  # Center the row horizontally
        # style={'height': 200},
    ),

    html.Br(),


    #-------------------------------------------------
    #-4.4- App: Exploring player ratings
    #-------------------------------------------------

    html.H3("Explore Player Ratings", style={'text-align': 'center', 'color': '#ffffff'}),

    # Horizontal radio button group for "Position"
    dbc.Row([
        # dropdown: position
        dbc.Col(
            html.Div([
                html.Label('Seasons:', style={'color': colors['text'], 'font-weight': 'bold', 'text-align': 'center'}),
                dcc.Dropdown(
                    id='season-breakdown-dropdown',  # Update the ID
                    options=[
                        {'label': 'Group last 3', 'value': 'Group'},
                        {'label': 'Breakdown last 3', 'value': 'Breakdown'},
                    ],
                    value='Group',  # Set the default value to "All"
                    clearable=False,
                    style={'color': '#000000'}
                )],
            ),
        ),
        # dropdown: position
        dbc.Col(
            html.Div([
                html.Label('Position:', style={'color': colors['text'], 'font-weight': 'bold', 'text-align': 'center'}),
                dcc.Dropdown(
                    id='position-dropdown',  # Update the ID
                    options=[
                        {'label': 'All', 'value': 'All'},  # Add an "All" option
                        {'label': 'Forwards', 'value': 'Forwards'},
                        {'label': 'Defenseman', 'value': 'Defenseman'},
                        {'label': 'Goalie', 'value': 'Goalie'},
                        {'label': 'Center', 'value': 'Center'},
                        {'label': 'Right Wing', 'value': 'Right Wing'},
                        {'label': 'Left Wing', 'value': 'Left Wing'},
                    ],
                    value='All',  # Set the default value to "All"
                    clearable=False,
                    style={'color': '#000000'}
                )],
            ),
        )
        ],
        justify='center',
        style={'margin': '1px'}  # Add right margin to the position filter
        ),

    html.Br(),

    dbc.Row(
        html.Div([
                html.Label('Minimum TOI (mins):', style={'color': colors['text'], 'font-weight': 'bold', 'text-align': 'center'}),
                dcc.RangeSlider(
                    id='toi-slider',
                    min=0,  # Set the minimum value
                    max=1000,  # Set the maximum value
                    step=50,  # Set the step value
                    marks={i: str(i) for i in range(0, 1001, 250)},  # Add marks for each 100-unit interval
                    value=[min_toi_value],  # Set the initial value to cover the entire range
                    tooltip={"placement": "bottom"},  # Show tooltips below the slider
                ),
            ]),
    ),

    html.Br(),

    # A new row that contains the table
    dbc.Row(
        dbc.Col(
            dash_table.DataTable(
                id='all-players-data-table',
                columns=[
                    {'name': col, 'id': col}
                    for col in ranks_3y_df.columns
                ],
                data=ranks_3y_df.to_dict('records'),
                page_size=20,
                style_table={
                    'overflowX': 'auto',
                },
                style_header={
                    'backgroundColor': '#343a40',
                    'color': 'white',
                    'fontWeight': 'bold',
                },
                style_cell={
                    'backgroundColor': '#343a40',
                    'color': 'white',
                    'textAlign': 'left',
                    'font-family': 'Calibri, sans-serif',
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#444d56',
                    },
                ],
                sort_action='native',  # Use built-in sorting functionality
                sort_mode='multi',  # Allow multi-column sorting
            ),
            width=12
        ),
    ),
])

#-------------------------------------------------
#-5- React callbacks
#-------------------------------------------------

# Callback to update the DataTable based on selected position, season breakdown, and TOI range
@app.callback(
    Output('all-players-data-table', 'data'),
    Input('position-dropdown', 'value'),
    Input('season-breakdown-dropdown', 'value'),
    Input('toi-slider', 'value')
)
def update_table(selected_position, selected_season, toi_range):
    min_toi = toi_range[0]  # Get the selected TOI range (use [0] to get the minimum value)

    if selected_season == 'Group':
        df = ranks_3y_df

    elif selected_season == 'Breakdown':
        df = ranks_1y_df

    if selected_position == 'All':
        # Show all positions within the TOI range
        filtered_df = df[(df['TOI (mins)'] >= min_toi)]
    elif selected_position == 'Forwards':
        # Map "Forward" to "Center," "Left Wing," and "Right Wing" within the TOI range
        filtered_df = df[(df['Position'].isin(['Center', 'Left Wing', 'Right Wing'])) &
                            (df['TOI (mins)'] >= min_toi)]
    else:
        filtered_df = df[(df['Position'] == selected_position) &
                        (df['TOI (mins)'] >= min_toi)]
    return filtered_df.to_dict('records')


@callback(
    Output(component_id='ev-xg-ring-progress-value', component_property='children'),
    Output(component_id='ev-offense-ring-progress-value', component_property='children'),
    Output(component_id='ev-defense-ring-progress-value', component_property='children'),
    Output(component_id='finishing-ring-progress-value', component_property='children'),
    Output(component_id='gx60-ring-progress-value', component_property='children'),
    Output(component_id='a1x60-ring-progress-value', component_property='children'),
    Output(component_id='pp-ring-progress-value', component_property='children'),
    Output(component_id='pk-ring-progress-value', component_property='children'),
    Output(component_id='penalty-ring-progress-value', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value')

)
def update_player_stat_rings(player_name, df = ranks_3y_df):
    stats = get_player_stats(player_name, df)

    # Create a mapping of stat display names to their corresponding column names
    stats_mapping = {
        'ev_xg': 'EV XG',
        'ev_offense': 'EV Offense',
        'ev_defense': 'EV Defense',
        'finishing': 'Finishing',
        'gx60': 'Gx60',
        'a1x60': 'A1x60',
        'pp': 'PP',
        'pk': 'PK',
        'penalty': 'Penalty',
    }
    stats_rings = []
    for column_name, display_name in stats_mapping.items():
        # Conditionally set the ring color based on the stat value
        if stats[column_name] > 80:
            color = 'green'
        elif stats[column_name] > 50:
            color = '#9ACD32'
        elif stats[column_name] > 30:
            color = 'yellow'
        else:
            color = 'red'

        # Build the ring progress component for each stat
        stats_rings.append(dmc.RingProgress(
            size=100,
            thickness=4,
            sections = [{'value': stats[column_name], 'color': color}],
            roundCaps=True,
            rootColor='rgba(0, 0, 0, 0)',
            label = dmc.Stack(
                children=[
                    dmc.Text(display_name, size='xs'),
                    dmc.Text(stats[column_name], size=20, weight='500', color=color),
                ],
                align='center',
                spacing=0,
                style={'height': 50},
            )
        ))
    # The size of this list must correspond to the number of outputs in the callback
    # The order must also match the order of the outputs
    return stats_rings

@app.callback(
    Output('metric-season-trend', 'figure'),
    Input('player-name-dropdown', 'value'),
    )
def update_metric_season_trend(selected_player, df = ranks_1y_df):
    # Filter the ranks DataFrame for the selected player and season
    filtered_df = df[(df['Player Name'] == selected_player)]
    # Create or update the multi-line chart for the selected player
    fig = create_metric_season_trend_viz(filtered_df, player_name=selected_player)

    return fig

@callback(
    Output(component_id='player-info-age', component_property='children'),
    Output(component_id='player-info-team-name', component_property='children'),
    Output(component_id='player-info-position', component_property='children'),
    Output(component_id='player-info-shoots', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_stats1(selected_player, df=ranks_cap_df_raw, player_name_col = 'player_name'):
    stats = get_player_card1(selected_player, df, player_name_col)
    components = []
    for stat in ['age', 'team_name', 'position', 'shoots']:
        if stat == 'age':
            components.append(
                html.P('Age: {} |'.format(stats[stat]), style={'margin-bottom': 0})
            )
        if stat == 'team_name':
            components.append(
                html.P(
                    children=[
                        html.Img(
                        src=app.get_asset_url('logos/teams/{}.png'.format(stats['team_code'])),
                        height=18
                        ),
                        html.P(' {} |'.format(stats['team_code']), style={'display': 'inline-block', 'padding-right': 5, 'margin-bottom': 0})
                    ]
                )
            )
        if stat == 'position':
            components.append(
                html.P('Position: {} |'.format(stats[stat]), style={'padding-right': 5, 'margin-bottom': 0})
            )
        if stat == 'shoots':
            components.append(
                html.P('Shoots: {}'.format(stats[stat]), style={'margin-bottom': 0})
            )

    return components

@callback(
    Output(component_id='player-info-cap', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_stats2(selected_player, df = ranks_cap_df, player_name_col = 'Player Name'):
    stats = get_player_card2(selected_player, df, player_name_col)
    # Check if term is not NaN before rounding
    if not pd.isna(stats["term"]):
        term_rounded = round(stats["term"])
    else:
        term_rounded = "Inactive"

    return f'Cap: {stats["cap_hit"]} x {term_rounded}'

@callback(
    Output(component_id='player-info-name', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_name(selected_player, df = ranks_cap_df_raw):
    return selected_player

@callback(
    Output(component_id='rink-image-title', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value'),
    Input(component_id='rink-image-comparison-type', component_property='value')
)
def set_rink_image_title(player_name, comparison_type):
    if comparison_type == 'against_league':
        return f'{player_name} vs. League'
    elif comparison_type == 'individual':
        return f'{player_name} Shot XG'

@callback(
    Output(component_id='rink-image', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value'),
    Input(component_id='rink-image-comparison-type', component_property='value')
)
def plot_rink(player_name, comparison_type):
    fig = plot_comparisons(player_name, comparison_type)
    img_bytes = fig.to_image(format='png')
    encoding = b64encode(img_bytes).decode()
    img_b64 = 'data:image/png;base64,{}'.format(encoding)
    return html.Img(src=img_b64, style={'maxWidth': '95%'})

@callback(
    Output(component_id='player-image', component_property='src'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_headshot(player_name, df = ranks_cap_df_raw, player_name_col = 'player_name'):
    stats = get_player_card1(player_name, df, player_name_col)
    return get_player_headshot(stats['id'])

@callback(
    # Div components
    Output(component_id='player-image-div', component_property='style'),
    # Headshot component
    Output(component_id='player-image', component_property='style'),
    Input(component_id='player-name-dropdown', component_property='value'),
)
def set_player_card_colors(selected_player, df = ranks_cap_df_raw):
    stats = get_player_card1(selected_player, df, player_name_col = 'player_name')
    colors = pd.read_csv('assets/csv/colors/team_colors.csv')
    # filter team_colors dataframe for the selected player's team
    team_colors = colors[colors['team_code'] == stats['team_code']]
    # get the primary and secondary colors for the selected player's team
    primary_color = team_colors[team_colors['color_type']=='primary'].iloc[0]['hex']
    secondary_color = team_colors[team_colors['color_type']=='secondary'].iloc[0]['hex']

    # Div styles
    style_primary_div = {'background-color': primary_color, 'text-align': 'center'}

    # Headshot style
    style_headshot = {'height': '140px', 'width': 'auto', 'border-radius': '50%', 'background-color': 'white', 'border': f'5px solid {secondary_color}'}


    return style_primary_div, style_headshot


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
