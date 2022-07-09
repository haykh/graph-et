from typing import List, Union

FnameTemplate = Union[str, None]

def AutoDetectTSteps(path: str,
                     fname_template: FnameTemplate) -> List[int]:
    import os
    import numpy as np
    fname = fname_template.split('%')[0]
    ext = fname_template.split('.')[-1]
    tsteps = []
    try:
        tsteps = np.sort([int(f.replace(fname, '').replace('.' + ext, '')) for f in os.listdir(path) if f.startswith(fname)])
    except Exception as e:
        raise Exception(f"Unable to find tsteps: {e.args}") from e
    return tsteps
    
print (AutoDetectTSteps("/Users/hayk/.tmp/graph-et/graph-et/tests/test_data_2", "dummy%02d.hdf5"))