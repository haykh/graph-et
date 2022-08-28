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
        
        self.configs = Configs(app=self.app, simulations=self.simulations)
        self.plots = Plots(app=self.app, simulations=self.simulations)
        self.app.layout = dash.html.Div([dash.html.Div(self.configs.view), dash.html.Div(self.plots.view)])

    def deploy(self, debug: bool = False, port: int = 8050) -> None:
        self.app.run_server(debug=debug, port=port)