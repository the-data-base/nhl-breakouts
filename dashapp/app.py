# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
#import plotly.graph_objects as go
from datetime import date, datetime


# Modules
from dashapp.utils.extract.extract import get_player_headshot
from dashapp.utils.transform.transform import plot_comparisons

# Read data from local CSVs and create the initial DataFrame
# TODO: dynamically read data from Cloud Storage
def read_data(file_path):
    return pd.read_csv(file_path, delimiter=',')

ranks_df = read_data('data/bq_results/202202_player_ranks.csv')

def prepare_clean_ranks_table(df, sort_col = 'EV XG'):
    df2 = df[['player_name', 'primary_position_name', 'gp', 'toi_m', 'EV XG', 'EV Offense', 'EV Defense','Finishing','Gx60', 'A1x60', 'PP','PK', 'Penalty']]
    df2.rename(columns={'player_name': 'Player Name', 'primary_position_name': 'Position', 'toi_m': 'TOI (mins)', 'gp':'GP'}, inplace=True)
    float_columns = df2.select_dtypes(include=['float64']).columns
    df2[float_columns] = df2[float_columns].round(1)  # You can adjust the number of decimal places as needed
    return df2.sort_values(by=f'{sort_col}', ascending = False)

ranks_df2 = prepare_clean_ranks_table(ranks_df, "EV XG")

# Create a card with given title and value
def create_card(title):
    # Calculate the color based on the value (0 to 100)
    card = dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.H2("Default", className="text-nowrap", id=f"{title.lower().replace(' ', '-')}-card-value"),
                html.H4(title, className="text-nowrap", id=f"{title.lower().replace(' ', '-')}-card-title"),
            ]),
        )
    , width={"size": 4})
    return card

def create_stat_ring(title):
    return dbc.Col(
        html.Center(
        id = f"{title.lower().replace(' ', '-')}-ring-progress-value",
        )
    )

# Calculate age
def calculate_age(born):
    born_dt = datetime.strptime(born, "%Y-%m-%d")
    today = date.today()
    return today.year - born_dt.year - ((today.month, today.day) < (born_dt.month, born_dt.day))

def get_player_card(player_name):
    df = ranks_df
    player_df = df[df['player_name'] == player_name]
    return {
        'id': player_df['player_id'].values[0],
        'name': player_name,
        'age': calculate_age(player_df['birth_date'].values[0]),
        'country': player_df['nationality'].values[0],
        'position': player_df['primary_position_name'].values[0],
        'shoots': player_df['shoots_catches'].values[0],
        'number': player_df['primary_number'].values[0],
        'height': player_df['height'].values[0],
        'weight': player_df['weight'].values[0],
        'team_code': player_df['current_team_code'].values[0],
        'team_name': player_df['current_team_name'].values[0]
    }

def get_player_stats(player_name):
    df = ranks_df
    player_df = df[df['player_name'] == player_name]
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
        'toi': player_df['TOI'].values[0],
    }
    # round to 2 decimal places
    for key, value in stats.items():
        stats[key] = round(value, 1)

    return stats


def set_player_dropdown_options():
    df = ranks_df
    return [{'label': player, 'value': player} for player in df['player_name'].unique()]

# Set colors
colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'title': '#ffffff'
}

# Calculate the minimum and maximum TOI values from your DataFrame
min_toi_value = ranks_df2['TOI (mins)'].min()
max_toi_value = ranks_df2['TOI (mins)'].max()

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])  # Use the DARKLY theme for dark mode


# Player stat cards
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

