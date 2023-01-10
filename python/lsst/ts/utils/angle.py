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

__all__ = [
    "AngleOrDegType",
    "angle_diff",
    "angle_wrap_center",
    "angle_wrap_nonnegative",
]

import typing

import astropy.coordinates
import astropy.time
import astropy.units as u
import astropy.utils.iers

AngleOrDegType: typing.TypeAlias = astropy.coordinates.Angle | float

_MIDDLE_WRAP_ANGLE = astropy.coordinates.Angle(180, u.deg)
_POSITIVE_WRAP_ANGLE = astropy.coordinates.Angle(360, u.deg)


def angle_diff(
    angle1: AngleOrDegType, angle2: AngleOrDegType
) -> astropy.coordinates.Angle:
    """Return angle1 - angle2 wrapped into the range [-180, 180) deg.

    Parameters
    ----------
    angle1
        Angle 1; if a float then in degrees
    angle2
        Angle 2; if a float then in degrees

    Returns
    -------
    diff : `astropy.coordinates.Angle`
        angle1 - angle2 wrapped into the range -180 <= diff < 180 deg.
    """
    return angle_wrap_center(
        astropy.coordinates.Angle(angle1, u.deg)
        - astropy.coordinates.Angle(angle2, u.deg)
    )


def angle_wrap_center(angle: AngleOrDegType) -> astropy.coordinates.Angle:
    """Return an angle wrapped into the range [-180, 180) deg.

    Parameters
    ----------
    angle
        Angle; if a float then in degrees

    Returns
    -------
    wrapped : `astropy.coordinates.Angle`
        angle wrapped into the range -180 <= wrapped < 180 deg.
    """
    return astropy.coordinates.Angle(angle, u.deg).wrap_at(_MIDDLE_WRAP_ANGLE)


def angle_wrap_nonnegative(angle: AngleOrDegType) -> astropy.coordinates.Angle:
    """Return an angle wrapped into the range [0, 360) deg.

    Parameters
    ----------
    angle
        Angle; if a float then in degrees

    Returns
    -------
    wrapped : `astropy.coordinates.Angle`
        angle wrapped into the range 0 <= wrapped < 360 deg.
    """
    return astropy.coordinates.Angle(angle, u.deg).wrap_at(_POSITIVE_WRAP_ANGLE)
