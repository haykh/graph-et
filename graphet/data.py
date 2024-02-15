from typing import List
from .plugin import Plugin


class Data:
    def __init__(self, plugin: Plugin, steps: List[int], **kwargs):
        """
        Main data container class.

        Parameters
        ----------
        `plugin` : `Plugin`
            the data reading plugin to use
        `steps` : `List[int]`
            the steps to read
        `**kwargs`: `Dict[str, Any]`
            the keyword arguments to pass to the plugin
        """
        import dask
        import dask.array as da
        import xarray as xr
        import numpy as np

        self.steps = np.array(steps)

        self.plugin = plugin(**kwargs)

        with dask.config.set(**{"array.slicing.split_large_chunks": True}):
            # preload some of the metadata
            params = self.plugin.readParams()
            coord_transforms = self.plugin.coord_transform
            flds_keys = self.plugin.fieldKeys()
            times = np.array(steps).astype(float)
            if (coord_transforms is not None) and ("t" in coord_transforms.keys()):
                times = coord_transforms["t"](times, params)

            # load field metadata
            if self.plugin.fields is not None:
                self.fields = xr.Dataset()
                coords = self.plugin.coords()
                coord_keys = list(coords.keys())
                swapaxes = self.plugin.swapaxes
                if swapaxes is not None:
                    ax = list("xyz")
                    for sw in swapaxes:
                        ax[sw[0]], ax[sw[1]] = ax[sw[1]], ax[sw[0]]
                    coord_keys = ax[::-1]

                datasets = {}
                for s in self.steps:
                    for f in flds_keys:
                        if f not in datasets.keys():
                            datasets[f] = []
                        datasets[f].append(self.plugin.field(f, s))

                for f in flds_keys:
                    self.fields[f] = xr.DataArray(
                        da.stack(datasets[f], axis=0),
                        dims=["t", *coord_keys],
                        name=f,
                        coords={
                            "t": times,
                            **coords,
                        },
                    )
            else:
                self.fields = None

            if self.plugin.particles is not None:
                self.particles = {}
                prtl_species = self.plugin.prtlSpecies()
                prtl_keys = self.plugin.prtlKeys()
                for p in prtl_species:
                    self.particles[p] = xr.Dataset()
                    for k in prtl_keys:
                        try:
                            self.particles[p][k] = self.plugin.particleKey(p, k, steps)
                        except:
                            ...
            else:
                self.particles = None

            if self.plugin.spectra is not None:
                self.spectra = xr.Dataset()
                for s in self.plugin.specKeys():
                    self.spectra[s] = self.plugin.spectrum(s, steps)
            else:
                self.spectra = None

            if self.plugin.params:
                self.params = self.plugin.readParams()
            else:
                self.params = None

    def __repr__(self) -> str:
        format_str = "Data container\n\n"
        format_str += f"Plugin: {type(self.plugin).__name__}\n"
        if self.plugin.fields is not None:
            format_str += f"Fields: {list(self.plugin.fieldKeys())}\n"
            format_str += "Coordinates:\n"
            for c, x in self.fields.coords.items():
                format_str += f"  {c}: {x.min().values[()]:.2f}...{x.max().values[()]:.2f} [{x.shape[0]}]\n"
        return format_str

    def __str__(self) -> str:
        return self.__repr__()
