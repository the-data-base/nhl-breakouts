# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
#import plotly.graph_objects as go
from datetime import date, datetime

# Read data
def read_data(file_path):
    return pd.read_csv(file_path, delimiter=',')

# Create player-specific DataFrame
def create_player_df(dataframe, player_name):
    player_df = dataframe[dataframe['player_name'] == player_name]
    cols = ['player_name', 'primary_position_type', 'game_type', 'EV XG', 'EV Offense', 'EV Defense', 'Finishing', 'Gx60', 'A1x60', 'PP', 'PK', 'Penalty']
    return player_df[cols], player_df

# Create a card with given title and value
def create_card(title, value):
    return dbc.Card(
        dbc.CardBody([
            html.H2(value, className="text-nowrap"),
            html.H4(title, className="text-nowrap")
        ]),
        className="col-auto text-center m-2 p-2")

# Calcualte age
def calculate_age(born):
    born_dt = datetime.strptime(born, "%Y-%m-%d")
    today = date.today()
    return today.year - born_dt.year - ((today.month, today.day) < (born_dt.month, born_dt.day))

# Set colors
colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'title': '#ffffff'
}

# Initialize the app
#app = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])  # Use the DARKLY theme for dark mode

# Read data and create the initial DataFrame
ranks_df = read_data('.output/bq_results/202202_player_ranks.csv')
shots_df = read_data('.output/bq_results/202202_player_shots.csv')

# Initial player selection
initial_player_name = 'Connor McDavid'
mcdavid_df, mcdavid_df_all = create_player_df(ranks_df, initial_player_name)

# Define app layout
app.layout = html.Div([
    dbc.Navbar(
        dbc.Container([
            html.Img(src='assets/avatar.jpg', height="40px"),  # Add this line to insert the image
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
        html.Img
            (src='assets/player_img.png',
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
                children='Connor McDavid',
                style={
                    'textAlign': 'center',
                    'color': colors['title'],
                    'display': 'inline',
                    'font-weight': 'bold',  # Make the font bold
                    'margin-left': '20px',  # Add margin to the right for spacing
                }
            ),
            html.H6(
                children = f'Age: {calculate_age(mcdavid_df_all["birth_date"].values[0])} | Country: {mcdavid_df_all["nationality"].values[0]} | Position: {mcdavid_df_all["primary_position_name"].values[0]} | Shoots: {mcdavid_df_all["shoots_catches"].values[0]}',
                style={
                    'textAlign': 'center',
                    'color': colors['text'],
                    'margin-left': '20px',  # Add margin to the right for spacing
                }
            ),
        ]),
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),

    html.Br(),

    # Cards for player-specific metrics
    html.Div(dbc.Container(
        html.Div([
            dbc.Row([
                create_card("EV XG", mcdavid_df['EV XG'].round(2)),
                create_card("EV Offense", mcdavid_df['EV Offense'].round(2)),
                create_card("EV Defense", mcdavid_df['EV Defense'].round(2)),
                create_card("Finishing", mcdavid_df['Finishing'].round(2)),
                create_card("Gx60", mcdavid_df['Gx60'].round(2)),
                create_card("A1x60", mcdavid_df['A1x60'].round(2)),
                create_card("PP", mcdavid_df['PP'].round(2)),
                create_card("PK", mcdavid_df['PK'].round(2)),
                create_card("Penalty", mcdavid_df['Penalty'].round(2))
            ],
            className="cards justify-content-center"
            ),
        ])
    )),

    html.Br(),

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

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
