from ..sim import Simulation
from typeguard import typechecked
import dash

@typechecked
def simulationItem(sim: Simulation) -> dash.html.Div:
    return dash.html.Div(children=[
        dash.html.P(sim.name + " : " + sim.path, className="sim-label"),
        dash.html.Div(children=[
            dash.html.Button(str(t), disabled=(not s.isLoaded), className="sim-load-btn",
                             id={"index": sim.name + "_" + str(t),
                                 "type": "sim-load-btn"}
                             ) for t, s in zip(sim.tsteps, sim.snapshots.values())
        ],
            className="sim-timesteps",
            id={"index": sim.name, "type": "sim-timesteps"}
        ),
        dash.html.Button("x", className="sim-remove",
                         id={"index": sim.name, "type": "sim-remove"})
    ])
