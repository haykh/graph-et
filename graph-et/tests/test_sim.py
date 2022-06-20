import objects.sim as nvsim


def test_simulation_class() -> None:
    import numpy as np
    test_sim = nvsim.Simulation("test_simple",
                                ["ex1"],
                                lambda f, t: np.array([])
                                )
    assert test_sim.name == "test_simple"
    assert test_sim.tsteps == [0]
    assert "ex1" in test_sim._snapshots[0]._fields
    test_sim.load(0, "ex1")
    assert test_sim._snapshots[0]._fields["ex1"].isLoaded
    test_sim.unload(0, "ex1")
    assert not test_sim._snapshots[0]._fields["ex1"].isLoaded


def test_fields_load() -> None:
    import numpy as np

    def load_field(field: str, tstep: int) -> np.ndarray:
        import h5py
        import os
        fname = f'{os.path.dirname(os.path.realpath(__file__))}/dummy_{tstep:05d}.hdf5'
        with h5py.File(fname, 'r') as f:
            return f[field][:]
    test_sim = nvsim.Simulation("test_load",
                                ["ex1", "ex2", "ex3"],
                                load_field,
                                [23, 24]
                                )
    assert test_sim.tsteps == [23, 24]
    assert all([["ex{i}" in test_sim._snapshots[j]._fields
                 for i in range(1, 4)]
               for j in range(23, 25)])
    test_sim.load(23, "ex1")
    test_sim.load(23, "ex2")
    assert all(
        [test_sim._snapshots[23]._fields[f"ex{i}"].isLoaded for i in [1, 2]])
    assert test_sim.getRawField(23, "ex1")[4] == 0.7162887942105369
    assert test_sim.getRawField(23, "ex2")[12] == 0.13346133480035838
    test_sim.unload(23, "ex1")
    test_sim.unload(23, "ex2")
    assert all(
        [not test_sim._snapshots[23]._fields[f"ex{i}"].isLoaded for i in [1, 2]])

    test_sim.load(24, "ex1")
    test_sim.load(24, "ex3")
    assert all(
        [test_sim._snapshots[24]._fields[f"ex{i}"].isLoaded for i in [1, 3]])
    assert test_sim.getRawField(24, "ex1")[4] == 0.1828261253481539
    assert test_sim.getRawField(24, "ex3")[65] == 0.5783858243351494
    test_sim.unload(24, "ex1")
    test_sim.unload(24, "ex3")
    assert all(
        [not test_sim._snapshots[24]._fields[f"ex{i}"].isLoaded for i in [1, 3]])
