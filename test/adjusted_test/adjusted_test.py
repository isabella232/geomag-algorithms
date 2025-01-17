import json

import numpy as np
from numpy.testing import assert_equal, assert_array_almost_equal
from obspy.core import UTCDateTime
import pytest

from geomagio.adjusted import AdjustedMatrix
from geomagio.adjusted.Affine import Affine, get_epochs
from geomagio.adjusted.transform import (
    LeastSq,
    QRFactorization,
    Rescale3D,
    RotationTranslationXY,
    SVD,
    ShearYZ,
    TranslateOrigins,
    ZRotationHscale,
    TranslateOrigins,
    ZRotationHscaleZbaseline,
    ZRotationShear,
)
from test.residual_test.residual_test import (
    get_json_readings,
    get_spreadsheet_directory_readings,
)


def format_result(result) -> dict:
    Ms = []
    for M in result:
        m = []
        for row in M:
            m.append(list(row))
        Ms.append(m)
    return Ms


def get_excpected_matrices(observatory, key):
    with open(f"etc/adjusted/{observatory}_expected.json", "r") as file:
        expected = json.load(file)
    return expected[key]


def get_expected_synthetic_result(key):
    with open("etc/adjusted/synthetic.json") as file:
        expected = json.load(file)
    return expected["results"][key]


def get_sythetic_variables():
    with open("etc/adjusted/synthetic.json") as file:
        data = json.load(file)
    variables = data["variables"]
    ordinates = np.array([variables["h_ord"], variables["e_ord"], variables["z_ord"]])
    absolutes = np.array([variables["x_abs"], variables["y_abs"], variables["z_abs"]])
    weights = np.arange(0, len(ordinates[0]))
    return ordinates, absolutes, weights


def test_BOU201911202001_infinite_one_interval():
    readings = get_json_readings("etc/residual/BOU20191001.json")
    result = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
        transforms=[
            RotationTranslationXY(memory=np.inf, acausal=True),
            TranslateOrigins(memory=np.inf, acausal=True),
        ],
        update_interval=None,
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    expected_matrices = get_excpected_matrices("BOU", "inf_one_interval")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), 1)


