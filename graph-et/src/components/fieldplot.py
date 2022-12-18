import dash
import dash_bootstrap_components as dbc
from typing import Dict, Any
import plotly.express as px

from ..data.sim import Simulation


class FieldPlot:
    def __init__(
        self, simulations: Dict[str, "Simulation"], id: str, state: Dict[str, Any]
    ) -> None:
        print (state)
        self._id = id
        simulation_names = list(simulations.keys())
        if state.get("sim", None) is None:
            state["sim"] = simulation_names[0] if len(simulation_names) > 0 else None
        if state["sim"] is not None:
            field_options = [
                {"label": f, "value": f} for f in simulations[state["sim"]].field_keys
            ]
        else:
            field_options = []
        if state.get("field", None) is None:
            state["field"] = (
                field_options[0]["value"] if len(field_options) > 0 else None
            )

        if state.get("colormap", None) is None:
            state["colormap"] = "viridis"

        selected_sim = state["sim"]
        selected_field_name = state["field"]
        selected_colormap = state["colormap"]
        plot_remove = dbc.Button(
            "❌",
            color="secondary",
            className="plot-remove float-end",
            id={"index": self._id, "type": "plot-remove"},
        )
        plot_sim_dropdown = dbc.Select(
            options=simulation_names,
            value=selected_sim,
            id={"index": self._id, "type": "plot-sim-dropdown"},
        )
        plot_field_dropdown = dbc.Select(
            options=field_options,
            value=selected_field_name,
            id={"index": self._id, "type": "plot-field-dropdown"},
        )
        fig = px.imshow(
            [[]],
            aspect="equal",
            origin="lower",
            color_continuous_scale=selected_colormap,
        )
        fig.update_layout(
            uirevision="constant",
            font_family="JetBrains Mono",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#ffffff",
            modebar_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, b=0, t=0, pad=0),
        )
        plot_graph = dash.dcc.Graph(
            figure=fig,
            id={"index": self._id, "type": "plot-field-graph"},
            className="graph",
            config={"displaylogo": False},
        )
        plot_colormap = dbc.Select(
            options=[{"label": c, "value": c} for c in px.colors.named_colorscales()],
            value=selected_colormap,
            id={"index": self._id, "type": "plot-colormap"},
        )
        plot_indicator = dash.html.Div(
            "", id={"index": self._id, "type": "plot-loadedQ"}
        )
        self._view = dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(plot_sim_dropdown),
                                dbc.Col(plot_field_dropdown),
                                dbc.Col(plot_remove),
                            ]
                        ),
                    ),
                    dbc.CardBody(plot_graph),
                    dbc.CardFooter([dash.html.Div(plot_colormap), plot_indicator]),
                ],
            ),
            lg=6,
            md=12,
            id=f"field-plot-{self._id}",
        )

    @property
    def view(self):
        return self._view

    @property
    def id(self):
        return self._id
