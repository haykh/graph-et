import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from typing import List, Dict

from ..data.sim import Simulation
from .fieldplot import FieldPlot


class Plots:
    def __init__(self, app, simulations: Dict[str, Simulation]) -> None:
        self._plots = {}
        step_badge = dash.html.P("timesteps", className="float-end")
        step_slider = dash.dcc.Slider(
            0,
            1,
            1,
            value=0,
            id="plot-timestep",
            updatemode="drag",
        )
        self._view = [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button("➕ field plot", color="light", id="plot-add-flds"),
                        width=12,
                    ),
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(step_badge, width=1),
                                dbc.Col(step_slider, width=11),
                            ],
                            id="plot-timestep-row",
                        ),
                        width=12,
                        className="p-4",
                        align="center",
                    ),
                ],
                id="plot-controls",
            ),
            dash.html.Div([], id="plot-plots"),
        ]

        # --------------------------------- add plot --------------------------------- #
        @app.callback(
            dash.Output("plot-plots", "children"),
            [
                dash.Input("plot-add-flds", "n_clicks"),
            ],
            [
                dash.Input({"type": "plot-loadedQ", "index": dash.ALL}, "children"),
            ],
            dash.State("plot-plots", "children"),
        )
        def add_field_plot(_1: int, _2: str, plots: List) -> List:
            if dash.ctx.triggered_id == "plot-add-flds":
                newplot = FieldPlot(list(simulations.keys()))
                self._plots[newplot.id] = newplot
                return plots + [newplot.view]
            elif dash.ctx.triggered_id and (
                dash.ctx.triggered_id.get("type", None) == "plot-loadedQ"
            ):
                return [
                    p
                    for p in plots
                    if p["props"]["id"].split("-")[-1] != dash.ctx.triggered_id["index"]
                ]
            return plots

        # -------------------------------- remove plot ------------------------------- #
        @app.callback(
            dash.Output({"index": dash.MATCH, "type": "plot-loadedQ"}, "children"),
            [
                dash.Input({"index": dash.MATCH, "type": "plot-remove"}, "n_clicks"),
                dash.State({"index": dash.MATCH, "type": "plot-remove"}, "id"),
            ],
            dash.State({"index": dash.MATCH, "type": "plot-loadedQ"}, "children"),
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
                {"index": dash.MATCH, "type": "plot-field-dropdown"}, "options"
            ),
            dash.Input({"index": dash.MATCH, "type": "plot-sim-dropdown"}, "value"),
        )
        def update_field_dropdown(sim: str) -> List[str]:
            if sim is not None:
                return simulations[sim].field_keys
            else:
                return []

        # -------------------------------- plot field -------------------------------- #
        @app.callback(
            dash.Output({"index": dash.MATCH, "type": "plot-field-graph"}, "figure"),
            [
                dash.Input({"index": dash.MATCH, "type": "plot-sim-dropdown"}, "value"),
                dash.Input(
                    {"index": dash.MATCH, "type": "plot-field-dropdown"}, "value"
                ),
                dash.Input("plot-timestep", "value"),
                # !TODO: adjust aggregation based on zoom level
                dash.Input(
                    {"index": dash.MATCH, "type": "plot-field-graph"}, "relayoutData"
                ),
            ],
            dash.State({"index": dash.MATCH, "type": "plot-field-graph"}, "figure"),
        )
        def set_fieldplot(sim: str, field: str, tstep: int, rel, fig: go.Figure):
            if sim != None and field != None and tstep != None:
                selected_sim = simulations[sim]
                time = selected_sim.tsteps[tstep]
                selected_sim.aggregate(time, 50, 50)
                agg_data = selected_sim.getAggregatedField(time, field)
                fig["data"][0]["z"] = agg_data.values
                fig["data"][0]["x"] = agg_data.coords["x"].values
                fig["data"][0]["y"] = agg_data.coords["y"].values
                return fig
            else:
                return fig

    @property
    def view(self) -> List:
        return self._view