def test_BOU201911202001_infinite_weekly():
    readings = get_json_readings("etc/residual/BOU20191001.json")

    starttime = UTCDateTime("2019-11-01T00:00:00Z")
    endtime = UTCDateTime("2020-01-31T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="BOU",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
        transforms=[
            RotationTranslationXY(memory=np.inf, acausal=True),
            TranslateOrigins(memory=np.inf, acausal=True),
        ],
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    expected_matrices = get_excpected_matrices("BOU", "inf_weekly")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_BOU201911202001_invalid_readings():
    starttime = UTCDateTime("2019-11-01T00:00:00Z")
    with pytest.raises(
        ValueError, match=f"No valid observations for: {starttime}"
    ) as error:
        readings = []
        result = Affine(
            observatory="BOU",
            starttime=starttime,
            endtime=UTCDateTime("2020-01-31T23:59:00Z"),
            transforms=[
                RotationTranslationXY(memory=np.inf, acausal=True),
                TranslateOrigins(memory=np.inf, acausal=True),
            ],
            update_interval=None,
        ).calculate(
            readings=readings,
        )


def test_BOU201911202001_short_acausal():
    readings = get_json_readings("etc/residual/BOU20191001.json")

    starttime = UTCDateTime("2019-11-01T00:00:00Z")
    endtime = UTCDateTime("2020-01-31T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="BOU",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
        transforms=[
            RotationTranslationXY(memory=(86400 * 100), acausal=True),
            TranslateOrigins(memory=(86400 * 10), acausal=True),
        ],
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    expected_matrices = get_excpected_matrices("BOU", "short_acausal")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_BOU201911202001_short_causal():
    readings = get_json_readings("etc/residual/BOU20191001.json")

    starttime = UTCDateTime("2019-11-01T00:00:00Z")
    endtime = UTCDateTime("2020-01-31T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="BOU",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
        transforms=[
            RotationTranslationXY(memory=(86400 * 100), acausal=False),
            TranslateOrigins(memory=(86400 * 10), acausal=False),
        ],
    ).calculate(readings=readings)

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    expected_matrices = get_excpected_matrices("BOU", "short_causal")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_CMO2015_infinite_one_interval():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/residual/Caldata/",
    )

    assert len(readings) == 146

    result = Affine(
        observatory="CMO",
        starttime=UTCDateTime("2015-02-01T00:00:00Z"),
        endtime=UTCDateTime("2015-11-27T23:59:00Z"),
        transforms=[
            RotationTranslationXY(memory=np.inf, acausal=True),
            TranslateOrigins(memory=np.inf, acausal=True),
        ],
        acausal=True,
        update_interval=None,
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    expected_matrices = get_excpected_matrices("CMO", "inf_one_interval")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )

    assert_equal(len(matrices), 1)


def test_CMO2015_infinite_weekly():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/residual/Caldata/",
    )
    assert len(readings) == 146

    starttime = UTCDateTime("2015-02-01T00:00:00Z")
    endtime = UTCDateTime("2015-11-27T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="CMO",
        starttime=starttime,
        endtime=endtime,
        transforms=[
            RotationTranslationXY(memory=np.inf, acausal=True),
            TranslateOrigins(memory=np.inf, acausal=True),
        ],
        update_interval=update_interval,
        acausal=True,
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    expected_matrices = get_excpected_matrices("CMO", "inf_weekly")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_CMO2015_short_acausal():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/residual/Caldata/",
    )
    assert len(readings) == 146

    starttime = UTCDateTime("2015-02-01T00:00:00Z")
    endtime = UTCDateTime("2015-11-27T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="CMO",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
        transforms=[
            RotationTranslationXY(memory=(86400 * 100), acausal=True),
            TranslateOrigins(memory=(86400 * 10), acausal=True),
        ],
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    expected_matrices = get_excpected_matrices("CMO", "short_acausal")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_CMO2015_short_causal():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/residual/Caldata/",
    )
    assert len(readings) == 146

    starttime = UTCDateTime("2015-02-01T00:00:00Z")
    endtime = UTCDateTime("2015-11-27T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="CMO",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
        transforms=[
            RotationTranslationXY(memory=(86400 * 100), acausal=False),
            TranslateOrigins(memory=(86400 * 10), acausal=False),
        ],
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    expected_matrices = get_excpected_matrices("CMO", "short_causal")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_get_epochs():
    readings = get_json_readings("etc/residual/BOU20200101.json")
    # force a bad measurement for second reading
    readings[2].absolutes[1].absolute = 0
    epochs = [r.time for r in readings if r.get_absolute("H").absolute == 0]
    assert len(epochs) == 1
    epoch_start, epoch_end = get_epochs(
        epochs=epochs,
        time=UTCDateTime("2019-11-01T00:00:00Z"),
    )
    assert epoch_start is None
    assert epoch_end == readings[2].time
    epoch_start, epoch_end = get_epochs(
        epochs=epochs,
        time=UTCDateTime("2020-01-07T00:00:00Z"),
    )
    assert epoch_start == readings[2].time
    assert epoch_end is None
    epoch_start, epoch_end = get_epochs(
        epochs=epochs,
        time=UTCDateTime("2020-01-07T00:00:00Z"),
    )


def test_LeastSq_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        LeastSq().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("LeastSq"),
        decimal=3,
    )


def test_QRFactorization_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        QRFactorization().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("QRFactorization"),
        decimal=3,
    )


def test_Rescale3D_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        Rescale3D().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("Rescale3D"),
        decimal=3,
    )


def test_RotationTranslationXY_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        RotationTranslationXY().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("RotationTranslationXY"),
        decimal=3,
    )


def test_ShearYZ_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        ShearYZ().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("ShearYZ"),
        decimal=3,
    )


def test_SVD_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        SVD().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("SVD"),
        decimal=3,
    )


def test_TranslateOrigins_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        TranslateOrigins().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("TranslateOrigins"),
        decimal=3,
    )


def test_ZRotationHscale_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        ZRotationHscale().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("ZRotationHscale"),
        decimal=3,
    )


def test_ZRotationHscaleZbaseline_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        ZRotationHscaleZbaseline().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("ZRotationHscaleZbaseline"),
        decimal=3,
    )


def test_ZRotationShear_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        ZRotationShear().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("ZRotationShear"),
        decimal=3,
    )
