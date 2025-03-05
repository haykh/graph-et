from typing import Any, List, Dict, Union, Callable
from .utils import array_t


class Plugin:

    def __init__(
        self,
        params: bool = False,
        fields: None | List[str] = ["ALL"],
        particles: None | List[str] = ["ALL"],
        spectra: None | List[str] = ["ALL"],
        coord_transform: None | Dict[str, Callable[[array_t, Any], array_t]] = None,
        origaxes: str = "zyx",
        swapaxes: Union[List[List[int]], None] = None,
    ):
        """
        Plugin base class contains all the information required to properly read the date from a simulation, but does not actually carry the data itself. Child classes must implement the following virtual methods:
        - `readParams`
        - `readCoords`
        - `readField`
        - `readParticleKey`
        - `readSpectrum`
        - `fieldKeys`
        - `prtlKeys`
        - `prtlSpecies`
        - `specKeys`
        - `specBins`
        - `openFieldFiles`
        - `openParticleFiles`
        - `openSpectrumFiles`

        Parameters
        ----------
        `params` : `bool`, optional
            whether to read the simulation parameters (default: `False`)
        `fields` : `Union[None, List[str]]`, optional
            list of fields to read (default: `["ALL"]`)
        `particles` : `Union[None, List[str]]`, optional
            list of particle species to read (default: `["ALL"]`)
        `spectra` : `Union[None, List[str]]`, optional
            list of spectra to read (default: `["ALL"]`)
        `coord_transform` : `Union[None, Dict[str, Callable[[np_Array, Any], np_Array]]]`, optional
            dictionary of coordinate transformations to apply to the coordinates read from the simulation. The keys are the axes to transform, and the values are the transformation functions. The transformation functions take two arguments: the coordinate array and the simulation parameters. (default: `None`)
        `origaxes` : `str`, optional
            the original axis order of the simulation (default: `"zyx"`)
        `swapaxes` : `Union[List[List[int]], None]`, optional
            list of pairs of axes to swap (default: `None`)
        """
        self.params = params
        self.fields = fields
        self.particles = particles
        self.spectra = spectra
        self.origaxes = origaxes
        self.coord_transform = coord_transform
        self.swapaxes = swapaxes
        self.axes = list(self.origaxes)
        self._has_prtl_idx = None
        if self.swapaxes is not None:
            for s in self.swapaxes:
                self.axes[s[0]], self.axes[s[1]] = (
                    self.axes[s[1]],
                    self.axes[s[0]],
                )
        self.axes = "".join(self.axes)

    def coords(self) -> Dict[str, array_t]:
        """
        Read the coordinates from the simulation and apply any coordinate transformations.

        Returns
        -------
        `Dict[str, np_Array]`
            dictionary of coordinates, with the keys being the axes and the values being the coordinate arrays
        """
        coords = self.readCoords()
        ax_mapping = {newax: oldax for oldax, newax in zip(self.origaxes, self.axes)}
        if self.coord_transform is not None:
            params = self.readParams()
            for ax, func in self.coord_transform.items():
                if ax != "t":
                    coords[ax_mapping[ax]] = func(coords[ax_mapping[ax]], params)
        return {newax: coords[oldax] for oldax, newax in zip(self.origaxes, self.axes)}

    def field(self, field: str, step: int) -> array_t:
        """
        Read a field from the simulation at a specific step and return it as an dask array.

        Parameters
        ----------
        `field` : `str`
            the name of the field to read
        `step` : `int`
            the step to read
        Returns
        -------
        `da.Array`
            the field as a dask array
        """
        from dask.array.core import from_array as da_from_array
        from dask.array.routines import swapaxes as da_swapaxes

        oldfield = field + ""
        ax_mapping = {newax: oldax for oldax, newax in zip(self.origaxes, self.axes)}
        params = self.readParams()

        transform: None | Callable = None

        if any(oldfield.endswith(i) for i in ["x", "y", "z"]):
            xyz = oldfield[-1]
            if oldfield[-2] == oldfield[-1]:
                oldfield = oldfield[:-2] + ax_mapping[oldfield[-1]] * 2
                if (self.coord_transform is not None) and (
                    xyz in self.coord_transform.keys()
                ):
                    transform = self.coord_transform[xyz]
            else:
                oldfield = oldfield[:-1] + ax_mapping[oldfield[-1]]

        arr = da_from_array(self.readField(oldfield, step), chunks="auto")
        if self.swapaxes is not None:
            for sw in self.swapaxes:
                arr = da_swapaxes(arr, *sw)

        if transform is not None:
            return transform(arr, params)
        else:
            return arr

    def particleKey(self, sp: int, key: str, step: int) -> array_t:
        """
        Read a particle key from the simulation at a specific step and return it as a dask array.

        Parameters
        ----------
        `sp` : `int`
            the particle species
        `key` : `str`
            the name of the particle key to read
        `step` : `int`
            the step to read

        Returns
        -------
        `da.Array`
            the particle key as a dask array
        """
        from dask.array.core import from_array as da_from_array
        from xarray import DataArray as xr_DataArray
        from numpy import array as np_array

        oldkey = key + ""
        ax_mapping = {newax: oldax for oldax, newax in zip(self.origaxes, self.axes)}
        params = self.readParams()

        transform: None | Callable = None

        if oldkey in ["x", "y", "z"]:
            oldkey = ax_mapping[oldkey]
            if (self.coord_transform is not None) and (
                oldkey in self.coord_transform.keys()
            ):
                transform = self.coord_transform[key]

        idx = self.prtlIndex(sp, step)
        if idx is not None:
            if (self.coord_transform is not None) and (
                "t" in self.coord_transform.keys()
            ):
                t = self.coord_transform["t"](np_array([step]), params)
                assert t is not None, "Time transformation not implemented"
                t = t[0]
            else:
                t = step

            self._has_prtl_idx = True
            da = xr_DataArray(
                self.readParticleKey(sp, oldkey, step),
                coords={"idx": idx, "t": t},
                dims="idx",
            )
        else:
            self._has_prtl_idx = False
            da = da_from_array(self.readParticleKey(sp, oldkey, step), chunks="auto")

        if transform is not None:
            return transform(
                da,
                params,
            )
        else:
            return da

    def prtlIndex(self, sp: int, step: int) -> array_t:
        """
        Return custom particle index used to identify particles in the simulation.

        Parameters
        ----------
        `sp` : `int`
            the particle species
        `step` : `int`
            the step

        Returns
        -------
        `da.Array | None`
            the particle index as a dask array (or none if indexing is not available)
        """
        return None

    def spectrum(self, spec: str, step: int) -> array_t:
        """
        Read a spectrum from the simulation at a specific step and return it as a dask array.

        Parameters
        ----------
        `spec` : `str`
            the name of the spectrum to read
        `step` : `int`
            the step to read

        Returns
        -------
        `da.array`
            the spectrum as a dask array
        """
        from dask.array.core import from_array as da_from_array
        import numpy as np

        arr = self.readSpectrum(spec, step)
        arr = da_from_array(np.squeeze(arr), chunks="auto")
        return arr.reshape(arr.shape[0], -1).sum(axis=1)

    def readParams(self) -> Any:
        """
        Read the simulation parameters.

        Returns
        -------
        `Any`
            the simulation parameters

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("readParams not implemented")

    def readCoords(self) -> Dict[str, array_t]:
        """
        Read the coordinates from the simulation.

        Returns
        -------
        `Dict[str, np_Array]`
            dictionary of coordinates, with the keys being the axes and the values being the coordinate arrays

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("readCoords not implemented")

    def readField(self, field: str, step: int) -> Any:
        """
        Read a field from the simulation.

        Parameters
        ----------
        `field` : `str`
            the name of the field to read
        `step` : `int`
            the step to read

        Returns
        -------
        `Any`
            the field

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("readField not implemented")

    def readSpectrum(self, spec: str, step: int) -> Any:
        """
        Read a spectrum from the simulation.

        Parameters
        ----------
        `spec` : `str`
            the name of the spectrum to read
        `step` : `int`
            the step to read

        Returns
        -------
        `Any`
            the spectrum
        """
        raise NotImplementedError("readSpectrum not implemented")

    def readParticleKey(self, species: int, key: str, step: int) -> Any:
        """
        Read a particle key from the simulation.

        Parameters
        ----------
        `species` : `int`
            the particle species
        `key` : `str`
            the name of the particle key to read
        `step` : `int`
            the step to read

        Returns
        -------
        `Any`
            the particle key
        """
        raise NotImplementedError("readParticleKey not implemented")

    def fieldKeys(self) -> List[str]:
        """
        Get the list of field keys.

        Returns
        -------
        `List[str]`
            the list of field keys

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("fieldKeys not implemented")

    def specKeys(self) -> List[str]:
        """
        Get the list of spectrum keys.

        Returns
        -------
        `List[str]`
            the list of spectrum keys

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("specKeys not implemented")

    def specBins(self, spec: str) -> Dict[str, array_t]:
        """
        Get the bins for a specific spectrum.

        Parameters
        ----------
        `spec` : `str`
            the name of the spectrum

        Returns
        -------
        `Dict[str, np_Array]`
            the bins for the spectrum

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("specBins not implemented")

    def prtlKeys(self, sp: int | None = None) -> List[str]:
        """
        Get the list of particle keys.

        Parameters
        ----------
        `sp` : `int`, optional
            the species to get the particle keys for (default: `None`)

        Returns
        -------
        `List[str]`
            the list of particle keys for species `sp`

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("prtlKeys not implemented")

    def prtlSpecies(self) -> List[int]:
        """
        Get the list of particle species.

        Returns
        -------
        `List[int]`
            the list of particle species

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("prtlSpecies not implemented")

    def openFieldFiles(self, steps: List[int]) -> Any:
        """
        Open the field files.

        Parameters
        ----------
        `steps` : `List[int]`
            the steps to open

        Returns
        -------
        `Any`
            the opened files

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("openFieldFiles not implemented")

    def openParticleFiles(self, steps: List[int]) -> Any:
        """
        Open the particle files.

        Parameters
        ----------
        `steps` : `List[int]`
            the steps to open

        Returns
        -------
        `Any`
            the opened files

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("openParticleFiles not implemented")

    def openSpectrumFiles(self, steps: List[int]) -> Any:
        """
        Open the spectrum files.

        Parameters
        ----------
        `steps` : `List[int]`
            the steps to open

        Returns
        -------
        `Any`
            the opened files

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("openSpectrumFiles not implemented")

    @property
    def has_particle_idx(self) -> bool:
        """
        Check if the plugin has particle index.

        Returns
        -------
        `bool`
            whether the plugin has particle index
        """
        assert self._has_prtl_idx is not None, "Particle index not checked"
        return getattr(self, "_has_prtl_idx", False)
