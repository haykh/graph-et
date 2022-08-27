from src.dashboard import Dashboard

if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.deploy(debug=True)

# import numpy as np
# import xarray as xr
# import datashader as ds

# import plotly.graph_objects as go
# import plotly.express as px
# import plotly.io as pio

# import dash

# import objects.sim as sim

# pio.templates.default = 'plotly_dark'

# app = dash.Dash(__name__)

# loading = dash.dcc.Loading(
#     id="loading-data",
#     type="default",
#     children=dash.html.Div(id="loading-data-div")
# )
# button = dash.html.Button('Submit', id='load-data', n_clicks=0)
# app.layout = dash.html.Div([
#     button,
#     loading
# ])

# def example():
#     import time
#     time.sleep(5)
# try:
#     mysim = sim.Simulation("test", [
#         {"fld-ex1": example},
#     ])
# except Exception as e:
#     print(*e.args)


# @app.callback(
#     dash.Output("loading-data-div", "children"),
#     dash.Input('load-data', 'n_clicks')
# )
# def update_output(n_clicks):
#     if n_clicks > 0:
#         mysim.load(0, "fld-ex1")
#     loadedQ = mysim._snapshots[0]._fields["fld-ex1"].isLoaded
#     return '{} -- {}'.format(
#         loadedQ,
#         n_clicks
#     )

# if __name__ == "__main__":
#     app.run_server(debug=True)

# # layout = go.Layout(
# #     paper_bgcolor='rgba(0,0,0,0)',
# #     plot_bgcolor='rgba(0,0,0,0)',
# #     coloraxis=dict(
# #         colorbar=dict(
# #             xpad=0,
# #         )
# #     )
# # )

# # nx = 1000
# # ny = 500
# # istep = 10

# # x = np.linspace(-2, 2, nx)
# # y = np.linspace(-1, 1, ny)

# # x_, y_ = np.meshgrid(x, y)

# # data = xr.Dataset(
# #     {
# #         'density': (('y', 'x'), x_**2),
# #         'temperature': (('y', 'x'), y_**2),
# #         'pressure': (('y', 'x'), x_ + 15 * y_),
# #     },
# #     coords={
# #         'x': x,
# #         'y': y,
# #     }
# # )
# # canvas = ds.Canvas(plot_width=20, plot_height=10)
# # data_agg = {
# #     k: canvas.raster(data[k], interpolate='nearest')
# #     for k in data.data_vars
# # }
# # print(agg.values.min(), agg.values.max())
# # img = ds.transfer_functions.shade(agg)

# # fig = px.imshow(agg,
# # aspect='equal',
# # origin='lower')
# # fig.show()

# # field-dropdown
# # ┌───┐         ┌─┐ cbar-dropdown
# # ├───┴─────────┼┼│
# # │             │┼│
# # │             │┼│
# # │   2dplot    │┼│
# # │             │┼│ cbar
# # │             │┼│
# # └─────────────┼┼│
# #               └─┘ log-radio

# # fieldDropdown = dash.dcc.Dropdown(
# #     list(data.data_vars), list(data.data_vars)[0],
# #     id="field-dropdown",
# #     searchable=False,
# # )

# # plots = dash.html.Div([
# #     # dash.dcc.Graph(id='graph', config={'displaylogo': False}),
# #     # dash.dcc.Graph(id='graph', config={'displaylogo': False})
# # ], className="graph-container", id="graph-container")

# # top_toolbar = dash.html.Div([
# #     fieldDropdown,
# # ], className="tooltip-container-top")


# # @app.callback(
# #     dash.dependencies.Output('graph-container', 'children'),
# #     dash.dependencies.Input(fieldDropdown, 'value')
# # )
# # def update_graph(field):
# #     # ctx = dash.callback_context
# #     # if not ctx.triggered:
# #     # field = list(data.data_vars.keys())[0]
# #     # else:
# #     # field = ctx.triggered[0]['prop_id'].split('.')[0].split('-')[1]
# #     fig1 = px.imshow(data_agg[field],
# #                      aspect='equal', origin='lower')
# #     fig1.update_layout(layout)
# #     fig2 = px.imshow(data_agg[field],
# #                      aspect='equal', origin='lower')
# #     fig2.update_layout(layout)
# #     graphs = [dash.dcc.Graph(figure=fig1, id='graph-1', config={'displaylogo': False}),
# #               dash.dcc.Graph(figure=fig2, id='graph-2', config={'displaylogo': False})]
# #     return graphs
