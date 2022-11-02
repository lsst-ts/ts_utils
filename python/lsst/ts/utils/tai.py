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
    "MJD_MINUS_UNIX_SECONDS",
    "SECONDS_PER_DAY",
    "astropy_time_from_tai_unix",
    "current_tai",
    "tai_from_utc",
    "tai_from_utc_unix",
    "utc_from_tai_unix",
]

import asyncio
import bisect
import datetime
import logging
import math
import threading
import time
import typing

import astropy.time
import astropy.utils.iers
import astropy.coordinates
import astropy.units as u


SECONDS_PER_DAY = 24 * 60 * 60

# MJD - unix seconds, in seconds
MJD_MINUS_UNIX_SECONDS = (
    astropy.time.Time(0, scale="utc", format="unix").utc.mjd * SECONDS_PER_DAY
)

# A list of (utc_unix_seconds, TAI-UTC seconds);
# automatically updated by `_update_leap_second_table`.
_UTC_LEAP_SECOND_TABLE: typing.Optional[
    typing.Sequence[typing.Tuple[float, float]]
] = None
# A list of (tai_unix_seconds, TAI-UTC seconds);
# automatically updated by `_update_leap_second_table`.
_TAI_LEAP_SECOND_TABLE: typing.Optional[
    typing.Sequence[typing.Tuple[float, float]]
] = None
# A threading timer that schedules automatic update of the leap second table.
_LEAP_SECOND_TABLE_UPDATE_TIMER: typing.Optional[threading.Timer] = None
# When to update the leap second table, in days before expiration.
_LEAP_SECOND_TABLE_UPDATE_MARGIN_DAYS = 10

_MIDDLE_WRAP_ANGLE = astropy.coordinates.Angle(180, u.deg)
_POSITIVE_WRAP_ANGLE = astropy.coordinates.Angle(360, u.deg)


def astropy_time_from_tai_unix(tai_unix: float) -> astropy.time.Time:
    """Get astropy time from TAI in unix seconds.

    Parameters
    ----------
    tai_unix : `float`
        TAI time as unix seconds, e.g. the time returned by CLOCK_TAI
        on linux systems.
    """
    tai_mjd = (MJD_MINUS_UNIX_SECONDS + tai_unix) / SECONDS_PER_DAY
    return astropy.time.Time(tai_mjd, scale="tai", format="mjd")


def make_done_future() -> asyncio.Future:
    future: asyncio.Future = asyncio.Future()
    future.set_result(None)
    return future


def current_tai_from_utc() -> float:
    """Return the current TAI in unix seconds, using `tai_from_utc`."""
    return tai_from_utc_unix(time.time())


def tai_from_utc(
    utc: typing.Union[float, str, astropy.time.Time],
    format: typing.Optional[str] = "unix",
) -> float:
    """Return TAI in unix seconds, given UTC or any `astropy.time.Time`.

    Warning: smears time evenly on the day before a leap second.
    See :ref:`Leap Second Smearing <lsst.ts.utils.leap_second_smearing>`
    for details.

    Because of the smearing, this function should only be used for scalar
    measures of UTC, such as unix seconds, Julian Date or Modified Julian Date.
    It should not be used for ISO-formatted date strings.

    Parameters
    ----------
    utc : `float`, `str` or `astropy.time.Time`
        UTC time in the specified format.
    format : `str` or `None`
        Format of the UTC time, as an `astropy.time` format name,
        or `None` to have astropy guess.
        Ignored if ``utc`` is an instance of `astropy.time.Time`.

    Returns
    -------
    tai_unix : `float`
        TAI time in unix seconds.

    Raises
    ------
    ValueError
        If the date is earlier than 1972 (which is before integer leap seconds)
        or within one day of the expiration date of the leap second table
        (which is automatically updated).

    Notes
    -----
    This function uses a leap second table that is automatically updated
    in the background (though updates are very infrequent).
    """
    if isinstance(utc, float) and format == "unix":
        utc_unix = utc
    elif isinstance(utc, astropy.time.Time):
        utc_unix = utc.unix
    else:
        utc_unix = astropy.time.Time(utc, scale="utc", format=format).unix
    return tai_from_utc_unix(utc_unix)


