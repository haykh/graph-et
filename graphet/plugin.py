from typing import Any, List, Dict, Union, Callable


class Plugin:
    import numpy as np
    import xarray as xr

    def __init__(
        self,
        params: bool = False,
        fields: Union[None, List[str]] = ["ALL"],
        particles: Union[None, List[str]] = ["ALL"],
        spectra: Union[None, List[str]] = ["ALL"],
        coord_transform: Union[
            None, Dict[str, Callable[[np.ndarray, Any], np.ndarray]]
        ] = None,
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
        `coord_transform` : `Union[None, Dict[str, Callable[[np.ndarray, Any], np.ndarray]]]`, optional
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
        if self.swapaxes is not None:
            for s in self.swapaxes:
                self.axes[s[0]], self.axes[s[1]] = (
                    self.axes[s[1]],
                    self.axes[s[0]],
                )
        self.axes = "".join(self.axes)

    def coords(self) -> Dict[str, np.ndarray]:
        """
        Read the coordinates from the simulation and apply any coordinate transformations.

        Returns
        -------
        `Dict[str, np.ndarray]`
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

    def field(self, field: str, steps: List[int]) -> xr.DataArray:
        """
        Read a field from the simulation and return it as an xarray DataArray.

        Parameters
        ----------
        `field` : `str`
            the name of the field to read
        `steps` : `List[int]`
            the steps to read
        Returns
        -------
        `xr.DataArray`
            the field as an xarray DataArray
        """
        import dask
        import dask.array as da
        import numpy as np
        import xarray as xr

        coord_map = {old: new for old, new in zip(self.origaxes, self.axes)}
        for xyz in ["x", "y", "z"]:
            if xyz in field:
                field = field.replace("x", coord_map["x"])
                break
        coords = self.coords()
        dask_arrays = []
        with dask.config.set(**{"array.slicing.split_large_chunks": True}):
            for step in steps:
                fld = da.from_array(self.readField(field, step), chunks="auto")
                dask_arrays.append(fld)
        times = np.array(steps).astype(float)
        if (self.coord_transform is not None) and ("t" in self.coord_transform.keys()):
            params = self.readParams()
            times = self.coord_transform["t"](times, params)
        return xr.DataArray(
            da.stack(dask_arrays, axis=0),
            dims=["t", *list(coords.keys())],
            name=field,
            coords={
                "t": times,
                **coords,
            },
        )

    def particleKey(self, spec: int, key: str, steps: List[int]) -> xr.DataArray:
        """
        Read a particle key from the simulation and return it as an xarray DataArray.

        Parameters
        ----------
        `spec` : `int`
            the particle species
        `key` : `str`
            the name of the particle key to read
        `steps` : `List[int]`
            the steps to read

        Returns
        -------
        `xr.DataArray`
            the particle key as an xarray DataArray
        """
        import dask.array as da
        import numpy as np
        import xarray as xr

        def list_to_ragged(arr):
            max_len = np.max([len(a) for a in arr])
            return [da.concatenate([a, da.full(max_len - len(a), np.nan)]) for a in arr]

        dask_arrays = []
        for step in steps:
            dask_arrays.append(self.readParticleKey(spec, key, step))
        data = list_to_ragged(dask_arrays)
        times = np.array(steps).astype(float)
        if (self.coord_transform is not None) and ("t" in self.coord_transform.keys()):
            params = self.readParams()
            times = self.coord_transform["t"](times, params)
        return xr.DataArray(da.stack(data), dims=["t", "id"], coords={"t": times})

    def spectrum(self, spec: str, steps: List[int]) -> xr.DataArray:
        """
        Read a spectrum from the simulation and return it as an xarray DataArray.

        Parameters
        ----------
        `spec` : `str`
            the name of the spectrum to read
        `steps` : `List[int]`
            the steps to read

        Returns
        -------
        `xr.DataArray`
            the spectrum as an xarray DataArray
        """
        import dask.array as da
        import numpy as np
        import xarray as xr

        bns = self.specBins(spec)
        dask_arrays = []
        for step in steps:
            sp = da.from_array(np.squeeze(self.readSpectrum(spec, step)), chunks="auto")
            dask_arrays.append(sp)
        times = np.array(steps).astype(float)
        if (self.coord_transform is not None) and ("t" in self.coord_transform.keys()):
            params = self.readParams()
            times = self.coord_transform["t"](times, params)

        return xr.DataArray(
            da.stack(dask_arrays, axis=0),
            dims=["t", *list(bns.keys())],
            name=spec,
            coords={"t": times, **bns},
        )

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

    def readCoords(self) -> Dict[str, np.ndarray]:
        """
        Read the coordinates from the simulation.

        Returns
        -------
        `Dict[str, np.ndarray]`
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

    def specBins(self, spec: str) -> Dict[str, np.ndarray]:
        """
        Get the bins for a specific spectrum.

        Parameters
        ----------
        `spec` : `str`
            the name of the spectrum

        Returns
        -------
        `Dict[str, np.ndarray]`
            the bins for the spectrum

        Raises
        ------
        `NotImplementedError`
            if not implemented in the child class
        """
        raise NotImplementedError("specBins not implemented")

    def prtlKeys(self) -> List[str]:
        """
        Get the list of particle keys.

        Returns
        -------
        `List[str]`
            the list of particle keys

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
