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

__all__ = ["assert_angles_almost_equal", "modify_environ"]

import contextlib
import os
import typing
import unittest
from collections.abc import Generator

import astropy.coordinates
import astropy.units as u

from .angle import AngleOrDegType, angle_diff


def assert_angles_almost_equal(
    angle1: AngleOrDegType, angle2: AngleOrDegType, max_diff: AngleOrDegType = 1e-5
) -> None:
    """Raise AssertionError if angle1 and angle2 are too different,
    ignoring wrap.

    Parameters
    ----------
    angle1 : `astropy.coordinates.Angle` or `float`
        Angle 1; if a float then in degrees
    angle2 : `astropy.coordinates.Angle` or `float`
        Angle 2; if a float then in degrees
    max_diff : `astropy.coordinates.Angle` or `float`
        Maximum allowed difference; if a float then in degrees

    Raises
    ------
    AssertionError
        If `angle_diff` of angle1 and angle2 exceeds max_diff.
    """
    diff = abs(angle_diff(angle1, angle2))
    if diff > astropy.coordinates.Angle(max_diff, u.deg):
        raise AssertionError(f"{angle1} and {angle2} differ by {diff} > {max_diff}")


@contextlib.contextmanager
def modify_environ(**kwargs: typing.Any) -> Generator[None, None, None]:
    """Context manager to temporarily patch os.environ.

    This calls `unittest.mock.patch` and is only intended for unit tests.

    Parameters
    ----------
    kwargs : `dict` [`str`, `str` or `None`]
        Environment variables to set or clear.
        Each key is the name of an environment variable (with correct case);
        it need not already exist. Each value must be one of:

        * A string value to set the env variable.
        * None to delete the env variable, if present.

    Raises
    ------
    RuntimeError
        If any value in kwargs is not of type `str` or `None`.

    Notes
    -----
    Example of use::

        from lsst.ts import utils
        ...
        def test_foo(self):
            set_value = "Value for $ENV_TO_SET"
            with utils.modify_environ(
                HOME=None,  # Delete this env var
                ENV_TO_SET=set_value,  # Set this env var
            ):
                self.assertNotIn("HOME", os.environ)
                self.assert(os.environ["ENV_TO_SET"], set_value)
    """
    bad_value_strs = [
        f"{name}: {value!r}"
        for name, value in kwargs.items()
        if not isinstance(value, str) and value is not None
    ]
    if bad_value_strs:
        raise RuntimeError(
            "The following arguments are not of type str or None: "
            + ", ".join(bad_value_strs)
        )

    new_environ = os.environ.copy()
    for name, value in kwargs.items():
        if value is None:
            new_environ.pop(name, None)
        else:
            new_environ[name] = value
    with unittest.mock.patch("os.environ", new_environ):  # type: ignore
        yield
