import random
import dash
from typing import List, Dict
from typeguard import typechecked

from ..data.sim import Simulation


@typechecked
class FieldPlot:
    def __init__(self, app, simulations: Dict[str, Simulation]) -> None:
        self._id = f"{random.getrandbits(64):x}"
        plot_remove = dash.html.Button("❌ close", className="plot-remove",
                                       id={"index": self._id, "type": "plot-remove"})
        # plot_plot = dash.html.Div(style={"width": "100px", "height": "100px", "backgroundColor": "white"},
        #                           id={"index": self._id, "type": "plot-view"},
        #                           className="plot-view")
        plot_indicator = dash.html.Div(
            "", id={"index": self._id, "type": "plot-loadedQ"})
        if len(simulations) > 0:
            sims = list(simulations.keys())
            sim_init = list(simulations.keys())[0]
        else:
            sims = []
            sim_init = None
        plot_sim_dropdown = dash.dcc.Dropdown(
            sims, sim_init,
            id={"index": self._id, "type": "plot-sim-dropdown"},
            searchable=False
        )

        # fieldDropdown = dash.dcc.Dropdown(
        #     list(data.data_vars), list(data.data_vars)[0],
        #     id="field-dropdown",
        #     searchable=False,
        # )

        plot = dash.dcc.Graph(id={"index": self._id, "type": "plot-fieldgraph"},
                              className='graph', config={'displaylogo': False})

        plot_toolbar_top = dash.html.Div([],
                                         id={"index": self._id,
                                             "type": "plot-toolbar-top"},
                                         className="plot-toolbar-top")

        self._view = dash.html.Div([
            plot_remove,
            plot_sim_dropdown,
            plot_toolbar_top,
            plot,
            plot_indicator
        ], id=f"field-plot-{self._id}")
        # @app.callback(
        #     dash.dependencies.Output('graph-container', 'children'),
        #     dash.dependencies.Input(fieldDropdown, 'value')
        # )
        # def update_graph(field):
        #     # ctx = dash.callback_context
        #     # if not ctx.triggered:
        #     # field = list(data.data_vars.keys())[0]
        #     # else:
        #     # field = ctx.triggered[0]['prop_id'].split('.')[0].split('-')[1]
        #     fig1 = px.imshow(data_agg[field],
        #                      aspect='equal', origin='lower')
        #     fig1.update_layout(layout)
        #     fig2 = px.imshow(data_agg[field],
        #                      aspect='equal', origin='lower')
        #     fig2.update_layout(layout)
        #     graphs = [dash.dcc.Graph(figure=fig1, id='graph-1', config={'displaylogo': False}),
        #               dash.dcc.Graph(figure=fig2, id='graph-2', config={'displaylogo': False})]
        #     return graphs
    @property
    def view(self):
        return self._view

    @property
    def id(self):
        return self._id
