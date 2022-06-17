from typing import Dict, Any, List, Callable
from numpy.typing import NDArray
from typeguard import typechecked

LoadField = Callable[[str, int], NDArray]

@typechecked
class Field:
    def __init__(self, label: str, loadField: LoadField, tstep: int = 0) -> None:
        self._isLoaded = False
        self._isAggregated = False
        self._loadField = loadField
        self._label = label
        self._data = None
        self._agg = None
        self._tstep = tstep

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

    def load(self) -> None:
        try:
            self._data = self._loadField(self._label, self._tstep)
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
        
    # !TODO:
    def describe(self) -> None:
        pass


@typechecked
class Snapshot:
    def __init__(self, fields: List[str], loadFields: LoadField, tstep: int = 0) -> None:
        self._tstep = tstep
        self._fields = {}
        self._spectra = {}
        self._particles = {}
        for f in fields:
            self._fields[f] = Field(f, loadFields, tstep)

    @property
    def tstep(self) -> int:
        return self._tstep

    def load(self, f: str) -> None:
        self._fields[f].load()

    def unload(self, f: str) -> None:
        self._fields[f].unload()

    def getRawField(self, f: str) -> NDArray:
        return self._fields[f].data


@typechecked
class Simulation:
    def __init__(self, name: str, fields: List[str], loadFields: LoadField, tsteps: List[int] = [0], params: Dict[str, Any] = {}) -> None:
        self._name = name
        self._params = params
        self._tsteps = tsteps
        self._snapshots = {
            tstep: Snapshot(fields, loadFields, tstep) for tstep in self._tsteps
        }

    @property
    def params(self) -> Dict[str, Any]:
        return self._params

    @property
    def name(self) -> str:
        return self._name

    @property
    def tsteps(self) -> List[int]:
        return self._tsteps

    def load(self, tstep: int, f: str) -> None:
        self._snapshots[tstep].load(f)

    def unload(self, tstep: int, f: str) -> None:
        self._snapshots[tstep].unload(f)

    def getRawField(self, tstep: int, f: str) -> NDArray:
        return self._snapshots[tstep].getRawField(f)
