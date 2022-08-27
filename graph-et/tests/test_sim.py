import src.data.sim as nvsim


def test_simulation_class() -> None:
    import os
    path = f'{os.path.dirname(os.path.realpath(__file__))}/test_data'
    test_sim = nvsim.Simulation("test_simple", path,
                                flds_fname="dummy%02d.hdf5")
    assert test_sim.name == "test_simple"
    assert test_sim.tsteps == list(range(10))
    test_sim.snapshots[5].load()
    assert test_sim.snapshots[5].loaded
    test_sim.snapshots[5].aggregate(32, 32)
    assert test_sim.snapshots[5].aggregated
    test_sim.snapshots[5].unload()
    assert not test_sim.snapshots[5].loaded
    test_sim.snapshots[5].unaggregate()
    assert not test_sim.snapshots[5].aggregated

# def test_fields_load() -> None:
#     import os
#     path = f'{os.path.dirname(os.path.realpath(__file__))}/test_data_1'
#     test_sim = nvsim.Simulation("test_load", path,
#                                 flds_fname_template="dummy_%05d.hdf5",
#                                 tsteps=[23, 24]
#                                 )
#     assert test_sim.tsteps == [23, 24]
#     assert all([["ex{i}" in test_sim._snapshots[j]._fields
#                  for i in range(1, 4)]
#                for j in range(23, 25)])
#     test_sim.load(23)
#     assert all(
#         [test_sim._snapshots[23]._fields[f"ex{i}"].isLoaded for i in [1, 2]])
#     assert test_sim.getRawField(23, "ex1")[4] == 0.7162887942105369
#     assert test_sim.getRawField(23, "ex2")[12] == 0.13346133480035838
#     test_sim.unload(23)
#     assert all(
#         [not test_sim._snapshots[23]._fields[f"ex{i}"].isLoaded for i in [1, 2]])

#     test_sim.load(24)
#     assert all(
#         [test_sim._snapshots[24]._fields[f"ex{i}"].isLoaded for i in [1, 3]])
#     assert test_sim.getRawField(24, "ex1")[4] == 0.1828261253481539
#     assert test_sim.getRawField(24, "ex3")[65] == 0.5783858243351494
#     test_sim.unload(24)
#     assert all(
#         [not test_sim._snapshots[24]._fields[f"ex{i}"].isLoaded for i in [1, 3]])

# def test_data_container() -> None:
#     import os
#     path = f'{os.path.dirname(os.path.realpath(__file__))}/test_data_2'
#     ex1 = nvsim.LazyContainer(lambda: nvsim.LoadHdf5Field(
#         "arr1", path, "dummy%02d.hdf5", 0))
#     assert ex1.data is None
#     ex1.load()
#     assert ex1.data is not None
#     assert (ex1.loaded)
#     assert (ex1.data[2][3] == -2.9372549019607845)
#     ex1.unload()
#     assert ex1.data is None
#     assert not (ex1.loaded)
