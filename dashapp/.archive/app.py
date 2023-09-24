# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# Read data
def read_data(file_path):
    return pd.read_csv(file_path, delimiter=',')

# Create player-specific DataFrame
def create_player_df(dataframe, player_name):
    player_df = dataframe[dataframe['player_name'] == player_name]
    cols = ['player_name', 'primary_position_type', 'game_type', 'EV XG', 'EV Offense', 'EV Defense', 'Finishing', 'Gx60', 'A1x60', 'PP', 'PK', 'Penalty']
    return player_df[cols]

# Create a card with given title and value
def create_card(title, value):
    return dbc.Card(
        dbc.CardBody([
            html.H2(value, className="text-nowrap"),
            html.H4(title, className="text-nowrap")
        ]),
        #className="col-auto mb-3",
        className="col-auto text-center m-2 p-2"  # Adjust margin and padding

    )

colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'title': '#8B0000'
}

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])

# Read data and create the initial DataFrame
ranks_df = read_data('.output/bq_results/202202_player_ranks.csv')
shots_df = read_data('.output/bq_results/202202_player_shots.csv')

# Initial player selection
initial_player_name = 'Connor McDavid'
mcdavid_df = create_player_df(ranks_df, initial_player_name)

# Define app layout
app.layout = html.Div([
    html.Div(dcc.Markdown(children='## the-data-base: nhl-app'),
             style={'textAlign': 'center', 'color': colors['title']}),

    # Dropdowns for user input
    html.Div(style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'space-between'}, children=[
        html.Div(style={'flex': '1', 'padding': '15px'}, children=[
            html.Label('1. Choose Position Type'),
            dcc.Dropdown(
                options=[
                    {'label': 'Forward', 'value': 'Forward'},
                    {'label': 'Defenseman', 'value': 'Defenseman'},
                    {'label': 'Goalie', 'value': 'Goalie'}
                ],
                value='Forward',
                id='position-type-dropdown',
            ),
        ]),

        html.Div(style={'flex': '1', 'padding': '15px'}, children=[
            html.Label('2. Select Player(s)'),
            dcc.Dropdown(
                options=[{'label': name, 'value': name} for name in ranks_df['player_name']],
                value=[initial_player_name],
                multi=True,
                id='player-multi-select',
                style={'maxHeight': '50px', 'overflowY': 'auto'}  # Adjust maxHeight to a reasonable value
            ),
        ]),

        html.Div(style={'flex': '1', 'padding': '15px'}, children=[
            html.Label('3. Choose Metric to Visualize'),
            dcc.RadioItems(
                options=[
                    {'label': metric, 'value': metric} for metric in ['EV XG', 'EV Offense', 'EV Defense', 'Finishing', 'Gx60', 'A1x60', 'PP', 'PK', 'Penalty']
                ],
                value='EV XG',
                inline=True,
                id='rank-metric-radio'
            ),
        ]),
    ]),

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

    # Data table and metric bar chart
    html.Div(className='row', children=[
        html.Div(className='six columns', children=[
            dash_table.DataTable(
                id='all-players-data-table',
                data=ranks_df.to_dict('records'),
                page_size=20,
                style_table={'overflowX': 'auto'}
            )
        ]),
        html.Div(className='six columns', children=[
            dcc.Graph(
                figure={},
                id='metric-bar-chart',
                style={'height': '55vh'}
            )
        ])
    ])
])

# Callback to update the metric bar chart
@app.callback(
    Output(component_id='metric-bar-chart', component_property='figure'),
    Input(component_id='rank-metric-radio', component_property='value'),
    Input(component_id='player-multi-select', component_property='value'),
    Input(component_id='position-type-dropdown', component_property='value')
)
def update_fig(metric, players, position):
    selected_players_df = ranks_df[(ranks_df['primary_position_type'] == position) & ranks_df['player_name'].isin(players)]
    fig = px.bar(
        selected_players_df.sort_values(by=metric, ascending=False),
        x='player_name',
        y=metric,
        color="primary_position_type",
        barmode='stack'
    )
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
