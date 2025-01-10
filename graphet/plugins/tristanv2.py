from typing import Dict, Any, List
from ..plugin import Plugin
from ..utils import array_t
from h5py import Dataset as h5_Ds, File as h5_File


class TristanV2(Plugin):
    def __init__(
        self,
        path: str = "",
        cfg_fname: str | None = None,
        **kwargs,
    ):
        self.first_step = kwargs.get("first_step", kwargs.get("steps", [0])[0])
        parent_kwargs = [
            "params",
            "fields",
            "particles",
            "spectra",
            "coord_transform",
            "origaxes",
            "swapaxes",
        ]
        super().__init__(**{k: v for k, v in kwargs.items() if k in parent_kwargs})
        self.path = path
        self.cfg_fname = cfg_fname
        if not self.cfg_fname is None:
            self.params = True
        else:
            self.params = False
        self.fname_templates = {
            "flds": "flds/flds.tot.%05d",
            "prtl": "prtl/prtl.tot.%05d",
            "spec": "spec/spec.tot.%05d",
        }

        self.kwargs = {k: v for k, v in kwargs.items() if k not in parent_kwargs}
        self.files: Dict[str, Dict[int, h5_File] | None] = {
            "flds": None,
            "prtl": None,
            "spec": None,
        }

    def readCoords(self) -> Dict[str, array_t]:
        if self.fields is None:
            return {
                "x": self.kwargs.get("x"),
                "y": self.kwargs.get("y"),
                "z": self.kwargs.get("z"),
            }
        else:
            s0 = self.first_step
            xx, yy, zz = (
                self.readField("xx", s0),
                self.readField("yy", s0),
                self.readField("zz", s0),
            )
            return {
                "x": xx[:][0, 0, :],
                "y": yy[:][0, :, 0],
                "z": zz[:][:, 0, 0],
            }

    def readParams(self) -> Dict[str, Any] | None:
        if self.params:
            attrs = {}
            assert self.cfg_fname is not None, "cfg_fname not provided"
            with open(self.cfg_fname) as f:
                attrs_raw = f.readlines()
            block = None
            for r in attrs_raw:
                r = r.strip()
                if r.startswith("<"):
                    block = r[1:-1]
                elif r.startswith("#"):
                    continue
                elif "=" in r:
                    attr, val = r.split("=", 1)
                    attr = attr.strip()
                    if "#" in val:
                        val = val[: val.find("#")]
                    val = val.strip()
                    if "." in val or "e" in val:
                        val = float(val)
                    else:
                        val = int(val)
                    attrs[f"{block}:{attr}"] = val
            return attrs
        else:
            return None

    def readField(self, field: str, step: int) -> h5_Ds:
        if self.fields is None:
            raise ValueError("`fields` cannot be None when calling `readField`")
        if (self.files["flds"] is None) or (step not in self.files["flds"].keys()):
            self.openFieldFiles([step])
        assert self.files["flds"] is not None, "Field files not opened"
        ds = self.files["flds"][step][field]
        assert isinstance(ds, h5_Ds), f"Field {field} not found in step {step}"
        return ds

    def readParticleKey(self, species: int, key: str, step: int) -> h5_Ds:
        if self.particles is None:
            raise ValueError(
                "`particles` cannot be None when calling `readParticleKey`"
            )
        if (self.files["prtl"] is None) or (step not in self.files["prtl"].keys()):
            self.openParticleFiles([step])
        assert self.files["prtl"] is not None, "Particle files not opened"
        ds = self.files["prtl"][step][f"{key}_{species}"]
        assert isinstance(ds, h5_Ds), f"Particle key {key} not found in step {step}"
        return ds

    def readSpectrum(self, spec: str, step: int) -> h5_Ds:
        if self.spectra is None:
            raise ValueError("`spectra` cannot be None when calling `readSpectrum`")
        if (self.files["spec"] is None) or (step not in self.files["spec"].keys()):
            self.openSpectrumFiles([step])
        assert self.files["spec"] is not None, "Spectrum files not opened"
        ds = self.files["spec"][step][spec]
        assert isinstance(ds, h5_Ds), f"Spectrum {spec} not found in step {step}"
        return ds

    def rawFieldKeys(self) -> List[str]:
        if self.fields is None:
            return []
        else:
            s0 = self.first_step
            self.openFieldFiles([s0])
            assert self.files["flds"] is not None, "Field files not opened"
            return list(self.files["flds"][s0].keys())

    def fieldKeys(self) -> List[str]:
        if self.fields is None:
            return []
        elif "ALL" in self.fields:
            if len(self.fields) != 1:
                raise NotImplementedError("fieldKeys not implemented for custom fields")
            return self.rawFieldKeys()
        else:
            raise NotImplementedError("fieldKeys not implemented for custom fields")

    def specKeys(self) -> List[str]:
        if self.spectra is None:
            return []
        else:
            s0 = self.first_step
            self.openSpectrumFiles([s0])
            assert self.files["spec"] is not None, "Spectrum files not opened"
            return [x for x in list(self.files["spec"][s0].keys()) if x.startswith("n")]

    def specBins(self, spec: str) -> Dict[str, array_t]:
        bins = {}
        s0 = self.first_step
        self.openSpectrumFiles([s0])
        if spec.startswith("nr"):
            assert self.files["spec"] is not None, "Spectrum files not opened"
            rbins_ds = self.files["spec"][s0]["rbins"]
            assert isinstance(rbins_ds, h5_Ds), "Radial bins not found"
            bins["re"] = rbins_ds[:]
        else:
            assert self.files["spec"] is not None, "Spectrum files not opened"
            ebins_ds = self.files["spec"][s0]["ebins"]
            assert isinstance(ebins_ds, h5_Ds), "Energy bins not found"
            bins["e"] = ebins_ds[:]
            # for xyz in "xyz":
            #     if xyz + "bins" in self.files["spec"][s0].keys():
            #         arr = self.files["spec"][s0][xyz + "bins"][:]
            #         if len(arr) > 1:
            #             bins[xyz] = arr

        return bins

    def prtlKeys(self, sp: int | None = None) -> List[str]:
        import numpy as np

        if self.particles is None:
            return []
        else:
            s0 = self.first_step
            self.openParticleFiles([s0])
            assert self.files["prtl"] is not None, "Particle files not opened"
            return [
                str(k)
                for k in np.unique(
                    [
                        k.split("_")[0]
                        for k in self.files["prtl"][s0].keys()
                        if k.endswith(f"_{sp}")
                    ]
                )
            ]

    def prtlIndex(self, sp: int, step: int) -> array_t:
        from dask.array.routines import ravel_multi_index as da_ravel_multi_index
        from dask.array.core import from_array as da_from_array
        from numpy import int64

        return da_ravel_multi_index(
            [
                da_from_array(self.readParticleKey(sp, "ind", step)),
                da_from_array(self.readParticleKey(sp, "proc", step)),
            ],
            [100000000, 100000000],
        )

    def prtlSpecies(self) -> List[int]:
        import numpy as np

        if self.particles is None:
            return []
        else:
            s0 = self.first_step
            self.openParticleFiles([s0])
            assert self.files["prtl"] is not None, "Particle files not opened"
            return [
                int(k)
                for k in np.unique(
                    [int(k.split("_")[1]) for k in list(self.files["prtl"][s0].keys())]
                )
            ]

    def openH5File(self, data: str, step: int) -> h5_File:
        import h5py
        import os

        return h5py.File(
            os.path.join(self.path, self.fname_templates[data] % step), "r"
        )

    def openFieldFiles(self, steps: List[int]):
        if self.fields:
            self.files["flds"] = {step: self.openH5File("flds", step) for step in steps}
        else:
            self.files["flds"] = None

    def openParticleFiles(self, steps: List[int]):
        if self.particles:
            self.files["prtl"] = {step: self.openH5File("prtl", step) for step in steps}
        else:
            self.files["prtl"] = None

    def openSpectrumFiles(self, steps: List[int]):
        if self.spectra:
            self.files["spec"] = {step: self.openH5File("spec", step) for step in steps}
        else:
            self.files["spec"] = None
