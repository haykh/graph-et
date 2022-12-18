import dash
import dash_bootstrap_components as dbc
from typing import List, Dict, Union, Any

from ..data.sim import Simulation

FnameTemplate = Union[str, None]


def simulationItem(sim: Simulation) -> dash.html.Div:
    sim_name = dash.html.H3(sim.name, className="float-left d-inline align-middle")
    sim_load = dbc.Button(
        "⬆ load",
        color="primary" if not sim.loaded else "secondary",
        className="sim-load",
        id={"index": sim.name, "type": "sim-load"},
        disabled=sim.loaded,
    )
    sim_unload = dbc.Button(
        "⬇ unload",
        color="primary" if sim.loaded else "secondary",
        className="sim-unload",
        id={"index": sim.name, "type": "sim-unload"},
        disabled=not sim.loaded,
    )
    sim_remove = dbc.Button(
        "❌",
        color="secondary",
        className="sim-remove float-end d-inline",
        id={"index": sim.name, "type": "sim-remove"},
    )
    sim_memory = dash.html.P(f"size : {sim.memoryUsage}", className="sim-memory")
    sim_loadunload = dbc.ButtonGroup([sim_load, sim_unload], className="float-end")
    sim_indicator = dash.html.Div("", id={"index": sim.name, "type": "sim-loadedQ"})
    return dbc.Col(
        dbc.Card(
            [
                dbc.CardHeader(
                    [sim_name, sim_remove],
                    className="sim-label",
                ),
                dbc.CardBody(
                    [
                        dash.html.H5(f"path : {sim.path}", className="sim-path"),
                        dash.html.P(
                            f"fields files : {(sim.flds_fname if sim.flds_fname else 'N/A')}",
                            className="sim-flds-fname",
                        ),
                    ]
                ),
                dbc.CardFooter(
                    dbc.Row(
                        [
                            dbc.Col(sim_memory, width=5),
                            dbc.Col(sim_loadunload, width=7),
                        ],
                        align="center",
                    ),
                ),
                sim_indicator,
            ],
        ),
        md=4,
    )


