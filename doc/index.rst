.. py:currentmodule:: lsst.ts.utils

.. _lsst.ts.utils:

#############
lsst.ts.utils
#############

.. image:: https://img.shields.io/badge/GitHub-gray.svg
    :target: https://github.com/lsst-ts/ts_utils
.. image:: https://img.shields.io/badge/Jira-gray.svg
    :target: https://jira.lsstcorp.org/issues/?jql=labels+%3D+ts_utils

Overview
========

Python utilities used by ts_salobj and other Telescope and Site software.
The main focus is TAI time (functions such as current_tai and tai_from_utc) and angles (functions such as angle_diff and angle_wrap_center).

This package has few dependencies beyond AstroPy.

.. _lsst.ts.utils-user_guide:

User Guide
==========

Time functions include:

* `current_tai`: get the current TAI time in unix seconds.
   This uses CLOCK_TAI, if available (linux only) and not equal to CLOCK_REALTIME (chrony or ntpd is configured to use a leap second table).
* `tai_from_utc`: get TAI in unix seconds given unix time or an `astropy.time.Time`.
  This is significantly faster (for scalars) than astropy.
  Please see the note ``Smearing During the Day Before a Leap Second``

Angle functions include `angle_diff`, `angle_wrap_center` and `angle_wrap_nonnegative`.
These accept either a floating point number in degrees or an `astropy.coordinates.Angle` and return the latter.
If you want the answer as a floating point number in degrees then use the ``deg`` attribute of the returned value.

Miscellaneous functions:

* `make_done_future`: return an `asyncio.Future` that is already done.
  Use this to initialize a class attribute to a Future to track a task that will be run later.
  It is cleaner than initializing the attribute to None and having to check for None every time you access the attribute.

Utilities for unit tests:

* `assert_angles_almost_equal`: assert that two angles are nearly eaqual.
  Each angle can be a floating point number in degrees or an `astropy.coordinates.Angle`.
* `modify_environ`: context manager to temporarily patch os.environ.
  This calls `unittest.mock.patch` and is only intended for unit tests.

.. _lsst.ts.utils.leap_second_smearing:

Leap Second Smearing
--------------------

On the day before a leap second, the following time routines smear the leap second uniformly over the whole day, so the day has exactly 86400 seconds of modified duration:

* `tai_from_utc`
* `tai_from_utc_unix`

This leads to the difference between TAI and UTC varying continuously on that day, instead of being an integer number of seconds.

This may seem strange, but it matches the behavior of `astropy.time` and Standards of Fundamental Astronomy (SOFA) for time expressed as a scalar (such as unix CLOCK_REALTIME UTC clock).
The reason for smearing is that for one sign of leap second there is a second-long period during which there are two possible values of TAI for a given scalar value of UTC.

To convert UTC to TAI without smearing: use astropy.time to convert the value, and express the UTC date as an ISO string;
ISO format supports 60 <= seconds < 61, whereas scalar representations cannot.
Do not use datetime format because neither the datetime library nor astropy.time support datetimes with 60 <= seconds < 61.

On Linux the recommended way to get accurate TAI on the day of a leap second is use the ``CLOCK_TAI`` clock.
In order for this to give the correct time you must configure chrony or ptp (or ntpd, but that is not recommended because it is painfully slow to set CLOCK_TAI after restart) as follows:

* Main a leap second table
  If you omit this then CLOCK_TAI will match CLOCK_REALTIME (your "TAI" time will actually be UTC).
* Make the clock jump at the leap second, rather than smearing over some period of time.
  If you allow smearing then ``CLOCK_TAI`` (and ``CLOCK_REALTIME``) will be wrong during the smearing, because the two clocks always differ by an integer number of seconds.

.. _lsst.ts.utils-pyapi:

Python API reference
====================

.. automodapi:: lsst.ts.utils
   :no-main-docstr:
   :no-inheritance-diagram:

Build and Test
==============

This is a pure python package.
There is nothing to build except the documentation.

.. code-block:: bash

    pytest -v  # to run tests
    package-docs clean; package-docs build  # to build the documentation

Version History
===============

.. toctree::
    version_history
    :maxdepth: 1
