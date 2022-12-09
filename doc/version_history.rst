.. py:currentmodule:: lsst.ts.utils

.. _lsst.ts.utils.version_history:

###############
Version History
###############

v1.2.1
------

* Add aiohttp as test and run dependencies in conda recipe.

v1.2.0
------

* Fix an overly severe log message at import on operating systems without a CLOCK_TAI clock (e.g. macOS).
  Instead of a warning-level message that describes an error, issue a bland info-level message.
* Run isort
* Add isort and mypy to pre-commit and update other pre-commit software versions.
* Add ImageNameServiceClient class

v1.1.2
------

* Change the build system to use pyproject.toml.

v1.1.1
------

* Fix a doc string to show using modify_environment from utils, not salobj.
* Modernize the Jenkinsfile.

v1.1.0
------

* Add `index_generator`.

v1.0.2
------

* Fix a new mypy error by not checking DM's `lsst/__init__.py` files.

v1.0.1
------

* Fix incorrect use of ``pytest.approx`` in unit tests.

v1.0.0
------

* The first release.
