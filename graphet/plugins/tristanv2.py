from typing import Union, Dict, Any, List
from ..plugin import Plugin


class TristanV2(Plugin):
    import h5py
    import numpy as np

    def __init__(
        self,
        path: str = "",
        cfg_fname: Union[str, None] = None,
        **kwargs,
    ):
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
        if self.params and cfg_fname is None:
            raise ValueError("`cfg_fname` must be specified if `params` is True")
        self.fname_templates = {
            "flds": "flds/flds.tot.%05d",
            "prtl": "prtl/prtl.tot.%05d",
            "spec": "spec/spec.tot.%05d",
        }
        self.kwargs = {k: v for k, v in kwargs.items() if k not in parent_kwargs}
        self.files = {
            "flds": None,
            "prtl": None,
            "spec": None,
        }

    def readCoords(self) -> Dict[str, np.ndarray]:
        if self.fields is None:
            return {
                "x": self.kwargs.get("x"),
                "y": self.kwargs.get("y"),
                "z": self.kwargs.get("z"),
            }
        else:
            s0 = self.kwargs.get("first_step", 0)
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

    def readParams(self) -> Union[Dict[str, Any], None]:
        if self.params:
            attrs = {}
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

    def readField(self, field: str, step: int) -> h5py.Dataset:
        if self.fields is None:
            raise ValueError("`fields` cannot be None when calling `readField`")
        if (self.files["flds"] is None) or (step not in self.files["flds"].keys()):
            self.openFieldFiles([step])
        return self.files["flds"][step][field]

    def readParticleKey(self, species: int, key: str, step: int) -> h5py.Dataset:
        if self.particles is None:
            raise ValueError(
                "`particles` cannot be None when calling `readParticleKey`"
            )
        if (self.files["prtl"] is None) or (step not in self.files["prtl"].keys()):
            self.openParticleFiles([step])
        return self.files["prtl"][step][f"{key}_{species}"]

    def readSpectrum(self, spec: str, step: int) -> h5py.Dataset:
        if self.spectra is None:
            raise ValueError("`spectra` cannot be None when calling `readSpectrum`")
        if (self.files["spec"] is None) or (step not in self.files["spec"].keys()):
            self.openSpectrumFiles([step])
        return self.files["spec"][step][spec]

    def rawFieldKeys(self) -> List[str]:
        if self.fields is None:
            return []
        else:
            s0 = self.kwargs.get("first_step", 0)
            self.openFieldFiles([s0])
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
            s0 = self.kwargs.get("first_step", 0)
            self.openSpectrumFiles([s0])
            return [x for x in list(self.files["spec"][s0].keys()) if x.startswith("n")]

    def specBins(self, spec: str) -> Dict[str, np.ndarray]:
        bins = {}
        s0 = self.kwargs.get("first_step", 0)
        self.openSpectrumFiles([s0])
        if spec.startswith("nr"):
            bins["re"] = self.files["spec"][s0]["rbins"][:]
        else:
            bins["e"] = self.files["spec"][s0]["ebins"][:]
            for xyz in "xyz":
                if xyz + "bins" in self.files["spec"][s0].keys():
                    arr = self.files["spec"][s0][xyz + "bins"][:]
                    if len(arr) > 1:
                        bins[xyz] = arr
        return bins

    def prtlKeys(self) -> List[str]:
        import numpy as np

        if self.particles is None:
            return []
        else:
            s0 = self.kwargs.get("first_step", 0)
            self.openParticleFiles([s0])
            return np.unique(
                [k.split("_")[0] for k in list(self.files["prtl"][s0].keys())]
            ).tolist()

    def prtlSpecies(self) -> List[int]:
        import numpy as np

        if self.particles is None:
            return []
        else:
            s0 = self.kwargs.get("first_step", 0)
            self.openParticleFiles([s0])
            return np.unique(
                [int(k.split("_")[1]) for k in list(self.files["prtl"][s0].keys())]
            ).tolist()

    def openH5File(self, data: str, step: int) -> h5py.File:
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
