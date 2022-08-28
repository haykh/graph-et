import dash
from typing import List, Dict, Union, Any
from typeguard import typechecked

from ..data.sim import Simulation
from ..data.fieldplot import FieldPlot


@typechecked
class Plots:
    def __init__(self, app, simulations: Dict[str, Simulation]) -> None:
        self._plots = {}
        self._view = [
            dash.html.Div([
                dash.html.Button("➕ add field plot",
                                 id="plot-add-flds"),
            ], id="plot-controls"),
            dash.html.Div([], id="plot-plots")
        ]

        # --------------------------------- add plot --------------------------------- #
        @app.callback(
            dash.Output(
                "plot-plots",
                "children"
            ),
            [
                dash.Input(
                    "plot-add-flds",
                    "n_clicks"
                ),
            ],
            [
                dash.Input(
                    {"type": "plot-loadedQ", "index": dash.ALL},
                    "children"
                ),
            ]
        )
        def add_field_plot(n: int, _: str) -> List:
            if (dash.ctx.triggered_id == "plot-add-flds"):
                newplot = FieldPlot(app, simulations)
                self._plots[newplot.id] = newplot
            return [p.view for _, p in self._plots.items()]

        # -------------------------------- remove plot ------------------------------- #
        @app.callback(
            dash.Output(
                {"index": dash.MATCH, "type": "plot-loadedQ"},
                "children"
            ),
            [
                dash.Input(
                    {"index": dash.MATCH, "type": "plot-remove"},
                    "n_clicks"
                ),
                dash.State(
                    {"index": dash.MATCH, "type": "plot-remove"},
                    "id"
                ),
            ],
            dash.State(
                {"index": dash.MATCH, "type": "plot-loadedQ"},
                "children"
            ),
        )
        def add_field_plot(n: int, id: str, loaded_txt: str) -> List:
            if n is not None:
                if id["index"] in self._plots:
                    self._plots.pop(id["index"])
                    return loaded_txt + "-remove"
            return loaded_txt

        # --------------------------- change field dropdown -------------------------- #
        @app.callback(
            dash.Output(
                {"index": dash.MATCH, "type": "plot-toolbar-top"},
                "children"
            ),
            dash.Input(
                {"index": dash.MATCH, "type": "plot-sim-dropdown"},
                "value"
            ),
        )
        def update_field_dropdown(v: str):
            if v is not None:
                sim = simulations[v]
                snapshot = sim.snapshots[sim.tsteps[0]]
                print(snapshot.fkeys)
                return dash.dcc.Dropdown(
                    list(snapshot.fkeys), list(snapshot.fkeys)[0],
                    id="field-dropdown",
                    searchable=False,
                )
            else:
                return dash.html.Div("")

    @property
    def view(self) -> List:
        return self._view
