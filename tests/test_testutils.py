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

import os
import unittest
import unittest.mock

import astropy.time
from astropy.coordinates import Angle
import astropy.units as u
import numpy as np
import pytest

from lsst.ts import utils


class BasicsTestCase(unittest.TestCase):
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

    def test_modify_environ(self) -> None:
        rng = np.random.default_rng(seed=45)
        original_environ = os.environ.copy()
        n_to_delete = 3
        self.assertGreater(len(original_environ), n_to_delete)
        new_key0 = "_a_long_key_name_" + astropy.time.Time.now().isot
        new_key1 = "_another_long_key_name_" + astropy.time.Time.now().isot
        self.assertNotIn(new_key0, os.environ)
        self.assertNotIn(new_key1, os.environ)
        some_keys = rng.choice(list(original_environ.keys()), 3)
        kwargs = {
            some_keys[0]: None,
            some_keys[1]: None,
            some_keys[2]: "foo",
            new_key0: "bar",
            new_key1: None,
        }
        with utils.modify_environ(**kwargs):
            for name, value in kwargs.items():
                if value is None:
                    assert name not in os.environ
                else:
                    assert os.environ[name] == value
            for name, value in os.environ.items():
                if name in kwargs:
                    assert value == kwargs[name]
                else:
                    assert value == original_environ[name]
        assert os.environ == original_environ

        # Values that are neither None nor a string should raise RuntimeError
        for bad_value in (3, 1.23, True, False):
            with pytest.raises(RuntimeError):
                bad_kwargs = kwargs.copy()
                bad_kwargs[new_key1] = bad_value  # type: ignore
                with utils.modify_environ(**bad_kwargs):
                    pass
            assert os.environ == original_environ


if __name__ == "__main__":
    unittest.main()