# Define app layout
app.layout = html.Div([
    dbc.Navbar(
        dbc.Container([
            html.Img(src=app.get_asset_url('avatar.jpg'), height="40px"),
            dbc.NavbarBrand("NHL App", href="/"),
            dbc.DropdownMenu(
                label="Menu",
                children=[
                    dbc.DropdownMenuItem("Home", href="/"),
                    dbc.DropdownMenuItem("About", href="/about"),
                ],
            ),
        ]),
        color="dark",
        dark=True
    ),

    # Create a div for the header with an image, player name, and subtitles
    html.Div([
        html.Div(
            html.Img(
                id='player-image',
                height="150px",
                style={
                    'border-radius': '50%',  # Apply circular border
                    'background': '#ffffff',
                    'border': '3px solid #000000',  # Border color
                }
            ),
            style={
                'flex': '0 0 auto',  # Don't allow image to grow or shrink
                'margin': '5px',  # Add margin for spacing
            }
        ),
        html.Div([
            html.H1(
                id='player-name',
                style={
                    'color': colors['title'],
                    'font-weight': 'bold',  # Make the font bold
                    'margin-bottom': '5px',  # Add margin for spacing
                    'text-align': 'center',  # Center the H1 title horizontally
                }
            ),
            html.Div([
                html.H6(
                    id='player-stats-1',
                    style={
                        'color': colors['text'],
                    }
                ),
            ], style={'margin-left': '5px'}),  # Add margin for spacing
        ], style={'flex': '1', 'align-self': 'center'}),  # Allow text to grow, align to center
    ], style={
        'display': 'flex',
        'flex-direction': 'column',
        'align-items': 'center',
        'justify-content': 'center',
    }),

    # New row for a searchable dropdown menu containing player names
    # Align the dropdown menu to the center
    dbc.Row([
        dbc.Col(
            html.Div([
                html.Label('Player:', style={'color': colors['text'], 'font-weight': 'bold', 'text-align': 'center'}),
                dcc.Dropdown(
                    id='player-name-dropdown',
                    options=set_player_dropdown_options(),
                    value='Connor McDavid',
                    clearable=False
                )],
            ),
        ), # column
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


    # Cards for player-specific metrics
    html.Div(dbc.Container(cards)),

    # Rink image
    dbc.Container([
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    figure={},
                    id='rink',
                    style={'height': '100%', 'max-width': '100%', 'margin': '0 auto'},
                ),
            ),
            className="justify-content-center",
        ),],
        fluid=True,
        style={'width': '100%'},
    ),

    # Horizontal radio button group for "Position"
    dbc.Row([
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
            ), # column
            dbc.Col(
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
                ), # column
            ],
            justify='center',
            style={'margin': '1px'}  # Add right margin to the position filter
            ),

        html.Br(),

    # A new row that contains the table
    dbc.Row(
        dbc.Col(
            dash_table.DataTable(
                id='all-players-data-table',
                columns=[
                    {'name': col, 'id': col}
                    for col in ranks_df2.columns  # Automatically generate columns
                ],
                data=ranks_df2.to_dict('records'),
                page_size=20,
                style_table={
                    'overflowX': 'auto',
                    'padding-right': '20px',  # Add 20-pixel padding
                    'padding-left': '20px',  # Add 20-pixel padding
                },
                style_header={
                    'backgroundColor': '#343a40',
                    'color': 'white',
                    'fontWeight': 'bold',  # Make headers bold
                },
                style_cell={
                    'backgroundColor': '#343a40',
                    'color': 'white',
                    'textAlign': 'center',
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#444d56',
                    }
                ],
                # Enable sorting
                sort_action='native',  # Use built-in sorting functionality
                sort_mode='multi',  # Allow multi-column sorting
            ),
            width=12
        ),

    ),

])

# Callback to update the DataTable based on selected position and TOI range
@app.callback(
    Output('all-players-data-table', 'data'),
    Input('position-dropdown', 'value'),
    Input('toi-slider', 'value')  # Updated slider input
)
def update_table(selected_position, toi_range):
    min_toi = toi_range[0]  # Get the selected TOI range (use [0] to get the minimum value)
    if selected_position == 'All':
        # Show all positions within the TOI range
        filtered_df = ranks_df2[(ranks_df2['TOI (mins)'] >= min_toi)]
    elif selected_position == 'Forwards':
        # Map "Forward" to "Center," "Left Wing," and "Right Wing" within the TOI range
        filtered_df = ranks_df2[(ranks_df2['Position'].isin(['Center', 'Left Wing', 'Right Wing'])) &
                                (ranks_df2['TOI (mins)'] >= min_toi)]
    else:
        filtered_df = ranks_df2[(ranks_df2['Position'] == selected_position) &
                                (ranks_df2['TOI (mins)'] >= min_toi)]
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
def update_player_stat_rings(player_name):
    stats = get_player_stats(player_name)

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
        if stats[column_name] > 50:
            color = '#7FDBFF'
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

@callback(
    Output(component_id='player-stats-1', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_stats(selected_player):
    stats = get_player_card(selected_player)
    return f'Age: {stats["age"]} • Team: {stats["team_name"]} • {stats["position"]} • Shoots: {stats["shoots"]}'

@callback(
    Output(component_id='player-name', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_name(selected_player):
    return selected_player

@callback(
    Output(component_id='rink', component_property='figure'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def plot_rink(player_name):
    fig = plot_comparisons(player_name)
    return fig

@callback(
    Output(component_id='player-image', component_property='src'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_headshot(player_name):
    stats = get_player_card(player_name)
    return get_player_headshot(stats['id'])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