def tai_from_utc_unix(utc_unix: float) -> float:
    """Return TAI in unix seconds, given UTC in unix seconds.

    Warning: smears time evenly on the day before a leap second.
    See :ref:`Leap Second Smearing <lsst.ts.utils.leap_second_smearing>`
    for details.

    Parameters
    ----------
    utc_unix : `float`
        UTC time in unix seconds.

    Returns
    -------
    tai_unix : `float`
        TAI time in unix seconds.

    Raises
    ------
    ValueError
        If the date is earlier than 1972 (which is before integer leap seconds)
        or within one day of the expiration date of the leap second table
        (which is automatically updated).

    Notes
    -----
    This function uses a leap second table that is automatically updated
    in the background (though updates are very infrequent).
    """
    # Use a local pointer, to prevent race conditions while the
    # global table is being replaced by `_update_leap_second_table`.
    global _UTC_LEAP_SECOND_TABLE
    utc_leap_second_table = _UTC_LEAP_SECOND_TABLE
    if utc_leap_second_table is None:
        raise RuntimeError("No leap second table")
    if utc_unix > utc_leap_second_table[-1][0] - SECONDS_PER_DAY:
        raise ValueError(
            f"{utc_unix} > {utc_leap_second_table[-1][0] - SECONDS_PER_DAY} = "
            "utc_unix expiry date of leap second table - 1 day"
        )
    i = bisect.bisect(utc_leap_second_table, (utc_unix, math.inf))
    if i == 0:
        raise ValueError(
            f"{utc_unix} < start of integer leap seconds "
            f"= {utc_leap_second_table[0][0]}"
        )
    utc0, tai_minus_utc0 = utc_leap_second_table[i - 1]
    utc1, tai_minus_utc1 = utc_leap_second_table[i]
    if utc_unix + SECONDS_PER_DAY > utc1:
        # utc_unix is within the day before a leap second.
        # Smear the UTC time uniformly over the whole day,
        # so that there are exactly 86400 seconds in the day.
        utc_days = utc_unix / SECONDS_PER_DAY
        frac_day = utc_days - math.floor(utc_days)
        tai_minus_utc = tai_minus_utc0 + (tai_minus_utc1 - tai_minus_utc0) * frac_day
    else:
        tai_minus_utc = tai_minus_utc0
    return utc_unix + tai_minus_utc


def utc_from_tai_unix(tai_unix: float) -> float:
    """Return UTC in unix seconds, given TAI in unix seconds.

    The difference is always an integer. Thus this is not the inverse
    of `tai_from_utc_unix`, because that function smears UTC time
    on the day before a leap second.

    Parameters
    ----------
    tai_unix : `float`
        TAI time in unix seconds.

    Returns
    -------
    utc_unix : `float`
        UTC time in unix seconds.

    Raises
    ------
    ValueError
        If the date is earlier than 1972 (which is before integer leap seconds)
        or within one day of the expiration date of the leap second table
        (which is automatically updated).

    Notes
    -----
    This function uses a leap second table that is automatically updated
    in the background (though updates are very infrequent).
    """
    # Use a local pointer, to prevent race conditions while the
    # global table is being replaced by `_update_leap_second_table`.
    global _TAI_LEAP_SECOND_TABLE
    tai_leap_second_table = _TAI_LEAP_SECOND_TABLE
    if tai_leap_second_table is None:
        raise RuntimeError("No leap second table")
    if tai_unix > tai_leap_second_table[-1][0]:
        raise ValueError(
            f"{tai_unix} > {tai_leap_second_table[-1][0]} = "
            "tai_unix expiry date of leap second table"
        )
    i = bisect.bisect(tai_leap_second_table, (tai_unix, math.inf))
    if i == 0:
        raise ValueError(
            f"{tai_unix} < start of integer leap seconds "
            f"= {tai_leap_second_table[0][0]}"
        )
    tai_minus_utc = tai_leap_second_table[i - 1][1]
    return tai_unix - tai_minus_utc


_log = logging.getLogger("lsst.ts.utils.tai")


