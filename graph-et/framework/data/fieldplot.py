import random
import dash
from typing import List, Dict
from typeguard import typechecked

from ..data.sim import Simulation


@typechecked
class FieldPlot:
    def __init__(self, simulations: Dict[str, Simulation]) -> None:
        self._id = f"{random.getrandbits(64):x}"
        plot_remove = dash.html.Button("❌ close", className="plot-remove",
                                       id={"index": self._id, "type": "plot-remove"})
        plot_plot = dash.html.Div(style={"width": "100px", "height": "100px", "backgroundColor": "white"},
                                  id={"index": self._id, "type": "plot-view"},
                                  className="plot-view")
        plot_indicator = dash.html.Div("",
                                       id={"index": self._id, "type": "plot-loadedQ"})
        self._view = dash.html.Div([
            plot_remove,
            plot_plot,
            plot_indicator
        ], id=f"field-plot-{self._id}")

    @property
    def view(self):
        return self._view

    @property
    def id(self):
        return self._id
