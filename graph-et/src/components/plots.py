import random
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.colors as pc

from typing import List, Dict, Any

from ..data.sim import Simulation
from .fieldplot import FieldPlot


def isValidState(id, state):
    if id is None:
        return False
    return (
        (state["plots"][id]["sim"] is not None)
        and (state["plots"][id]["field"] is not None)
        and (state["plots"][id]["colormap"] is not None)
    )


class Plots:
    def __init__(
        self,
        app,
        simulations: Dict[str, "Simulation"],
        state: Dict[str, Any],
    ) -> None:
        step_badge = dash.html.P("timesteps", className="float-end")
        step_slider = dash.dcc.Slider(
            0,
            1,
            1,
            value=state.get("timestep", 0),
            id="plot-timestep",
            updatemode="drag",
        )
        self.plots = {}
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
            dbc.Row([], id="plot-plots"),
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
        def add_field_plot(_1: int, _2: str, allplots: List) -> List:
            if dash.ctx.triggered_id == "plot-add-flds":
                newid = f"{random.getrandbits(64):x}"
                state["plots"][newid] = {}
                newplot = FieldPlot(simulations, newid, state["plots"][newid])
                self.plots[newid] = newplot
                print ("TRIGGERED: add_field_plot (newplot)")
                return allplots + [newplot.view]
            elif dash.ctx.triggered_id and (
                dash.ctx.triggered_id.get("type", None) == "plot-loadedQ"
            ):
                print ("TRIGGERED: add_field_plot (plot-loadedQ)")
                return [
                    p
                    for p in allplots
                    if p["props"]["id"].split("-")[-1] != dash.ctx.triggered_id["index"]
                ]
            print ("TRIGGERED: add_field_plot (general)", self.plots)
            return [p.view for i, p in self.plots.items()]

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
                if id["index"] in self.plots:
                    self.plots.pop(id["index"])
                    state["plots"].pop(id["index"])
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
                return [{"label": f, "value": f} for f in simulations[sim].field_keys]
            else:
                return []

        # # ------------------------------ change timestep ----------------------------- #
        # @app.callback(
        #     dash.Output({"index": dash.ALL, "type": "plot-field-graph"}, "figure"),
        #     [
        #         dash.Input("plot-timestep", "value"),
        #     ],
        #     dash.State({"index": dash.ALL, "type": "plot-field-graph"}, "figure")
        # )
        # def set_timestep(tstep: int, figs: List[go.Figure]) -> List[go.Figure]:
        #     state["timestep"] = tstep
        #     return [self.RedrawFigure(id, state, simulations, fig) for id, fig in figs]

        # ------------------------------ change one plot ----------------------------- #
        @app.callback(
            dash.Output({"index": dash.MATCH, "type": "plot-field-graph"}, "figure"),
            [
                dash.Input({"index": dash.MATCH, "type": "plot-sim-dropdown"}, "value"),
                dash.Input(
                    {"index": dash.MATCH, "type": "plot-field-dropdown"}, "value"
                ),
                dash.Input({"index": dash.MATCH, "type": "plot-colormap"}, "value"),
                # !TODO: adjust aggregation based on zoom level
                # dash.Input(
                #     {"index": dash.MATCH, "type": "plot-field-graph"}, "relayoutData"
                # ),
                dash.Input("plot-timestep", "value"),
            ],
            dash.State({"index": dash.MATCH, "type": "plot-field-graph"}, "figure"),
        )
        def set_fieldplot(
            sim: str, field: str, colormap: str, tstep: int, fig: go.Figure
        ):
            if dash.ctx.triggered_id == "plot-timestep":
                state["timestep"] = tstep
            elif (dash.ctx.triggered_id is not None) and (
                dash.ctx.triggered_id.get("type", None) is not None
            ):
                self.SavePlotState(
                    dash.ctx.triggered_id,
                    state=state,
                    sim=sim,
                    field=field,
                    colormap=colormap,
                )
            if state["timestep"] is not None:
                index = dash.ctx.args_grouping[0]["id"]["index"]
                if isValidState(index, state):
                    return self.RedrawFigure(index, state, simulations, fig)
            return fig

    @property
    def view(self) -> List:
        return self._view

    def SavePlotState(self, id, state, **kwargs):
        if (id is not None) and (id.get("index", None) is not None):
            id = id["index"]
            state["plots"][id] = {k: v for k, v in kwargs.items()}

    def RedrawFigure(self, id, state, simulations, fig):
        tstep = state["timestep"]
        colormap = state["plots"][id]["colormap"]
        selected_sim = simulations[state["plots"][id]["sim"]]
        selected_field = state["plots"][id]["field"]
        time = selected_sim.tsteps[tstep]
        selected_sim.aggregate(time, 50, 50)
        agg_data = selected_sim.getAggregatedField(time, selected_field)
        fig["data"][0]["z"] = agg_data.values
        fig["data"][0]["x"] = agg_data.coords["x"].values
        fig["data"][0]["y"] = agg_data.coords["y"].values
        fig["layout"]["coloraxis"]["colorscale"] = pc.get_colorscale(colormap)
        return fig
