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
        import xarray as xr
        import numpy as np
        import dask.array as da

        self.steps = np.array(steps)

        self.plugin = plugin(**kwargs)
        # if self.plugin.fields is not None:
        #     self.fields = xr.Dataset()
        #     for f in self.plugin.fieldKeys():
        #         self.fields[f] = self.plugin.field(f, steps)
        if self.plugin.fields is not None:
            coords = self.plugin.coords()
            times = np.array(steps).astype(float)
            if (self.plugin.coord_transform is not None) and (
                "t" in self.plugin.coord_transform.keys()
            ):
                params = self.plugin.readParams()
                times = self.plugin.coord_transform["t"](times, params)
            self.fields = xr.Dataset()
            datasets = {}
            for s in self.steps:
                for f in self.plugin.fieldKeys():
                    if f not in datasets.keys():
                        datasets[f] = []
                    arr = self.plugin.field1(f, s)
                    datasets[f].append(arr)
                # self.fields[f]

            for f in self.plugin.fieldKeys():
                self.fields[f] = xr.DataArray(
                    da.stack(datasets[f], axis=0),
                    dims=["t", *list(coords.keys())],
                    name=f,
                    coords={
                        "t": times,
                        **coords,
                    },
                )
            # self.fields = xr.Dataset()
            # for f in self.plugin.fieldKeys():
            #     self.fields[f] = self.plugin.field(f, steps)

        # if self.plugin.particles is not None:
        #     self.particles = {}
        #     all_species = self.plugin.prtlSpecies()
        #     all_keys = self.plugin.prtlKeys()
        #     for p in all_species:
        #         self.particles[p] = xr.Dataset()
        #         for k in all_keys:
        #             try:
        #                 self.particles[p][k] = self.plugin.particleKey(p, k, steps)
        #             except:
        #                 ...

        # if self.plugin.spectra is not None:
        #     self.spectra = xr.Dataset()
        #     for s in self.plugin.specKeys():
        #         self.spectra[s] = self.plugin.spectrum(s, steps)

        if self.plugin.params:
            self.params = self.plugin.readParams()

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
