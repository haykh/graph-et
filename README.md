# `graph-et` [grɑːf iː.tiː.]

`dask` and `xarray` based library for loading particle-in-cell simulation data produced by a variety of different codes. The support for arbitrary codes is provided through the so-called plugins. Currently supported (and planned) codes include:

- [ ] Tristan v1
- [x] Tristan v2

### Usage example

```python
from graphet import Data, Dashboard
from graphet.plugins import TristanV2

# to monitor usage etc using a locally hosted dashboard
Dashboard()

# load the metadata using the TristanV2 plugin
d = Data(
    TristanV2,              # plugin
    steps=range(150),       # steps to load metadata for
    path=f"output/",        # path to the data
    cfg_fname=f"input.cfg", # configuration file
    params=True,            # read configuration file
    coord_transform={       # time/coordinate transformation
        "t": lambda t, prm: t * prm["output:interval"] * prm["algorithm:c"] / prm["grid:my0"],
        "x": lambda x, prm: (x - x.mean()) / prm["grid:my0"],
        "z": lambda z, prm: (z - z.mean()) / prm["grid:my0"],
        "y": lambda y, prm: (y - y.mean()) / prm["grid:my0"],
    },
    swapaxes=[(0, 1), (2, 1)],  # axes swapping "zyx" -> "yxz"
)

# main containers are
d.fields      # <- fields
d.particles   # <- particles
d.spectra     # <- spectra

## Examples of doing useful stuff

# plot averaged spectra of species #2 between 1.5 < t < 2.2
d.spectra.n2.sel(t=slice(1.5, 2.2)).mean("t").plot()

# plot the density of species #1 and #2 at time t = 2.5 and y = 0.1
(d.fields.dens1 + d.fields.dens2).sel(y=0.1, t=2.5, method="nearest").plot(cmap="turbo")

# compute the distribution function from the particle data for species #3 at 1.5 < t < 2.2
cnt, _ = np.histogram(
    (np.sqrt(1 + d.particles[3].u ** 2 + d.particles[3].v ** 2 + d.particles[3].w ** 2) - 1)
    .sel(t=slice(1.5, 2.2)).mean("t"),
    bins=np.logspace(-1, 3, 100),
)

# to track the energy of a single particle of species #2 with, e.g., idx = 13500000000000, across timesteps
prtl = d.particles[2].sel(idx=13500000000000)
np.sqrt(1.0 + prtl.u**2 + prtl.v**2 + prtl.w**2).plot()
```

### Todo

- [ ] Add support for `TristanV1` plugin
- [x] Coordinate transformations for particles
- [x] Support for coordinate swapping in field names
- [ ] Support for custom defined fields
