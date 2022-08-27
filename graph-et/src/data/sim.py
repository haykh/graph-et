from typing import Dict, Any, List
from collections.abc import Callable
from numpy.typing import NDArray
import datashader as ds
from typeguard import typechecked

from ..defs import FnameTemplate
from ..utils import *


@typechecked
class LazyContainer:
    def __init__(self, loadData: Callable) -> None:
        self._loadData = loadData
        self._data = None
        self._aggdata = None
        self._loaded = False
        self._aggregated = False

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
        cnv = ds.Canvas(plot_width=w, plot_height=h)
        self._aggdata = {
            k: cnv.raster(self._data[k], interpolate='nearest')
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


@typechecked
class Snapshot:
    def __init__(self,
                 loadFields: Callable[[int], Callable[[], Any]],
                 tstep: int = 0) -> None:
        self._tstep = tstep
        self._spectra = {}
        self._particles = {}
        self._fields = LazyContainer(loadFields(tstep))

    def __del__(self) -> None:
        self.unload()

    @property
    def tstep(self) -> int:
        return self._tstep

    def load(self) -> None:
        self._fields.load()

    def aggregate(self, w: int, h: int) -> None:
        self._fields.aggregate(w, h)

    def unload(self) -> None:
        self._fields.unload()

    def unaggregate(self) -> None:
        self._fields.unaggregate()

    @property
    def fields(self) -> Any:
        return self._fields

    # def getRawField(self,
    #                 f: str) -> NDArray:
    #     try:
    #         return self._fields.data[f].data
    #     except KeyError as e:
    #         raise Exception(f"Field {f} not found") from e
    #     except Exception as e:
    #         raise Exception(f"Unable to get field {f}: {e.args[0]}") from e

    @property
    def loaded(self) -> bool:
        return self._fields.loaded

    @property
    def aggregated(self) -> bool:
        return self._fields.aggregated


@typechecked
class Simulation:
    def __init__(self,
                 name: str,
                 path: str,
                 flds_fname: FnameTemplate = None,
                 tsteps: List[int] = []) -> None:
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
        self._snapshots = {
            tstep: Snapshot(loadFields, tstep) for tstep in self._tsteps
        }
        # print(self)

    def __del__(self) -> None:
        if self._tsteps is not None and len(self._tsteps) > 0:
            for t in self._tsteps:
                self.unload(t)

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
    def path(self) -> str:
        return self._path

    @property
    def tsteps(self) -> List[int]:
        return self._tsteps

    @property
    def snapshots(self) -> Dict[int, Snapshot]:
        return self._snapshots

    @property
    def flds_fname(self) -> FnameTemplate:
        return self._flds_fname

    def load(self,
             tstep: int) -> None:
        self._snapshots[tstep].load()

    def loadAll(self) -> None:
        for t in self._tsteps:
            self.load(t)

    def unload(self,
               tstep: int) -> None:
        self._snapshots[tstep].unload()

    def unloadAll(self) -> None:
        for t in self._tsteps:
            self.unload(t)

    # def getRawField(self,
    #                 tstep: int,
    #                 f: str) -> NDArray:
    #     return self._snapshots[tstep].getRawField(f)


# @typechecked
# class Field:
#     def __init__(self,
#                  label: str) -> None:
#         self._isLoaded = False
#         self._isAggregated = False
#         self._label = label
#         self._data = None
#         self._agg = None

#     def __del__(self) -> None:
#         self.unload()

#     @property
#     def label(self) -> str:
#         return self._label

#     @property
#     def data(self) -> NDArray:
#         return self._data

#     @property
#     def agg(self):
#         return self._agg

#     @property
#     def isLoaded(self) -> bool:
#         return self._isLoaded

#     @property
#     def isAggregated(self) -> bool:
#         return self._isAggregated

#     @property
#     def data(self) -> NDArray:
#         return self._data

#     def load(self,
#              path: str,
#              fname_template: str,
#              tstep: int) -> None:
#         if self._isLoaded:
#             return
#         try:
#             self._data = LoadHdf5Field(
#                 self._label, path, fname_template, tstep)
#         except MemoryError as e:
#             raise Exception(f"Cannot fit field into memory") from e
#         except FileNotFoundError as e:
#             raise Exception(f"Cannot find field file") from e
#         except KeyError as e:
#             raise Exception(f"Cannot find field in file") from e
#         except Exception as e:
#             raise Exception(f"Unable to load field: {e.args[0]}") from e
#         else:
#             self._isLoaded = True

#     def unload(self) -> None:
#         if self._isLoaded:
#             del self._data
#             self._isLoaded = False

#     def aggregate(self) -> None:
#         pass
#         self._isAggregated = True

#     # TODO:
#     def describe(self) -> None:
#         pass
