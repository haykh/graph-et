from typeguard import typechecked
from typing import List, Union
import dash

FnameTemplate = Union[str, None]

from .defs import *
from .sim import Simulation

# !TODO:
#  1. progress bar
#  2. remove button for sim
#  3. load and aggregate indicators
#  4. memory tracker for simulation


@typechecked
def simulationItem(name: str, path: str, loadedQ: bool) -> dash.html.Div:
    return dash.html.Div(children=[
        dash.html.P(name + " : " + path, className="sim-label"),
        dash.html.Span(children="Loaded: " + str(loadedQ),
                       className="sim-loaded"),
        dash.html.Button("x", id="sim-remove-" + name)
    ])


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
            dash.html.Div(id='add-simulation-form', children=[
                dash.dcc.Input(
                    id="input-sim-name",
                    type="text",
                    placeholder="Simulation name",
                    debounce=True,
                ),
                dash.dcc.Input(
                    id="input-sim-path",
                    type="text",
                    placeholder="Simulation path",
                    debounce=True,
                    required=True,
                ),
                dash.html.Button(
                    "Add",
                    id="button-sim-path"
                ),
                dash.dcc.Checklist(
                    ["Fields", "Particles"],
                    ["Fields"],
                    id="check-load-vals"
                ),
                dash.dcc.Input(
                    id="input-flds-file",
                    type="text",
                    placeholder="flds.tot.%05d",
                    debounce=True,
                ),
                dash.dcc.Input(
                    id="input-prtl-file",
                    type="text",
                    placeholder="prtl.tot.%05d",
                    debounce=True,
                ),
            ]),
            dash.html.Div(
                children=[],
                id="simulation-list"
            ),
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
            dash.dependencies.Output('simulation-list', 'children'),
            [
                dash.dependencies.Input('button-sim-path', 'n_clicks'),
                dash.dependencies.Input('input-sim-name', 'value'),
                dash.dependencies.Input('input-sim-path', 'value'),
                dash.dependencies.Input('check-load-vals', 'value'),
                dash.dependencies.Input('input-flds-file', 'value'),
                dash.dependencies.Input('input-prtl-file', 'value'),
            ],
            dash.dependencies.State('simulation-list', 'children')
        )
        def add_sim(_: int,
                    name: str,
                    path: str,
                    load_vals: List[str],
                    flds_file: str,
                    prtl_file: str,
                    children: List) -> str:
            name = (name if (name is not None and name != "")
                    else f"SIM_{len(self.simulations)}")
            if (dash.ctx.triggered_id == 'button-sim-path'):
                if 'Fields' not in load_vals:
                    flds_file = None
                elif flds_file is None or flds_file == '':
                    flds_file = 'flds.tot.%05d'
                if 'Particles' not in load_vals:
                    prtl_file = None
                elif prtl_file is None or prtl_file == '':
                    prtl_file = 'prtl.tot.%05d'
                if ((path is not None) and (path != "")):
                    self.addSimulation(name, path, flds_file, prtl_file)
            children = [simulationItem(name, s.path, False)
                        for name, s in self.simulations.items()]
            return children
        
        @self.app.callback(
            dash.dependencies.Output('simulation-list', 'children'),
            dash.dependencies.Input('sim-remove-*', 'children'),
        )

    def addSimulation(self,
                      name: str,
                      path: str,
                      flds_file: FnameTemplate,
                      prtl_file: FnameTemplate) -> None:
        # TODO: warn if simulation is already in list
        # TODO: error handling here (missing files etc)
        self.simulations[name] = Simulation(name, path, flds_file, prtl_file)

    def deploy(self, debug: bool = False, port: int = 8050) -> None:
        self.app.run_server(debug=debug, port=port)