def _update_leap_second_table() -> None:
    """Update the leap second table.

    Notes
    -----
    This should be called when this module is loaded.
    When called, it obtains the current table from AstroPy,
    then schedules a background (daemon) thread to call itself
    to update the table ``_LEAP_SECOND_TABLE_UPDATE_MARGIN_DAYS``
    before the table expires.

    The leap table will typically have an expiry date that is
    many months away, so it will be rare for auto update to occur.
    """
    _log.info("Update leap second table")
    global _UTC_LEAP_SECOND_TABLE
    global _TAI_LEAP_SECOND_TABLE
    global _LEAP_SECOND_TABLE_UPDATE_TIMER
    ap_table = astropy.utils.iers.LeapSeconds.auto_open()
    utc_leap_second_table = [
        (
            astropy.time.Time(
                datetime.datetime(row["year"], row["month"], 1, 0, 0, 0), scale="utc"
            ).unix,
            float(row["tai_utc"]),
        )
        for row in ap_table
        if row["year"] >= 1972
    ]
    expiry_date_utc_unix = ap_table.expires.unix
    last_tai_utc = utc_leap_second_table[-1][1]
    utc_leap_second_table.append((expiry_date_utc_unix, last_tai_utc))
    tai_leap_second_table = [
        (unix_seconds + tai_utc, tai_utc)
        for (unix_seconds, tai_utc) in utc_leap_second_table
    ]
    _UTC_LEAP_SECOND_TABLE = utc_leap_second_table
    _TAI_LEAP_SECOND_TABLE = tai_leap_second_table

    update_date = (
        expiry_date_utc_unix - _LEAP_SECOND_TABLE_UPDATE_MARGIN_DAYS * SECONDS_PER_DAY
    )
    update_delay = update_date - time.time()
    if _LEAP_SECOND_TABLE_UPDATE_TIMER is not None:
        _LEAP_SECOND_TABLE_UPDATE_TIMER.cancel()
    _log.debug(
        f"Schedule a timer to call _update_leap_second_table in {update_delay} seconds"
    )
    _LEAP_SECOND_TABLE_UPDATE_TIMER = threading.Timer(
        update_delay, _update_leap_second_table
    )
    _LEAP_SECOND_TABLE_UPDATE_TIMER.daemon = True
    _LEAP_SECOND_TABLE_UPDATE_TIMER.start()


_update_leap_second_table()


def _get_current_tai_function() -> typing.Callable[[], float]:
    """Return a function returns the current TAI in unix seconds
    (and which takes no arguments).

    If ``time.clock_gettime(CLOCK_TAI)`` is available (only on linux)
    and gives a reasonable answer, then return that. Otherwise return
    `current_tai_from_utc`, which works on all operating systems, but is
    slower and can be off by up to a second on the day of a leap second.
    """
    if not hasattr(time, "clock_gettime"):
        _log.info(
            "current_tai uses current_tai_from_utc; your operating system does not support clock_gettime"
        )
        return current_tai_from_utc

    try:
        # The clock constant CLOCK_TAI will be available in Python 3.9;
        # meanwhile, the standard value 11 works just fine.
        clock_tai = getattr(time, "CLOCK_TAI", 11)

        def system_tai() -> float:
            """Return current TAI in unix seconds, using clock_gettime."""
            return time.clock_gettime(clock_tai)

        # Call current_tai_from_utc once before using the returned value,
        # to make sure the leap second table is downloaded.
        current_tai_from_utc()
        tslow = current_tai_from_utc()
        try:
            tfast = system_tai()
        except OSError:
            _log.info(
                "current_tai uses current_tai_from_utc; your operating system does not support CLOCK_TAI"
            )
            return current_tai_from_utc

        time_error = tslow - tfast
        # Give margin for being on the day of a leap second
        # (max error is 1 second)
        if abs(time_error) > 1.1:
            _log.warning(
                "current_tai uses current_tai_from_utc; "
                f"clock_gettime(CLOCK_TAI) is off by {time_error:0.1f} seconds"
            )
            return current_tai_from_utc

        _log.info("current_tai uses the system TAI clock")
        return system_tai
    except Exception as e:
        _log.warning(
            f"current_tai uses current_tai_from_utc; error determining if clock_gettime is usable: {e}"
        )
        return current_tai_from_utc


current_tai = _get_current_tai_function()
