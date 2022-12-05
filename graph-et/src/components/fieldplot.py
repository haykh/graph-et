import random
import dash
from typing import List
import plotly.express as px


class FieldPlot:
    def __init__(self, simulations: List[str]) -> None:
        self._id = f"{random.getrandbits(64):x}"
        plot_remove = dash.html.Button(
            "❌ close",
            className="plot-remove",
            id={"index": self._id, "type": "plot-remove"},
        )
        plot_sim_dropdown = dash.dcc.Dropdown(
            simulations,
            simulations[0] if len(simulations) > 0 else None,
            id={"index": self._id, "type": "plot-sim-dropdown"},
            searchable=False,
        )
        plot_field_dropdown = dash.dcc.Dropdown(
            [],
            id={"index": self._id, "type": "plot-field-dropdown"},
            searchable=False,
        )
        fig = px.imshow([[0]], aspect="equal", origin="lower")
        fig.update_layout(uirevision="constant")
        plot_graph = dash.dcc.Graph(
            figure=fig,
            id={"index": self._id, "type": "plot-field-graph"},
            className="graph",
            config={"displaylogo": False},
        )
        plot_indicator = dash.html.Div(
            "", id={"index": self._id, "type": "plot-loadedQ"}
        )

        self._view = dash.html.Div(
            [
                plot_remove,
                plot_sim_dropdown,
                plot_field_dropdown,
                plot_graph,
                plot_indicator,
            ],
            id=f"field-plot-{self._id}",
        )

    @property
    def view(self):
        return self._view

    @property
    def id(self):
        return self._id
