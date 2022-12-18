from .defs import *
import dash

from .components.configs import Configs
from .components.plots import Plots


class Dashboard:
    def __init__(self) -> None:
        self.simulations = {}
        self.state = {"plots": {}, "timestep": None}
        self.app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
        )
        self.config_container = Configs(app=self.app, simulations=self.simulations)
        self.plot_container = Plots(
            app=self.app,
            simulations=self.simulations,
            state=self.state,
        )
        self.app.layout = dash.html.Div(
            [
                dash.html.Div(self.config_container.view),
                dash.html.Div(self.plot_container.view),
            ]
        )

    def deploy(self, debug: bool = False, port: int = 8050) -> None:
        self.app.run_server(debug=debug, port=port)
