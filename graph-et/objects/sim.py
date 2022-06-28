from typing import Dict, Any, List, Union
from numpy.typing import NDArray
from typeguard import typechecked

FnameTemplate = Union[str, None]

def HandleFname(template: str, tstep: int = None) -> str:
    if '%' in template:
        return template % tstep
    else:
        return template


def CreateFieldKeysFromHdf5(path: str,
                            fname_template: FnameTemplate,
                            tstep: int) -> List[str]:
    import h5py
    with h5py.File(f'{path}/{HandleFname(fname_template, tstep)}', 'r') as f:
        return list(f.keys())


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
        assert self._isLoaded, "Field is not loaded"
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
                 tsteps: List[int] = [0],
                 params: Dict[str, Any] = {}) -> None:
        self._name = name
        self._path = path
        self._params = params
        self._tsteps = tsteps
        self._flds_fname_template = flds_fname_template
        self._prtls_fname_template = prtls_fname_template
        self._snapshots = {
            tstep: Snapshot(path, flds_fname_template, prtls_fname_template, tstep) for tstep in self._tsteps
        }

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
