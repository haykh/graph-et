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
        swapaxes=[(0, 1), (2, 1)],
        cfg_fname=f"{fdir}/tests/data/tristanv2/input.cfg",
    )
    assert d.params is not None
    assert d.params["blockA:paramA1"] == 1.23
    assert d.params["blockA:paramA2"] == 2
    assert d.params["blockB:paramB1"] == 345
    assert d.params["blockB:paramB2"] == 4.56
    # "zyx" -> "yxz"
    # test fields
    assert sorted(list(d.fields.variables.keys())) == sorted(
        [
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
    )

    assert d.fields.t.shape == (5,)
    assert d.fields.z.shape == (20,)
    assert d.fields.y.shape == (25,)
    assert d.fields.x.shape == (30,)
    assert np.all(d.fields.x.values == np.arange(30))
    assert np.all(d.fields.y.values == np.arange(25))
    assert np.all(d.fields.z.values == np.arange(20))

    assert np.all(d.fields.xx.sel(x=10).values == 10)
    assert np.all(d.fields.yy.sel(y=10).values == 10)
    assert np.all(d.fields.zz.sel(z=10).values == 10)

    assert np.all(d.fields.xx.sel(y=15, z=5).values == np.arange(30))
    assert np.all(d.fields.yy.sel(x=15, z=5).values == np.arange(25))
    assert np.all(d.fields.zz.sel(x=15, y=5).values == np.arange(20))

    for time in d.fields.t.values:
        xs = d.fields.xx.sel(t=time).values
        ys = d.fields.yy.sel(t=time).values
        zs = d.fields.zz.sel(t=time).values
        assert np.all(
            np.isclose(
                d.fields.bx.sel(t=time).values,
                np.cos(zs / 10 + time)
                * np.sin(xs / 10 + time)
                * np.cos(ys / 10 + time),
            )
        )
        assert np.all(
            np.isclose(
                d.fields.by.sel(t=time).values,
                np.cos(zs / 10 + time)
                * np.cos(xs / 10 + time)
                * np.sin(ys / 10 + time),
            )
        )
        assert np.all(
            np.isclose(
                d.fields.bz.sel(t=time).values,
                np.sin(zs / 10 + time)
                * np.cos(xs / 10 + time)
                * np.cos(ys / 10 + time),
            )
        )

    for f in ["xx", "yy", "zz", "bx", "by", "bz"]:
        assert d.fields[f].shape == (5, 30, 20, 25)

    # test particles
    assert list(d.particles.keys()) == [1, 2, 3, 4]
    for i in range(1, 5):
        assert np.all(d.particles[i].t == np.arange(5))

        print(i, d.particles[i].variables.keys())
    assert list(d.particles[2].variables.keys()) == [
        "t",
        "idx",
        "ind",
        "proc",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
    ]
    assert list(d.particles[3].variables.keys()) == [
        "t",
        "idx",
        "ind",
        "proc",
        "x",
        "y",
        "z",
    ]

    npart = [60, 77, 79, 87]
    for i in range(1, 5):
        for v in ["u", "v", "w", "x", "y", "z"] if i % 2 == 0 else ["x", "y", "z"]:
            assert d.particles[i][v].shape == (5, npart[i - 1])

    # test spectra
    assert list(d.spectra.variables.keys()) == ["t", "e", "n1", "n2", "n3", "n4"]
    assert d.spectra.t.shape == (5,)

    ebins = np.logspace(-2, 2, 101)
    ebins_mid = (ebins[1:] + ebins[:-1]) / 2

    assert np.all(np.isclose(d.spectra.e, ebins_mid))
    for i in range(1, 5):
        assert d.spectra[f"n{i}"].shape == (5, 100)
