import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
from glob import glob


external_stylesheets = [dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

####################
# global variables #
####################
extension = {'EPOCH':'sdf'}
var_list = []
files_list = []

###########################
# controls initialisation #
###########################
controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label(
                    "Simulation code",
                    style={'font-weight': 'bold'}
                ),
                dcc.Dropdown(
                    id='simulation',
                    options=[{'label': 'EPOCH', 'value': 'EPOCH'}],
                    value='EPOCH'
                ),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label(
                    "Path name",
                    style={'font-weight': 'bold'}
                ),
                dbc.Input(
                    id='pathname',
                    type='text',
                    placeholder='Input path name',
                    style={'width':'100%'}
                ),
                dbc.Button(
                    'Submit',
                    id='submit',
                    size='sm',
                    n_clicks=0,
                    style={'marginTop': '2px'}
                ),

            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label(
                    "Files",
                    style={'font-weight': 'bold'}
                ),
                dcc.Dropdown(
                    id='files',
                    value = -1
                ),
                dbc.Button(
                    '<',
                    id='file_previous',
                    n_clicks=0,
                    size='sm',
                    style={'marginTop': '2px', 'marginRight': '2px'}
                ),
                dbc.Button(
                    'Select',
                    id='file_select',
                    n_clicks=0,
                    size='sm',
                    style={'marginTop': '2px', 'marginRight': '2px'}
                ),
                dbc.Button(
                    '>',
                    id='file_next',
                    n_clicks=0,
                    size='sm',
                    style={'marginTop': '2px'}
                ),
            ]
        ),

        dbc.FormGroup(
            [
                dbc.Label(
                    "Variable",
                    style={'font-weight': 'bold'}
                ),
                dcc.Dropdown(
                id='variable',
                options=[{'label': 'Select variable', 'value': -1}],
                value=-1,
                ),
            ]
        ),
    ],
    body=True,
)

################################
# Initialisation of the figure #
################################
#fig = px.scatter()

##########
#        #
#  main  #
# Layout #
#        #
##########
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(controls, md=2),
                dbc.Col(
                    dcc.Graph(
                        id='main_fig',
                        config=dict(responsive=True),
                        style={'height': '100%'}
                    ),
                    md=10
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [html.Div(id='info')]
        )
    ],
    fluid=True,
)


#####################
# Callback function #
#####################
@app.callback(Output('files', 'options'),
              [Input('submit', 'n_clicks')],
              [State('simulation', 'value'),
               State('pathname', 'value')]
)
def update_files_list(clicks, simulation, path_name):
    global files_list

    if path_name is not None:
        only_files = [f for f in sorted(glob(f'{path_name}/*.{extension[simulation]}'))]
        files_list = [{'label': f.split('/')[-1], 'value': f} for f in only_files]
        return files_list
    else:
        return [{'label': 'No files', 'value': -1}]


@app.callback(Output('files', 'value'),
              Input('file_previous', 'n_clicks'),
              Input('file_next', 'n_clicks'),
              State('files', 'value')
)
def update_file(clicks_prev, clicks_next, current_file):
    global files_list
    ctx = dash.callback_context
    
    if not ctx.triggered or current_file == -1:
        return -1
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        values_list = [elem['value'] for elem in files_list]
        index = values_list.index(current_file)
    
    if button_id == 'file_previous':
        new_file = values_list[index-1] if index>0 else current_file
    elif button_id == 'file_next':
        new_file = values_list[index+1] if index<len(values_list)-1 else current_file
    return new_file


@app.callback(Output('variable', 'options'),
              Input('file_select', 'n_clicks'),
              State('files', 'value'),
              State('simulation', 'value')
)
def get_plot_variables(clicks, file_, simulation):
    if file_!=-1 and simulation=='EPOCH':
        import sdf_helper as sh
        global var_list
        file_content = sh.getdata(file_)
        var_to_check = ('Electric', 'Derived')
        var_list = [key for key in vars(file_content).keys() if key.startswith(var_to_check)]
        options = [{'label': var, 'value': var} for var in var_list]
        return options

    else:
        return [{'label': 'No variables', 'value': -1}]


@app.callback(Output('main_fig', 'figure'),
              Input('files', 'value'),
               Input('variable', 'value'),
              State('simulation', 'value')
)
def update_graph(file_, variable, simulation):
    if variable!=-1 and simulation=='EPOCH':
        import sdf_helper as sh
        # get data to plot and snapshot time
        file_content = sh.getdata(file_)
        space_var = file_content.Grid_Grid_mid.data
        exec( f'data = file_content.{variable}.data', locals(), globals() )
        time = file_content.Header['time'] * 1e12  # result in ps
        
        if len(space_var) == 1:  # 1d data --> line plot
            x = space_var[0]
            fig = px.line(x=x, y=data, title=f'time: {time:.3f} ps')
        
    else:
        fig = px.line()
    fig.update_layout(width=1200, height=800, transition_duration=500)
    return fig




if __name__ == '__main__':
    app.run_server(debug=True)