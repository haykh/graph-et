from typing import Dict, Any, List, Union
from numpy.typing import NDArray
from typeguard import typechecked

FnameTemplate = Union[str, None]


@typechecked
def HandleFname(template: str, tstep: int = None) -> str:
    if '%' in template:
        return template % tstep
    else:
        return template


@typechecked
def AutoDetectTSteps(path: str,
                     fname_template: FnameTemplate) -> List[int]:
    import os
    fname = fname_template.split('%')[0]
    ext = fname_template.split('.')[-1]
    try:
        tsteps = [int(f.replace(fname, '').replace('.' + ext, ''))
                  for f in os.listdir(path) if f.startswith(fname)]
        tsteps.sort()
        return tsteps
    except Exception as e:
        raise Exception(
            f"Unable to find tsteps, {path}, {fname}, {ext}: {e.args}") from e
    return []


@typechecked
def CreateFieldKeysFromHdf5(path: str,
                            fname_template: FnameTemplate,
                            tstep: int) -> List[str]:
    import h5py
    with h5py.File(f'{path}/{HandleFname(fname_template, tstep)}', 'r') as f:
        return list(f.keys())


@typechecked
def LoadHdf5Field(fld: str,
                  path: str,
                  fname_template: FnameTemplate,
                  tstep: int) -> NDArray:
    import h5py
    import numpy as np
    with h5py.File(f'{path}/{HandleFname(fname_template, tstep)}', 'r') as f:
        if (fld not in f.keys()):
            raise KeyError
        data = np.squeeze(f[fld][:])
    return data


@typechecked
class Field:
    def __init__(self,
                 label: str) -> None:
        self._isLoaded = False
        self._isAggregated = False
        self._label = label
        self._data = None
        self._agg = None

    def __del__(self) -> None:
        self.unload()

    @property
    def label(self) -> str:
        return self._label

    @property
    def data(self) -> NDArray:
        return self._data

    @property
    def agg(self):
        return self._agg

    @property
    def isLoaded(self) -> bool:
        return self._isLoaded

    @property
    def isAggregated(self) -> bool:
        return self._isAggregated

    @property
    def data(self) -> NDArray:
        return self._data

    def load(self,
             path: str,
             fname_template: str,
             tstep: int) -> None:
        try:
            self._data = LoadHdf5Field(
                self._label, path, fname_template, tstep)
        except MemoryError as e:
            raise Exception(f"Cannot fit field into memory") from e
        except FileNotFoundError as e:
            raise Exception(f"Cannot find field file") from e
        except KeyError as e:
            raise Exception(f"Cannot find field in file") from e
        except Exception as e:
            raise Exception(f"Unable to load field: {e.args[0]}") from e
        else:
            self._isLoaded = True

    def unload(self) -> None:
        if self._isLoaded:
            del self._data
            self._isLoaded = False

    def aggregate(self) -> None:
        pass
        self._isAggregated = True

    # TODO:
    def describe(self) -> None:
        pass


@typechecked
class Snapshot:
    def __init__(self,
                 path: str,
                 flds_fname_template: FnameTemplate,
                 prtls_fname_template: FnameTemplate,
                 tstep: int = 0) -> None:
        self._tstep = tstep
        self._fields = {}
        self._spectra = {}
        self._particles = {}
        fields = CreateFieldKeysFromHdf5(
            path, flds_fname_template, tstep
        ) if flds_fname_template is not None else []
        for f in fields:
            self._fields[f] = Field(f)

    def __del__(self) -> None:
        self.unload()

    @property
    def tstep(self) -> int:
        return self._tstep

    def load(self,
             path: str,
             flds_fname_template: FnameTemplate,
             prtls_fname_template: FnameTemplate) -> None:
        for _, fld in self._fields.items():
            fld.load(path, flds_fname_template, self._tstep)

    def unload(self) -> None:
        for _, fld in self._fields.items():
            fld.unload()

    def getRawField(self,
                    f: str) -> NDArray:
        return self._fields[f].data


@typechecked
class Simulation:
    def __init__(self,
                 name: str,
                 path: str,
                 flds_fname_template: FnameTemplate = None,
                 prtls_fname_template: FnameTemplate = None,
                 tsteps: List[int] = [],
                 params: Dict[str, Any] = {}) -> None:
        if len(tsteps) == 0:
            self._tsteps = []
            if flds_fname_template is not None:
                self._tsteps = AutoDetectTSteps(path, flds_fname_template)
            elif prtls_fname_template is not None:
                self._tsteps = AutoDetectTSteps(path, prtls_fname_template)
            else:
                raise Exception("No tsteps detected")
        else:
            self._tsteps = tsteps
        self._name = name
        self._path = path
        self._params = params
        self._flds_fname_template = flds_fname_template
        self._prtls_fname_template = prtls_fname_template
        self._snapshots = {
            tstep: Snapshot(path, flds_fname_template, prtls_fname_template, tstep) for tstep in self._tsteps
        }
        print(self)

    def __del__(self) -> None:
        if self._tsteps is not None and len(self._tsteps) > 0:
            for t in self._tsteps:
                self.unload(t)

    def __str__(self) -> str:
        if self._snapshots[0]._fields != {}:
            fields = self._snapshots[0]._fields.keys()
        else:
            fields = ["None"]
        if self._snapshots[0]._particles != {}:
            particles = self._snapshots[0]._particles.keys()
        else:
            particles = ["None"]
        snapshots = self._snapshots
        return \
            "-"*30 + "\n" + \
            f'Simulation:\t {self.name}' +\
            f'\nPath:\t\t {self.path}' +\
            f'\nFilenames:\t {self._flds_fname_template if self._flds_fname_template is not None else "None"} (fields)' + ", " +\
            f"{self._prtls_fname_template if self._prtls_fname_template is not None else 'None'} (particles)" +\
            f'\nTimesteps:\t {self.tsteps}' +\
            f'\nFields:\t\t ' + ', '.join(fields) +\
            ((f'\nLoaded?\n' + "".join(
                [f'\t{f}:\t {"".join(["*" if s._fields[f].isLoaded else "_" for _, s in snapshots.items()])}\n' for f in fields]
            )) if (fields != ["None"]) else "") +\
            ((f'Aggregated?\n' + "".join(
                [f'\t{f}:\t {"".join(["*" if s._fields[f].isAggregated else "_" for _, s in snapshots.items()])}\n' for f in fields]
            )) if (fields != ["None"]) else "") +\
            f'Particles:\t ' + ', '.join(particles)

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

    def load(self,
             tstep: int) -> None:
        self._snapshots[tstep].load(self._path,
                                    self._flds_fname_template,
                                    self._prtls_fname_template)

    def unload(self,
               tstep: int) -> None:
        self._snapshots[tstep].unload()

    def getRawField(self,
                    tstep: int,
                    f: str) -> NDArray:
        return self._snapshots[tstep].getRawField(f)
