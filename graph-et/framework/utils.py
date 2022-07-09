from .defs import FnameTemplate
import sys
from types import ModuleType, FunctionType
from gc import get_referents
from typeguard import typechecked
from typing import Any, List
from numpy.typing import NDArray

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
def SizeofFmt(num: int, suffix: str = "B") -> str:
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


@typechecked
def GetSimulationSize(obj: Any) -> int:
    """sum size of object & members."""
    BLACKLIST = type, ModuleType, FunctionType
    if isinstance(obj, BLACKLIST):
        raise TypeError(
            'getsize() does not take argument of type: ' + str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size
