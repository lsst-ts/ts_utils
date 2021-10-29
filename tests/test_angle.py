# This file is part of ts_utils.
#
# Developed for the Rubin Observatory Telescope and Site System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import unittest

from astropy.coordinates import Angle
import astropy.units as u
import pytest

from lsst.ts import utils


class BasicsTestCase(unittest.TestCase):
    def test_angle_diff(self) -> None:
        for angle1, angle2, expected_diff in (
            (5.15, 0, 5.15),
            (5.21, 359.20, 6.01),
            (270, -90, 0),
        ):
            with self.subTest(
                angle1=angle1, angle2=angle2, expected_diff=expected_diff
            ):
                diff = utils.angle_diff(angle1, angle2)
                assert diff.deg == pytest.approx(expected_diff, abs=1e-7)
                diff = utils.angle_diff(angle2, angle1)
                assert diff.deg == pytest.approx(-expected_diff, abs=1e-7)
                diff = utils.angle_diff(Angle(angle1, u.deg), angle2)
                assert diff.deg == pytest.approx(expected_diff, abs=1e-7)
                diff = utils.angle_diff(angle1, Angle(angle2, u.deg))
                assert diff.deg == pytest.approx(expected_diff, abs=1e-7)
                diff = utils.angle_diff(Angle(angle1, u.deg), Angle(angle2, u.deg))
                assert diff.deg == pytest.approx(expected_diff, abs=1e-7)

    def test_angle_wrap_center(self) -> None:
        for base_angle, expected_result in (
            (-180.001, 179.999),
            (-180, -180),
            (0, 0),
            (179.999, 179.999),
            (180, -180),
        ):
            for nwraps in (-2, -1, 0, 1, 2):
                with self.subTest(
                    base_angle=base_angle,
                    expected_result=expected_result,
                    nwraps=nwraps,
                ):
                    angle = base_angle + 360 * nwraps
                    result = utils.angle_wrap_center(angle)
                    assert result.deg == pytest.approx(expected_result, abs=1e-7)
                    result = utils.angle_wrap_center(Angle(angle, u.deg))
                    assert result.deg == pytest.approx(expected_result, abs=1e-7)

    def test_angle_wrap_nonnegative(self) -> None:
        for base_angle, expected_result in (
            (-0.001, 359.999),
            (0, 0),
            (180, 180),
            (359.999, 359.999),
            (360, 0),
        ):
            for nwraps in (-2, -1, 0, 1, 2):
                with self.subTest(
                    base_angle=base_angle,
                    expected_result=expected_result,
                    nwraps=nwraps,
                ):
                    angle = base_angle + 360 * nwraps
                    result = utils.angle_wrap_nonnegative(angle)
                    assert result.deg == pytest.approx(expected_result, abs=1e-7)
                    result = utils.angle_wrap_nonnegative(Angle(angle, u.deg))
                    assert result.deg == pytest.approx(expected_result, abs=1e-7)

    def test_assert_angles_almost_equal(self) -> None:
        for angle1, angle2 in ((5.15, 5.14), (-0.20, 359.81), (270, -90.1)):
            epsilon = Angle(1e-15, u.deg)
            with self.subTest(angle1=angle1, angle2=angle2):
                diff = abs(utils.angle_diff(angle1, angle2))
                bad_diff = diff - epsilon
                self.assertGreater(bad_diff.deg, 0)
                with pytest.raises(AssertionError):
                    utils.assert_angles_almost_equal(angle1, angle2, bad_diff)
                with pytest.raises(AssertionError):
                    utils.assert_angles_almost_equal(angle1, angle2, bad_diff.deg)
                with pytest.raises(AssertionError):
                    utils.assert_angles_almost_equal(angle2, angle1, bad_diff)
                with pytest.raises(AssertionError):
                    utils.assert_angles_almost_equal(
                        Angle(angle1, u.deg), angle2, bad_diff
                    )
                with pytest.raises(AssertionError):
                    utils.assert_angles_almost_equal(
                        angle1, Angle(angle2, u.deg), bad_diff
                    )
                with pytest.raises(AssertionError):
                    utils.assert_angles_almost_equal(
                        Angle(angle1, u.deg), Angle(angle2, u.deg), bad_diff
                    )

                good_diff = diff + epsilon
                utils.assert_angles_almost_equal(angle1, angle2, good_diff)
                utils.assert_angles_almost_equal(angle1, angle2, good_diff.deg)
                utils.assert_angles_almost_equal(angle2, angle1, good_diff)
                utils.assert_angles_almost_equal(
                    Angle(angle1, u.deg), angle2, good_diff
                )
                utils.assert_angles_almost_equal(
                    angle1, Angle(angle2, u.deg), good_diff
                )
                utils.assert_angles_almost_equal(
                    Angle(angle1, u.deg), Angle(angle2, u.deg), good_diff
                )
