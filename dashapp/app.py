# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
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

# Create a card with given title and value
def create_card(title):
    card = dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.H2("Default", className="text-nowrap", id=f"{title.lower().replace(' ', '-')}-card-value"),
                html.H4(title, className="text-nowrap", id=f"{title.lower().replace(' ', '-')}-card-title"),
            ])
        )
    , width = 2)
    return card

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
        'shoots': player_df['shoots_catches'].values[0]
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
        'penalty': player_df['Penalty'].values[0]
    }
    # round to 2 decimal places
    for key, value in stats.items():
        stats[key] = round(value, 2)

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

# Initialize the app
#app = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])  # Use the DARKLY theme for dark mode



# Player stat cards
cards = html.Div([
    dbc.Row([
        create_card("EV XG"),
        create_card("EV Offense"),
        create_card("EV Defense"),
        create_card("Finishing"),
        create_card("Gx60"),

    ],
    className="cards justify-content-center",
    ),
    dbc.Row([
        create_card("A1x60"),
        create_card("PP"),
        create_card("PK"),
        create_card("Penalty"),
    ],
    className="cards justify-content-center",
    ),
])

# Define app layout
app.layout = html.Div([
    dbc.Navbar(
        dbc.Container([
            html.Img(src='images/avatar.jpg', height="40px"),  # Add this line to insert the image
            dbc.NavbarBrand("NHL App", href="/"),
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink("Home", href="/")),
                    dbc.NavItem(dbc.NavLink("About", href="/about")),
                ],
                navbar=True,
            ),
        ]),
        color="dark",
        dark=True,
    ),

    html.Br(),

   # Create a div for the header with an image, player name, and subtitles
    html.Div([
        html.Img(
            id='player-image',
            height="200px",
            style={
                'margin-right': '10x',
                'border-radius': '50%',  # Apply circular border
                'border': '5px solid #000000',  # Border color
                #'box-shadow': '0px 0px 8px 0px #000000'  # Add shadow effect
            }
        ),
        html.Div([
            html.H1(
                id='player-name',
                style={
                    'textAlign': 'center',
                    'color': colors['title'],
                    'display': 'inline',
                    'font-weight': 'bold',  # Make the font bold
                    'margin-left': '20px',  # Add margin to the right for spacing
                }
            ),
            html.H6(
                id='player-stats',
                style={
                    'textAlign': 'center',
                    'color': colors['text'],
                    'margin-left': '20px',  # Add margin to the right for spacing
                }
            ),
        ]),
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),

    html.Br(),

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
            width='4'
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
            width='4'
        ), # column
    ], justify='center'), # row

    # Cards for player-specific metrics
    html.Div(dbc.Container(
        cards
    )),

    html.Br(),

    dbc.Row([
        # Plot for the ice rink
        dbc.Col(
            html.Div([
                dcc.Graph(
                    figure={},
                    id='rink',
                    style={'height': '650px'}
                ),
            ]),
            width=6
        ),

        dbc.Col(
            html.Div([
                dcc.RadioItems(
                    options=[
                        {'label': metric, 'value': metric} for metric in ['EV XG', 'EV Offense', 'EV Defense', 'Finishing']
                    ],
                    value='EV XG',
                    inline=True,
                    id='rank-metric-radio',
                    labelStyle={'display': 'block', 'padding-right': '20px'}  # Add padding between radio options
                ),
                dcc.Graph(
                    figure={},
                    id='metric-bar-chart',
                    style={'height': '650px'}
                ),
            ]),
            width=6
        ),
    ]),

    # A new row that contains the scatterplot from plot_rink
    dbc.Row([
        dbc.Col(
            dash_table.DataTable(
                id='all-players-data-table',
                data=ranks_df.to_dict('records'),
                page_size=20,
                style_table={
                    'overflowX': 'auto'},
                style_header={
                        'backgroundColor': '#343a40',  # Dark background color for headers
                        'color': 'white',  # Text color for headers
                    },
                style_cell={
                        'backgroundColor': '#343a40',  # Dark background color for cells
                        'color': 'white',  # Text color for cells
                        'textAlign': 'center',
                    },
                style_data_conditional=[
                    {
                    'if': {'row_index': 'odd'},  # Style for odd rows
                    'backgroundColor': '#444d56',  # Darker background color
                        },]
            ),
            width=12
        ),
    ]),

])

# Callback to update the metric bar chart
@app.callback(
    Output(component_id='metric-bar-chart', component_property='figure'),
    Input(component_id='rank-metric-radio', component_property='value'),
)
def update_fig(metric):
    forwards = ranks_df[ranks_df['primary_position_type'] == 'Forward']
    fig = px.bar(
        forwards.sort_values(by=metric, ascending=False),
        x='player_name',
        y=metric,
        color="primary_position_name",
        barmode='stack'
    )

    # Dark mode-friendly color scheme
    fig.update_layout(
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Set plot background color to transparent
        paper_bgcolor='rgba(0, 0, 0, 0.6)',  # Set paper background color for dark mode
        font=dict(color=colors['text']),  # Set text color
        xaxis=dict(linecolor=colors['text']),  # Set x-axis line color
        yaxis=dict(linecolor=colors['text']),  # Set y-axis line color
        xaxis_title="Players",
        yaxis_title=metric,
        title_text=f"Metric: {metric}",
        title_font=dict(color=colors['title'], size=16),  # Set title text color and size
    )

    return fig

@callback(
    Output(component_id='ev-xg-card-value', component_property='children'),
    Output(component_id='ev-offense-card-value', component_property='children'),
    Output(component_id='ev-defense-card-value', component_property='children'),
    Output(component_id='finishing-card-value', component_property='children'),
    Output(component_id='gx60-card-value', component_property='children'),
    Output(component_id='a1x60-card-value', component_property='children'),
    Output(component_id='pp-card-value', component_property='children'),
    Output(component_id='pk-card-value', component_property='children'),
    Output(component_id='penalty-card-value', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_cards(player_name):
    stats = get_player_stats(player_name)

    # return each stat as separate values
    return stats['ev_xg'], stats['ev_offense'], stats['ev_defense'], stats['finishing'], stats['gx60'], stats['a1x60'], stats['pp'], stats['pk'], stats['penalty']

@callback(
    Output(component_id='player-stats', component_property='children'),
    Input(component_id='player-name-dropdown', component_property='value')
)
def set_player_stats(selected_player):
    stats = get_player_card(selected_player)
    return f'Age: {stats["age"]} | Country: {stats["country"]} | Position: {stats["position"]} | Shoots: {stats["shoots"]} | ID: {stats["id"]}'

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
