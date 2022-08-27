from typing import List, Dict, Union, Any
from typeguard import typechecked

import dash
from ..data.sim import Simulation

FnameTemplate = Union[str, None]


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


@typechecked
class Configs:
    def __init__(self, app, simulations: Dict[str, Simulation]) -> None:
        self._view = [
            dash.html.Div(id='add-simulation-form', children=[
                dash.dcc.Input(
                    id="input-sim-name",
                    type="text",
                    placeholder="Simulation name",
                    debounce=True,
                ),
                dash.dcc.Input(
                    id="input-sim-path",
                    type="text",
                    placeholder="Simulation path",
                    debounce=True,
                    required=True,
                ),
                dash.html.Button(
                    "Add",
                    id="button-sim-path"
                ),
                dash.dcc.Checklist(
                    ["Fields", "Particles"],
                    ["Fields"],
                    id="check-load-vals"
                ),
                dash.dcc.Input(
                    id="input-flds-file",
                    type="text",
                    placeholder="flds.tot.%05d",
                    debounce=True,
                ),
                dash.dcc.Input(
                    id="input-prtl-file",
                    type="text",
                    placeholder="prtl.tot.%05d",
                    debounce=True,
                ),
            ]),
            dash.html.Div(
                children=[],
                id="simulation-list"
            ),
        ]

        # ------------------------------ add simulation ------------------------------ #
        @app.callback(
            dash.Output("simulation-list", "children"),
            [
                dash.Input("button-sim-path", "n_clicks"),
                dash.State("input-sim-name", "value"),
                dash.State("input-sim-path", "value"),
                dash.State("check-load-vals", "value"),
                dash.State("input-flds-file", "value"),
                dash.State("input-prtl-file", "value")
            ],
            dash.Input(
                {"type": "sim-loadedQ", "index": dash.ALL}, "children"),
        )
        def add_sim(_1: int,
                    name: str,
                    path: str,
                    load_vals: List[str],
                    flds_file: str,
                    prtl_file: str,
                    _2: str) -> List:
            if (dash.ctx.triggered_id == "button-sim-path"):
                name = (name if (name is not None and name != "")
                        else f"SIM_{len(simulations)}")
                if "Fields" not in load_vals:
                    flds_file = None
                elif flds_file is None or flds_file == "":
                    flds_file = "flds.tot.%05d"
                if "Particles" not in load_vals:
                    prtl_file = None
                elif prtl_file is None or prtl_file == "":
                    prtl_file = "prtl.tot.%05d"
                if ((path is not None) and (path != "")):
                    self.addSimulation(simulations,
                                       name,
                                       path,
                                       flds_file,
                                       prtl_file)
                else:
                    # !DEBUG
                    self.addSimulation(simulations,
                                       name,
                                       "graph-et/tests/test_data_2",
                                       "dummy%02d.hdf5",
                                       prtl_file)
            return [simulationItem(s) for _, s in simulations.items()]

        # -------------------------- load/remove simulation -------------------------- #
        @app.callback(
            dash.Output(
                {"index": dash.MATCH, "type": "sim-loadedQ"}, "children"),
            dash.Input(
                {"index": dash.MATCH, "type": "sim-remove"}, "n_clicks"),
            dash.Input(
                {"index": dash.MATCH, "type": "sim-load"}, "n_clicks"),
            dash.Input(
                {"index": dash.MATCH, "type": "sim-unload"}, "n_clicks"),
            dash.State(
                {"index": dash.MATCH, "type": "sim-remove"}, "id"),
            dash.State(
                {"index": dash.MATCH, "type": "sim-load"}, "id"),
            dash.State(
                {"index": dash.MATCH, "type": "sim-unload"}, "id"),
            dash.State(
                {"index": dash.MATCH, "type": "sim-loadedQ"}, "children"),
        )
        def ldrm_sim(n_rm, n_ld, n_un: int,
                     id_rm, id_ld, id_un: Dict[str, Any],
                     loaded_txt) -> None:
            if n_rm is not None:
                if id_rm["index"] in simulations:
                    simulations.pop(id_rm["index"])
                return loaded_txt + "-remove"
            elif n_ld is not None:
                if id_ld["index"] in simulations:
                    simulations[id_ld["index"]].loadAll()
                return loaded_txt + "-load"
            elif n_un is not None:
                if id_un["index"] in simulations:
                    simulations[id_un["index"]].unloadAll()
                return loaded_txt + "-unload"
            else:
                return loaded_txt

    @property
    def view(self) -> List:
        return self._view

    def addSimulation(self,
                      simulations: Dict[str, Simulation],
                      name: str,
                      path: str,
                      flds_file: FnameTemplate,
                      prtl_file: FnameTemplate) -> None:
        # TODO: warn if simulation is already in list
        # TODO: error handling here (missing files etc)
        simulations[name] = Simulation(name, path, flds_file, prtl_file)
