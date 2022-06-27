from typeguard import typechecked
from typing import List
import dash

from .defs import *
from .sim import Simulation

# !TODO:
#  1. progress bar
#  2. remove button for sim
#  3. load and aggregate indicators
#  4. memory tracker for simulation

@typechecked
def simulationItem(name: str, path: str, loadedQ: bool) -> dash.html.P:
    return dash.html.P(name + " : " + path, className="sim-label")

@typechecked
class Plotter:
    def __init__(self) -> None:
        self.simulations = {}
        self.app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True)
        # self.app.config.
        self.app.layout = dash.html.Div([
            dash.dcc.Tabs(id='tabs-container', value='tab-config', children=[
                dash.dcc.Tab(label='Configure ⚙️', value='tab-config'),
                dash.dcc.Tab(label='Plot fields 📈', value='tab-plot'),
            ]),
            dash.html.Div(id='tabs-content')
        ])
        self.config_tab = [
            dash.dcc.Input(
                id="input_sim_name",
                type="text",
                placeholder="Simulation name",
                debounce=True,
            ),
            dash.dcc.Input(
                id="input_sim_path",
                type="text",
                placeholder="Simulation path",
                debounce=True,
                required=True,
            ),
            dash.html.Button(
                "Add",
                id="button_sim_path"
            ),
            dash.html.Div(
                children=[],
                id="simulation_list"
            ),

            # dash.dcc.Upload(dash.html.Button('Add a simulation'))
            # path input
            # name input
            # step range input
        ]
        self.plot_tab = [
            dash.html.H1("dada")
        ]

        # # - - - tab switching - - - # #
        @self.app.callback(
            dash.dependencies.Output('tabs-content', 'children'),
            dash.dependencies.Input('tabs-container', 'value')
        )
        def render_tabs(tab: str) -> list:
            if tab == 'tab-config':
                return self.config_tab
            elif tab == 'tab-plot':
                return self.plot_tab

        # # - - - add simulation - - - # #
        @self.app.callback(
            dash.dependencies.Output('simulation_list', 'children'),
            [
                dash.dependencies.Input('button_sim_path', 'n_clicks'),
                dash.dependencies.Input('input_sim_name', 'value'),
                dash.dependencies.Input('input_sim_path', 'value')
            ],
            dash.dependencies.State('simulation_list', 'children')
        )
        def add_sim(n_clicks: int, name: str, path: str, children) -> str:
            name = (name if (name is not None and name != "") else f"SIM_{len(self.simulations)}")
            if (path is not None):
                self.addSimulation(name, path, [10])
            children = [simulationItem(name, s.path, False) for name, s in self.simulations.items()]
            return children

    def addSimulation(self, name: str, path: str, tsteps: List[int]) -> None:
        self.simulations[name] = Simulation(
            name, path, ['ex'], lambda f, x: None, tsteps)

        # def __init__(self, name: str,
        #              fields: List[str],
        #              loadFields: LoadField,
        #              tsteps: List[int] = [0],
        #              params: Dict[str, Any] = {}) -> None:
        # self.simulations[name] = Simulation(path, name, tsteps)

    def deploy(self, debug: bool = False, port: int = 8050) -> None:
        self.app.run_server(debug=debug, port=port)
