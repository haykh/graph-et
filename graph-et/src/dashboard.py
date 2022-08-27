from .defs import *
from typeguard import typechecked
from typing import List
import dash

from .components.configs import Configs
from .components.plots import Plots

@typechecked
class Dashboard:
    def __init__(self) -> None:
        self.simulations = {}
        self.app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True)
        
        self.app.layout = dash.html.Div([
            dash.dcc.Tabs(id="tabs-container", value="tab-plot", children=[
                dash.dcc.Tab(label="Configure ⚙️", value="tab-config"),
                dash.dcc.Tab(label="Plot fields 📈", value="tab-plot"),
            ]),
            dash.html.Div(id="tabs-content")
        ])
        self.configs = Configs(app=self.app, simulations=self.simulations)
        self.plots = Plots(app=self.app, simulations=self.simulations)

        # ------------------------------- tab switching ------------------------------ #
        @self.app.callback(
            dash.Output("tabs-content", "children"),
            dash.Input("tabs-container", "value")
        )
        def render_tabs(tab: str) -> List:
            if tab == "tab-config":
                return self.configs.view
            elif tab == "tab-plot":
                return self.plots.view

    def deploy(self, debug: bool = False, port: int = 8050) -> None:
        self.app.run_server(debug=debug, port=port)
