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

        def list_to_ragged(arr: List[da.Array]) -> List[da.Array]:
            max_len = np.max([len(a) for a in arr])
            return [da.concatenate([a, da.full(max_len - len(a), np.nan)]) for a in arr]

        self.steps = np.array(steps)

        self.plugin = plugin(**kwargs)
        if self.plugin.params:
            self.params = self.plugin.readParams()
        else:
            self.params = None

        with dask.config.set(**{"array.slicing.split_large_chunks": True}):
            # preload some of the metadata
            coord_transforms = self.plugin.coord_transform
            times = np.array(steps).astype(float)
            if (coord_transforms is not None) and ("t" in coord_transforms.keys()):
                times = coord_transforms["t"](times, self.params)

            # load field metadata
            if self.plugin.fields is not None:
                self.fields = xr.Dataset()
                flds_keys = self.plugin.fieldKeys()
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

            # load particle metadata
            if self.plugin.particles is not None:
                self.particles = {}
                prtl_species = self.plugin.prtlSpecies()
                for sp in prtl_species:
                    self.particles[sp] = xr.Dataset()
                    prtl_keys = self.plugin.prtlKeys(sp)
                    datasets = {}
                    for s in self.steps:
                        for k in prtl_keys:
                            if k not in datasets.keys():
                                datasets[k] = []
                            datasets[k].append(self.plugin.particleKey(sp, k, s))

                    for k in prtl_keys:
                        self.particles[sp][k] = xr.DataArray(
                            da.stack(list_to_ragged(datasets[k])),
                            dims=["t", "id"],
                            coords={"t": times},
                        )
            else:
                self.particles = None

            # load spectrum metadata
            if self.plugin.spectra is not None:
                self.spectra = xr.Dataset()
                spec_keys = self.plugin.specKeys()
                datasets = {}
                for s in self.steps:
                    for sk in spec_keys:
                        if sk not in datasets.keys():
                            datasets[sk] = []
                        datasets[sk].append(self.plugin.spectrum(sk, s))

                for sk in spec_keys:
                    spec_bins = self.plugin.specBins(sk)
                    self.spectra[sk] = xr.DataArray(
                        da.stack(datasets[sk], axis=0),
                        dims=["t", *list(spec_bins.keys())],
                        coords={"t": times, **spec_bins},
                    )
            else:
                self.spectra = None

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
