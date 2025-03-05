import h5py
import numpy as np
import os

path = "./"

rng = np.random.default_rng(1234)

xs = np.arange(0, 20)
ys = np.arange(0, 30)
zs = np.arange(0, 25)
xs, ys, zs = np.meshgrid(xs, ys, zs, indexing="ij")

# fields
for time in range(5):
    bxs = np.sin(xs / 10 + time) * np.cos(ys / 10 + time) * np.cos(zs / 10 + time)
    bys = np.cos(xs / 10 + time) * np.sin(ys / 10 + time) * np.cos(zs / 10 + time)
    bzs = np.cos(xs / 10 + time) * np.cos(ys / 10 + time) * np.sin(zs / 10 + time)
    dens = np.exp(
        -((xs - 10 + time) ** 2) / 25
        - (ys - 15 + time) ** 2 / 25
        - (zs - 10 - time) ** 2 / 30
    )
    fname = f"{path}tristanv2/flds/flds.tot.{time:05d}"
    if os.path.exists(fname):
        os.remove(fname)
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    hf = h5py.File(fname, "w")
    hf.create_dataset("xx", data=xs.T)
    hf.create_dataset("yy", data=ys.T)
    hf.create_dataset("zz", data=zs.T)
    hf.create_dataset("bx", data=bxs.T)
    hf.create_dataset("by", data=bys.T)
    hf.create_dataset("bz", data=bzs.T)
    hf.close()

for time in range(5):
    fname = f"{path}tristanv2/prtl/prtl.tot.{time:05d}"
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    if os.path.exists(fname):
        os.remove(fname)
    hf = h5py.File(fname, "w")
    hf.close()

    fname = f"{path}tristanv2/spec/spec.tot.{time:05d}"
    if os.path.exists(fname):
        os.remove(fname)
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    hf = h5py.File(fname, "w")
    hf.close()

ebins = np.logspace(-2, 2, 101)
ebins_mid = (ebins[1:] + ebins[:-1]) / 2

for time in range(5):
    fname = f"{path}tristanv2/spec/spec.tot.{time:05d}"
    hf = h5py.File(fname, "a")
    hf.create_dataset("ebins", data=ebins_mid)


for s in range(1, 5):
    n = int(rng.normal() * 20 + 100)
    xs = rng.random(n) * 20
    ys = rng.random(n) * 30
    zs = rng.random(n) * 25
    uxs = rng.random(n) * 2.0 - 1.0
    uys = rng.random(n) * 2.0 - 1.0
    uzs = rng.random(n) * 2.0 - 1.0
    inds = np.arange(n)
    procs = np.ones_like(inds)
    for time in range(5):
        gammas = np.sqrt(1 + uxs**2 + uys**2 + uzs**2)
        xs += uxs / gammas
        ys += uys / gammas
        zs += uzs / gammas
        uxs += rng.random(len(uxs)) * 2.0 - 1.0
        uys += rng.random(len(uys)) * 2.0 - 1.0
        uzs += rng.random(len(uzs)) * 2.0 - 1.0
        mask = (xs > 0) & (xs < 20) & (ys > 0) & (ys < 30) & (zs > 0) & (zs < 25)
        xs = xs[mask]
        ys = ys[mask]
        zs = zs[mask]
        uxs = uxs[mask]
        uys = uys[mask]
        uzs = uzs[mask]
        inds = inds[mask]
        procs = procs[mask]
        fname = f"{path}tristanv2/prtl/prtl.tot.{time:05d}"
        hf = h5py.File(fname, "a")
        hf.create_dataset(f"x_{s}", data=xs)
        hf.create_dataset(f"y_{s}", data=ys)
        hf.create_dataset(f"z_{s}", data=zs)
        if s % 2 == 0:
            # only write velocity for even species
            hf.create_dataset(f"u_{s}", data=uxs)
            hf.create_dataset(f"v_{s}", data=uys)
            hf.create_dataset(f"w_{s}", data=uzs)
        hf.create_dataset(f"ind_{s}", data=inds)
        hf.create_dataset(f"proc_{s}", data=procs)
        hf.close()

        fname = f"{path}tristanv2/spec/spec.tot.{time:05d}"
        hf = h5py.File(fname, "a")
        hist, _ = np.histogram(gammas - 1, bins=ebins)
        hf.create_dataset(f"n{s}", data=hist)
        hf.close()
