def test_tristanv2_plugin():
    from graphet.plugins import TristanV2
    from graphet import Data
    import numpy as np
    import os

    # get directory of current file
    fdir = os.path.dirname(os.path.abspath(__file__))
    d = Data(
        TristanV2,
        steps=range(5),
        path=f"{fdir}/tests/data/tristanv2/",
        first_step=0,
    )
    # test fields
    assert list(d.fields.variables.keys()) == [
        "t",
        "z",
        "y",
        "x",
        "bx",
        "by",
        "bz",
        "xx",
        "yy",
        "zz",
    ]

    assert d.fields.t.shape == (5,)
    assert d.fields.z.shape == (25,)
    assert d.fields.y.shape == (30,)
    assert d.fields.x.shape == (20,)
    assert np.all(d.fields.z.values == np.arange(25))
    assert np.all(d.fields.y.values == np.arange(30))
    assert np.all(d.fields.x.values == np.arange(20))

    assert np.all(d.fields.xx.sel(x=10).values == 10)
    assert np.all(d.fields.yy.sel(y=10).values == 10)
    assert np.all(d.fields.zz.sel(z=10).values == 10)

    for f in ["xx", "yy", "zz", "bx", "by", "bz"]:
        assert d.fields[f].shape == (5, 25, 30, 20)

    # test particles
    assert list(d.particles.keys()) == [1, 2, 3, 4]
    for i in range(1, 5):
        assert np.all(d.particles[i].t == np.arange(5))

    assert list(d.particles[2].variables.keys()) == ["t", "u", "v", "w", "x", "y", "z"]
    assert list(d.particles[3].variables.keys()) == ["t", "x", "y", "z"]

    npart = [60, 77, 79, 87]
    for i in range(1, 5):
        for v in ["u", "v", "w", "x", "y", "z"] if i % 2 == 0 else ["x", "y", "z"]:
            assert d.particles[i][v].shape == (5, npart[i - 1])

    # test spectra
    assert list(d.spectra.variables.keys()) == ["t", "e", "n1", "n2", "n3", "n4"]
    assert d.spectra.t.shape == (5,)

    ebins = np.logspace(-2, 2, 101)
    ebins_mid = (ebins[1:] + ebins[:-1]) / 2

    assert np.all(d.spectra.e == ebins_mid)
    for i in range(1, 5):
        assert d.spectra[f"n{i}"].shape == (5, 100)
