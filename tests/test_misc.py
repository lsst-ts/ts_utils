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

import asyncio
import unittest
from collections.abc import Generator, Sequence

import pytest
from lsst.ts import utils


class BasicsTestCase(unittest.IsolatedAsyncioTestCase):
    def check_index_generator(
        self,
        generator: Generator[int, None, None],
        expected_values: Sequence[int],
    ) -> None:
        values = [next(generator) for i in range(len(expected_values))]
        assert values == list(expected_values)

    def test_index_generator(self) -> None:
        with pytest.raises(ValueError):
            utils.index_generator(1, 1)  # imin >= imax
        with pytest.raises(ValueError):
            utils.index_generator(1, 0)  # imin >= imax
        with pytest.raises(ValueError):
            utils.index_generator(0, 5, -1)  # i0 < imin
        with pytest.raises(ValueError):
            utils.index_generator(0, 5, 6)  # i0 > imax

        # Check default arguments
        generator = utils.index_generator()
        self.check_index_generator(generator=generator, expected_values=[1, 2, 3])

        # Check wraparound with default imin and imax;
        # specifying i0 avoids the need to call next 2*31 times.
        max_int32 = (1 << 31) - 1
        generator = utils.index_generator(i0=max_int32)
        self.check_index_generator(
            generator=generator, expected_values=[max_int32, 1, 2]
        )

        imin = -2
        imax = 5
        generator = utils.index_generator(imin=-2, imax=5)
        self.check_index_generator(
            generator=generator,
            expected_values=[-2, -1, 0, 1, 2, 3, 4, 5, -2, -1, 0, 1, 2, 3, 4, 5, -2],
        )

        imin = -2
        imax = 5
        i0 = imax
        generator = utils.index_generator(imin=imin, imax=imax, i0=i0)
        self.check_index_generator(
            generator=generator, expected_values=[5, -2, -1, 0, 1, 2, 3, 4, 5, -2]
        )

    def test_make_done_future(self) -> None:
        done_future = utils.make_done_future()
        assert isinstance(done_future, asyncio.Future)
        assert done_future.done()
        assert done_future.result() is None
        assert not done_future.cancelled()
        assert done_future.exception() is None
