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

__all__ = ["index_generator", "make_done_future"]

import asyncio
from collections.abc import Generator

# Maximum value of a 32-bit signed int
MAX_INT32 = (1 << 31) - 1


def index_generator(
    imin: int = 1, imax: int = MAX_INT32, i0: int | None = None
) -> Generator[int, None, None]:
    """Sequential index generator.

    Returns values i0, i0+1, i0+2, ..., max, min, min+1, ...

    Parameters
    ----------
    imin : `int`, optional
        Minimum index (inclusive).
    imax : `int`, optional
        Maximum index (inclusive).
    i0 : `int`, optional
        Initial index; if None then use ``imin``.

    Notes
    -----
    The default min and max values are the allowed range of positive SAL
    indices. The index 0 has special meaning, and, by convention, we avoid
    negative SAL indices.

    Raises
    ------
    ValueError
        If imin >= imax
    """
    imin = int(imin)
    imax = int(imax)
    i0 = imin if i0 is None else int(i0)
    if imax <= imin:
        raise ValueError(f"imin={imin} must be less than imax={imax}")
    if not imin <= i0 <= imax:
        raise ValueError(f"i0={i0} must be >= imin={imin} and <= imax={imax}")

    # define an inner generator and return that
    # in order to get immediate argument checking
    def index_impl() -> Generator[int, None, None]:
        index = i0 - 1  # type: ignore
        while True:
            index += 1
            if index > imax:
                index = imin

            yield index

    return index_impl()


def make_done_future() -> asyncio.Future:
    future: asyncio.Future = asyncio.Future()
    future.set_result(None)
    return future