class Configs:
    def __init__(self, app, simulations: Dict[str, Simulation]) -> None:
        addbutton = dbc.Button(
            "Add simulation",
            color="primary",
            id="button-sim-path",
            className="flex-grow-1",
        )
        simpath = dbc.Input(
            id="input-sim-path",
            type="text",
            placeholder="path",
            debounce=True,
        )
        simname = dbc.Input(
            id="input-sim-name",
            type="text",
            placeholder="name",
            debounce=True,
        )
        simdata = dbc.Checklist(
            options=[
                {"label": "fields", "value": 1},
                {"label": "particles", "value": 2, "disabled": True},
            ],
            value=[1],
            id="check-load-vals",
            switch=True,
            className="float-right",
        )
        fldpath = dbc.Input(
            id="input-flds-file",
            type="text",
            placeholder="flds.tot.%05d",
            debounce=True,
        )
        prtlpath = dbc.Input(
            id="input-prtl-file",
            type="text",
            placeholder="prtl.tot.%05d",
            debounce=True,
        )

        self._view = [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Col(
                                    [addbutton],
                                    width=4,
                                    className="d-flex flex-column p-0",
                                ),
                                dbc.Col([simpath, simname], width=8, className="p-0"),
                            ]
                        ),
                        width=5,
                    ),
                    dbc.Col(
                        [simdata],
                        width=2,
                    ),
                    dbc.Col(
                        [fldpath, prtlpath],
                        width=5,
                    ),
                ],
                align="center",
                justify="center",
                className="m-0"
            ),
            dbc.Row(children=[], id="simulation-list", className="d-flex flex-row"),
        ]
        # ------------------ enable/disabled field/prtl path inputs ------------------ #
        @app.callback(
            dash.Output("input-flds-file", "disabled"),
            dash.Output("input-prtl-file", "disabled"),
            dash.Input("check-load-vals", "value"),
        )
        def updateDisabled(value: List[int]) -> List[bool]:
            return [1 not in value, 2 not in value]

        # ------------------------------ add simulation ------------------------------ #
        @app.callback(
            [
                dash.Output("simulation-list", "children"),
                dash.Output(
                    {"index": dash.ALL, "type": "plot-sim-dropdown"}, "options"
                ),
                dash.Output("plot-timestep", "max"),
                dash.Output("plot-timestep", "marks"),
                dash.Output("plot-timestep-row", "className"),
            ],
            [
                dash.Input("button-sim-path", "n_clicks"),
                dash.State("input-sim-name", "value"),
                dash.State("input-sim-path", "value"),
                dash.State("check-load-vals", "value"),
                dash.State("input-flds-file", "value"),
                dash.State("input-prtl-file", "value"),
            ],
            [
                dash.Input({"type": "sim-loadedQ", "index": dash.ALL}, "children"),
                dash.Input({"index": dash.ALL, "type": "plot-sim-dropdown"}, "value"),
            ],
        )
        def add_sim(
            _1: int,
            name: str,
            path: str,
            load_vals: List[str],
            flds_file: str,
            prtl_file: str,
            _2: str,
            sim_dropdowns: List[str],
        ):
            if dash.ctx.triggered_id == "button-sim-path":
                name = (
                    name
                    if (name is not None and name != "")
                    else f"SIM_{len(simulations)}"
                )
                if 1 not in load_vals:
                    flds_file = None
                elif flds_file is None or flds_file == "":
                    flds_file = "flds.tot.%05d"
                if 2 not in load_vals:
                    prtl_file = None
                elif prtl_file is None or prtl_file == "":
                    prtl_file = "prtl.tot.%05d"
                if (path is not None) and (path != ""):
                    self.addSimulation(simulations, name, path, flds_file)
                else:
                    # !DEBUG
                    self.addSimulation(
                        simulations, name, "graph-et/tests/test_data", "dummy%02d.hdf5"
                    )
            sims = (
                [{"label": i, "value": i} for i in list(simulations.keys())]
                if len(list(simulations.keys())) > 0
                else []
            )
            nplots = len(sim_dropdowns)
            # !TODO: common tsteps for all sims
            timesteps = (
                []
                if len(simulations) == 0
                else simulations[list(simulations.keys())[0]].tsteps
            )
            return (
                [simulationItem(s) for _, s in simulations.items()],
                [sims] * nplots,
                len(timesteps) - 1,
                {i: str(i) for i in timesteps} if len(timesteps) > 0 else None,
                "d-none" if len(sims) == 0 else "",
            )

        # -------------------------- load/remove simulation -------------------------- #
        @app.callback(
            dash.Output({"index": dash.MATCH, "type": "sim-loadedQ"}, "children"),
            [
                dash.Input({"index": dash.MATCH, "type": "sim-remove"}, "n_clicks"),
                dash.Input({"index": dash.MATCH, "type": "sim-load"}, "n_clicks"),
                dash.Input({"index": dash.MATCH, "type": "sim-unload"}, "n_clicks"),
            ],
            [
                dash.State({"index": dash.MATCH, "type": "sim-remove"}, "id"),
                dash.State({"index": dash.MATCH, "type": "sim-load"}, "id"),
                dash.State({"index": dash.MATCH, "type": "sim-unload"}, "id"),
                dash.State({"index": dash.MATCH, "type": "sim-loadedQ"}, "children"),
            ],
        )
        def ldrm_sim(
            n_rm, n_ld, n_un: int, id_rm, id_ld, id_un: Dict[str, Any], loaded_txt
        ) -> str:
            txt = loaded_txt
            if n_rm is not None:
                if id_rm["index"] in simulations:
                    simulations.pop(id_rm["index"])
                txt += "-remove"
            elif n_ld is not None:
                if id_ld["index"] in simulations:
                    simulations[id_ld["index"]].loadAll()
                txt += "-load"
            elif n_un is not None:
                if id_un["index"] in simulations:
                    simulations[id_un["index"]].unloadAll()
                txt += "-unload"
            return txt

    @property
    def view(self) -> List:
        return self._view

    def addSimulation(
        self,
        simulations: Dict[str, Simulation],
        name: str,
        path: str,
        flds_file: FnameTemplate,
    ) -> None:
        # TODO: warn if simulation is already in list
        # TODO: error handling here (missing files etc)
        simulations[name] = Simulation(name, path, flds_file)
