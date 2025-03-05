from typing import List, Type
import logging
from .plugin import Plugin
from .utils import array_t, sizeof_fmt


class Data:
    def __init__(
        self,
        plugin: Type[Plugin],
        steps: List[int],
        loglevel: int = logging.ERROR,
        **kwargs,
    ):
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
        import dask.config
        from dask.array.wrap import full as da_full
        from dask.array.core import concatenate as da_concatenate, stack as da_stack
        import xarray as xr
        import numpy as np

        logging.getLogger("graphet.log")
        logging.basicConfig(level=loglevel)

        def list_to_ragged(arr: List[array_t]) -> List[array_t]:
            max_len = np.max([len(a) for a in arr if a is not None])
            return [
                da_concatenate([a, da_full(max_len - len(a), np.nan)])
                for a in arr
                if a is not None
            ]

        self.steps = np.array(steps)

        self.plugin = plugin(**kwargs)
        if self.plugin.params:
            self.params = self.plugin.readParams()
        else:
            self.params = None

        with dask.config.set({"array.slicing.split_large_chunks": True}):
            # preload some of the metadata
            coord_transforms = self.plugin.coord_transform
            self.times = np.array(steps).astype(float)
            if (coord_transforms is not None) and ("t" in coord_transforms.keys()):
                self.times = coord_transforms["t"](self.times, self.params)

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
                        da_stack(datasets[f], axis=0),
                        dims=["t", *coord_keys],
                        name=f,
                        coords={
                            "t": self.times,
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
                    prtl_keys = self.plugin.prtlKeys(sp)
                    datasets = {}
                    for s in self.steps:
                        for k in prtl_keys:
                            if k not in datasets.keys():
                                datasets[k] = []
                            datasets[k].append(self.plugin.particleKey(sp, k, s))

                    lazy_arrays = {}
                    for k in prtl_keys:
                        if self.plugin.has_particle_idx:
                            aligned = xr.align(*datasets[k], join="outer")
                            lazy_arrays[k] = xr.DataArray(
                                da_stack(aligned),
                                dims=["t", "idx"],
                                coords={
                                    "t": self.times,
                                    "idx": aligned[0].coords["idx"],
                                },
                            )
                        else:
                            lazy_arrays[k] = xr.DataArray(
                                da_stack(list_to_ragged(datasets[k])),
                                dims=["t", "idx"],
                                coords={"t": self.times},
                            )
                    self.particles[sp] = xr.Dataset(lazy_arrays)
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
                        da_stack(datasets[sk], axis=0),
                        dims=["t", *list(spec_bins.keys())],
                        coords={"t": self.times, **spec_bins},
                    )
            else:
                self.spectra = None

        print(self)

    def __repr__(self) -> str:
        format_str = "{ Graph-ET Data Container }\n\n"

        format_str += f"Plugin: {type(self.plugin).__name__}\n\n"

        format_str += f"Steps: {self.steps[0]}...{self.steps[-1]} [{len(self.steps)}]\n"
        assert self.times is not None, "Times not assigned"
        format_str += f"Times: {self.times[0]:.2f}...{self.times[-1]:.2f}\n\n"

        if self.plugin.fields is not None and self.fields is not None:
            format_str += f"* Fields [{sizeof_fmt(self.fields.nbytes)}]:\n"
            format_str += f"  - Keys: {self.plugin.fieldKeys()}\n"
            format_str += "  - Coordinates:\n"
            for c, x in self.fields.coords.items():
                format_str += f"    {c}: {x.min().values[()]:.2f}...{x.max().values[()]:.2f} [{x.shape[0]}]\n"
            format_str += "\n"

        if self.plugin.particles is not None and self.particles is not None:
            format_str += f"* Particles:\n"
            for sp, sd in self.particles.items():
                format_str += f"  - Species {sp} [{sizeof_fmt(sd.nbytes)}]:\n"
                format_str += (
                    f"    - Keys: {[str(s) for s in self.plugin.prtlKeys(sp)]}\n"
                )
                format_str += f"    - Number: {self.particles[sp].sizes['idx']}\n"
            format_str += "\n"

        if self.plugin.spectra is not None and self.spectra is not None:
            format_str += f"* Spectra:\n"
            format_str += f"  - Keys: {self.plugin.specKeys()}\n"
            format_str += "\n"
        return format_str

    def __str__(self) -> str:
        return self.__repr__()
