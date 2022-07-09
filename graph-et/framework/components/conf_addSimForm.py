from typeguard import typechecked
import dash

@typechecked
def addSimForm() -> dash.html.Div:
    return dash.html.Div(id='add-simulation-form', children=[
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
    ])
