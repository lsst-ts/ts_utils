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

import datetime
import time
import unittest
import unittest.mock

import astropy.time
import astropy.units as u
import pytest
from lsst.ts import utils


def alternate_tai_from_utc_unix(utc_unix: float) -> float:
    """Compute TAI in unix seconds given UTC in unix seconds.

    Parameters
    ----------
    utc_unix : `float`

    This is not the implementation in base.py for two reasons:

    * It is too slow; it slows tests/test_speed.py by a factor of 8.
    * It blocks while downloading a leap second table.
    """
    ap_time = astropy.time.Time(utc_unix, scale="utc", format="unix")
    return ap_time.tai.mjd * utils.SECONDS_PER_DAY - utils.MJD_MINUS_UNIX_SECONDS


class BasicsTestCase(unittest.TestCase):
    def test_astropy_time_from_tai_unix(self) -> None:
        # Check the function at a leap second transition,
        # since that is likely to cause problems
        unix_time0 = datetime.datetime.fromisoformat("2017-01-01").timestamp()
        for dt in (-1, -0.5, -0.1, 0, 0.1, 1):
            with self.subTest(dt=dt):
                utc_unix = unix_time0 + dt
                tai_unix = utils.tai_from_utc(utc_unix)
                astropy_time1 = utils.astropy_time_from_tai_unix(tai_unix)
                assert isinstance(astropy_time1, astropy.time.Time)
                assert astropy_time1.scale == "tai"
                tai_unix_round_trip1 = utils.tai_from_utc(astropy_time1)
                assert tai_unix == pytest.approx(tai_unix_round_trip1, abs=1e-6)

    def check_tai_from_utc(self, utc_ap: astropy.time.Time) -> None:
        """Check tai_from_utc at a specific UTC date.

        Parameters
        ----------
        utc_ap : `astropy.time.Time`
            UTC date as an astropy time.
        """
        tai = utils.tai_from_utc(utc_ap.utc.unix)

        tai_alt = alternate_tai_from_utc_unix(utc_ap.utc.unix)
        assert tai == pytest.approx(tai_alt, abs=1e-6)

        tai2 = utils.tai_from_utc(utc_ap.utc.iso, format="iso")
        assert tai == pytest.approx(tai2, abs=1e-6)

        tai3 = utils.tai_from_utc(utc_ap.utc.iso, format=None)
        assert tai == pytest.approx(tai3, abs=1e-6)

        tai4 = utils.tai_from_utc(utc_ap.utc.mjd, format="mjd")
        assert tai == pytest.approx(tai4, abs=1e-6)

        tai_mjd = (tai + utils.MJD_MINUS_UNIX_SECONDS) / utils.SECONDS_PER_DAY
        tai_mjd_ap = astropy.time.Time(tai_mjd, scale="tai", format="mjd")
        tai5 = utils.tai_from_utc(tai_mjd_ap)
        assert tai == pytest.approx(tai5, abs=1e-6)

        tai_iso_ap = astropy.time.Time(utc_ap.tai.iso, scale="tai", format="iso")
        tai6 = utils.tai_from_utc(tai_iso_ap)
        assert tai == pytest.approx(tai6, abs=1e-6)

        tai7 = utils.tai_from_utc(utc_ap)
        assert tai == pytest.approx(tai7, abs=1e-6)

    def test_leap_second_table(self) -> None:
        """Check that the leap second table is set and an update scheduled."""
        assert utils.tai._UTC_LEAP_SECOND_TABLE is not None
        update_timer = utils.tai._LEAP_SECOND_TABLE_UPDATE_TIMER
        assert update_timer.is_alive()
        assert update_timer.daemon
        assert update_timer.function is utils.tai._update_leap_second_table
        update_margin = (
            utils.tai._LEAP_SECOND_TABLE_UPDATE_MARGIN_DAYS * utils.SECONDS_PER_DAY
        )
        current_duration = (
            time.time() - utils.tai._UTC_LEAP_SECOND_TABLE[-1][0] - update_margin
        )
        assert update_timer.interval > current_duration

    def test_tai_from_utc(self) -> None:
        """Test tai_from_utc."""
        # Check tai_from_utc near leap second transition at UTC = 2017-01-01
        # when leap seconds went from 36 to 37.
        utc0_ap = astropy.time.Time("2017-01-01", scale="utc", format="iso")
        for utc_ap in (
            (utc0_ap - 0.5 * u.day),
            (utc0_ap - 1 * u.second),
            (utc0_ap - 0.1 * u.second),
            (utc0_ap),
            (utc0_ap + 0.1 * u.second),
            (utc0_ap + 1 * u.second),
        ):
            with self.subTest(utc_ap=utc_ap):
                self.check_tai_from_utc(utc_ap=utc_ap)

        # Test values near the limits of the leap second table, which starts
        # on 1972-01-01T00:00:00 and ends whenever the table expires.
        first_utc_unix, first_tai_minus_utc = utils.tai._UTC_LEAP_SECOND_TABLE[0]
        desired_first_utc_unix = astropy.time.Time(
            "1972-01-01", scale="utc", format="iso"
        ).unix
        desired_first_tai_minus_utc = 10
        assert first_utc_unix == pytest.approx(desired_first_utc_unix)
        assert first_tai_minus_utc == pytest.approx(desired_first_tai_minus_utc)
        first_tai_unix = utils.tai_from_utc(first_utc_unix)
        assert first_tai_unix == pytest.approx(first_utc_unix + first_tai_minus_utc)
        with pytest.raises(ValueError):
            utils.tai_from_utc(first_utc_unix - 0.001)

        last_utc_unix, last_tai_minus_utc = utils.tai._UTC_LEAP_SECOND_TABLE[-1]
        # The last UTC that can be converted to TAI is a day earlier
        # than the last entry in the leap second table,
        # due to the possible 1 day smearing on the day before a leap second.
        last_usable_utc_unix = last_utc_unix - utils.SECONDS_PER_DAY
        # last_utc_unix -= utils.SECONDS_PER_DAY
        last_tai_unix = utils.tai_from_utc(last_usable_utc_unix)
        # Final value of TAI-UTC in the table.
        # Note that the last entry in the table has TAI-UTC = None.
        final_tai_minus_utc = utils.tai._UTC_LEAP_SECOND_TABLE[-1][1]
        assert last_tai_unix - last_usable_utc_unix == pytest.approx(
            final_tai_minus_utc
        )
        with pytest.raises(ValueError):
            utils.tai_from_utc(last_usable_utc_unix + 0.001)

    def test_utc_from_tai_unix(self) -> None:
        # Check utc_from_tai_unix near leap second transition at
        # UTC = 2017-01-01 when leap seconds went from 36 to 37.
        utc0 = astropy.time.Time("2017-01-01", scale="utc", format="iso").unix
        tai_minus_utc_before = 36
        tai_minus_utc_after = 37
        tai0 = utc0 + tai_minus_utc_after
        desired_tai_minus_utc_after = utils.tai_from_utc_unix(utc0) - utc0
        assert tai_minus_utc_after == pytest.approx(desired_tai_minus_utc_after)
        # Don't test right at tai0 because roundoff error could cause failure;
        # utc_from_tai_unix is discontinuous at a leap second tranition.
        for tai in (
            (tai0 - 0.5 * utils.SECONDS_PER_DAY),
            (tai0 - 1),
            (tai0 - 0.001),
            (tai0 + 0.001),
            (tai0 + 1),
            (tai0 + 0.5 * utils.SECONDS_PER_DAY),
        ):
            utc = utils.utc_from_tai_unix(tai)
            tai_minus_utc = tai - utc
            if tai < tai0:
                assert tai_minus_utc == pytest.approx(tai_minus_utc_before)
            else:
                assert tai_minus_utc == pytest.approx(tai_minus_utc_after)

        # Test values near the limits of the TAI leap second table
        first_tai_unix, first_tai_minus_utc = utils.tai._TAI_LEAP_SECOND_TABLE[0]
        first_utc_unix = utils.utc_from_tai_unix(first_tai_unix)
        desired_first_tai_minus_utc = 10
        assert first_tai_minus_utc == pytest.approx(desired_first_tai_minus_utc)
        assert first_tai_unix - first_utc_unix == pytest.approx(
            desired_first_tai_minus_utc
        )
        with pytest.raises(ValueError):
            utils.utc_from_tai_unix(first_tai_unix - 0.001)

        last_tai_unix, last_tai_minus_utc = utils.tai._TAI_LEAP_SECOND_TABLE[-1]
        last_utc_unix = utils.utc_from_tai_unix(last_tai_unix)
        assert last_tai_unix - last_utc_unix == pytest.approx(last_tai_minus_utc)
        with pytest.raises(ValueError):
            utils.utc_from_tai_unix(last_tai_unix + 0.001)

    def test_current_tai(self) -> None:
        utc0 = time.time()
        tai0 = utils.tai_from_utc(utc0)
        # utils.tai.current_tai_from_utc uses tai_from_utc,
        # so it should give the same answer.
        tai1 = utils.tai.current_tai_from_utc()
        # utils.current_tai uses the system TAI clock, if available.
        # This gives the correct answer (if your operating system
        # is correctly configured) and can differ from the answer given by
        # tai_from_utc by as much as a second on the day of a leap second.
        tai2 = utils.current_tai()
        print(f"tai1-tai0={tai1-tai0:0.4f}")
        # The difference should be much less than 0.1
        # but pytest can introduce unexpected delays.
        assert abs(tai1 - tai0) < 0.1
        assert tai1 >= tai0
        # The difference between the value returned by current_tai
        # and current_tai_from_utc
        assert abs(tai2 - tai0) < 1.1
        assert type(tai0) is float
        assert type(tai1) is float
        assert type(tai2) is float
