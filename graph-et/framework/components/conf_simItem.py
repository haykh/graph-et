from ..sim import Simulation
from typeguard import typechecked
import dash


@typechecked
def simulationItem(sim: Simulation) -> dash.html.Div:
    sim_title = dash.html.H1(
        sim.name + " : " + sim.path, className="sim-label")
    sim_memory = dash.html.H3(sim.memoryUsage, className="sim-memory")
    sim_flds = dash.html.P(
        f"fields: {(sim.flds_fname if sim.flds_fname else 'N/A')}",
        className="sim-flds-fname")
    sim_prtls = dash.html.P(
        f"particles: {(sim.prtls_fname if sim.prtls_fname else 'N/A')}", className="sim-prtls-fname")
    # sim_timesteps = dash.html.Div(children=[
    #     dash.html.Button(str(t), disabled=(not s.isLoaded), className="sim-load-btn",
    #                      id={"index": sim.name + "_" + str(t),
    #                          "type": "sim-load-btn"}
    #                      ) for t, s in zip(sim.tsteps, sim.snapshots.values())
    # ],
    #     className="sim-timesteps",
    #     id={"index": sim.name, "type": "sim-timesteps"}
    # )
    sim_remove = dash.html.Button("❌ close", className="sim-remove",
                                  id={"index": sim.name, "type": "sim-remove"})
    sim_load = dash.html.Button("⬆️ load", className="sim-load",
                                id={"index": sim.name, "type": "sim-load"})
    sim_unload = dash.html.Button("⬇️ unload", className="sim-unload",
                                id={"index": sim.name, "type": "sim-unload"})
    sim_indicator = dash.html.Div("",
                                  id={"index": sim.name, "type": "sim-loadedQ"})
    return dash.html.Div(children=[
        sim_title,
        sim_memory,
        dash.html.Div([sim_flds, sim_prtls]),
        sim_load,
        sim_unload,
        sim_remove,
        sim_indicator
    ])
