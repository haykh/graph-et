from typing import Dict, Any, List
from collections.abc import Callable
import datashader as ds
import numpy as np

from ..defs import FnameTemplate
from ..utils import *


class LazyContainer:
    def __init__(self, loadData: Callable) -> None:
        self._loadData = loadData
        self._data = None
        self._aggdata = None
        self._loaded = False
        self._aggregated = False

    def __del__(self) -> None:
        self.unload()
        self.unaggregate()

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def aggregated(self) -> bool:
        return self._aggregated

    def load(self) -> None:
        if self._data is None:
            try:
                self._data = self._loadData()
            except MemoryError as e:
                raise Exception(f"Cannot fit field into memory") from e
            except FileNotFoundError as e:
                raise Exception(f"Cannot find field file") from e
            except KeyError as e:
                raise Exception(f"Cannot find field in file") from e
            except Exception as e:
                raise Exception(f"Unable to load field: {e.args[0]}") from e
            else:
                self._loaded = True

    def aggregate(self, w: int, h: int, load: bool = True) -> None:
        if self._data is None:
            if load:
                self.load()
            else:
                raise ValueError("Data not loaded")
        wmax, hmax = [self._data[k].shape for k in self._data.data_vars][0]
        w = min(w, wmax)
        h = min(h, hmax)
        cnv = ds.Canvas(plot_width=w, plot_height=h)
        self._aggdata = {
            k: cnv.raster(self._data[k], interpolate="nearest")
            for k in self._data.data_vars
        }
        self._aggregated = True

    def unload(self) -> None:
        del self._data
        self._data = None
        self._loaded = False

    def unaggregate(self) -> None:
        del self._aggdata
        self._aggdata = None
        self._aggregated = False

    @property
    def data(self) -> Any:
        return self._data

    @property
    def aggdata(self) -> Any:
        return self._aggdata


class Simulation:
    def __init__(
        self,
        name: str,
        path: str,
        flds_fname: FnameTemplate = None,
        tsteps: List[int] = [],
    ) -> None:
        if len(tsteps) == 0:
            self._tsteps = []
            if flds_fname is not None:
                self._tsteps = AutoDetectTSteps(path, flds_fname)
            else:
                raise Exception("No tsteps detected")
        else:
            self._tsteps = tsteps
        self._name = name
        self._path = path
        self._flds_fname = flds_fname

        def loadFields(t: int) -> Callable[[], Any]:
            return lambda: Hdf5toXarray_flds(self._path, self._flds_fname, t)

        def loadKeys(t: int) -> List[str]:
            return Hdf5toKeys_flds(self._path, self._flds_fname, t)

        self._snapshots = {
            tstep: LazyContainer(loadFields(tstep)) for tstep in self._tsteps
        }
        self._field_keys = loadKeys(self._tsteps[0])

    def __del__(self) -> None:
        if self._tsteps is not None and len(self._tsteps) > 0:
            for t in self._tsteps:
                del self._snapshots[t]

    @property
    def memoryUsage(self) -> str:
        return SizeofFmt(GetSimulationSize(self))

    @property
    def params(self) -> Dict[str, Any]:
        return self._params

    @property
    def name(self) -> str:
        return self._name

    @property
    def tsteps(self) -> List[int]:
        return self._tsteps

    @property
    def field_keys(self) -> List[str]:
        return list(self._field_keys)

    @property
    def loaded(self) -> bool:
        return all([self._snapshots[t].loaded for t in self._tsteps])

    @property
    def snapshots(self) -> Dict[int, "LazyContainer"]:
        return self._snapshots

    def getAggregatedField(self, tstep: int, key: str) -> Any:
        assert self._snapshots[tstep].aggregated, "Data not aggregated"
        return self._snapshots[tstep].aggdata[key]

    def getRawField(self, tstep: int, key: str) -> Any:
        assert self._snapshots[tstep].loaded, "Data not loaded"
        return self._snapshots[tstep].data[key]

    def load(self, tstep: int) -> None:
        self._snapshots[tstep].load()

    def loadAll(self) -> None:
        for t in self._tsteps:
            self.load(t)

    def aggregate(self, tstep: int, w: int, h: int) -> None:
        self._snapshots[tstep].aggregate(w, h)

    def unload(self, tstep: int) -> None:
        self._snapshots[tstep].unload()

    def unloadAll(self) -> None:
        for t in self._tsteps:
            self.unload(t)

    # for internal use only
    @property
    def path(self) -> str:
        return self._path

    @property
    def flds_fname(self) -> "FnameTemplate":
        return self._flds_fname

    # def __str__(self) -> str:
    #     s0 = list(self._snapshots.keys())[0]
    #     if self._snapshots[s0]._fields != {}:
    #         fields = self._snapshots[s0]._fields.keys()
    #     else:
    #         fields = ["None"]
    #     if self._snapshots[s0]._particles != {}:
    #         particles = self._snapshots[s0]._particles.keys()
    #     else:
    #         particles = ["None"]
    #     snapshots = self._snapshots
    #     return \
    #         "-"*30 + "\n" + \
    #         f'Simulation:\t {self.name}' +\
    #         f'\nPath:\t\t {self.path}' +\
    #         f'\nFilenames:\t {self._flds_fname if self._flds_fname is not None else "None"} (fields)' + ", " +\
    #         f'\nTimesteps:\t {self.tsteps}' +\
    #         f'\nFields:\t\t ' + ', '.join(fields) +\
    #         ((f'\nLoaded?\n' + "".join(
    #             [f'\t{f}:\t {"".join(["*" if s.isLoaded else "_" for _, s in snapshots.items()])}\n' for f in fields]
    #         )) if (fields != ["None"]) else "") +\
    #         ((f'Aggregated?\n' + "".join(
    #             [f'\t{f}:\t {"".join(["*" if s._fields[f].isAggregated else "_" for _, s in snapshots.items()])}\n' for f in fields]
    #         )) if (fields != ["None"]) else "") +\
    #         f'Particles:\t ' + ', '.join(particles) +\
    #         f"\n\nOverall size:\t {self.memoryUsage}"

    #     # f"{self._prtls_fname_template if self._prtls_fname_template is not None else 'None'} (particles)" +\
