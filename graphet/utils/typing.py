from numpy.typing import NDArray as np_Array
from dask.array.core import Array as da_Array
from xarray import DataArray as xr_DataArray

array_t = np_Array | da_Array | xr_DataArray | None
