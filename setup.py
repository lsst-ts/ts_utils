import setuptools

dev_requires = ["documenteer[pipelines]"]

scm_version_template = """# Generated by setuptools_scm
__all__ = ["__version__"]

__version__ = "{version}"
"""

setuptools.setup(
    name="ts_utils",
    description="Python utilities used by ts_salobj and other Telescope and Site software.",
    package_dir={"": "python"},
    use_scm_version={
        "write_to": "python/lsst/ts/utils/version.py",
        "write_to_template": scm_version_template,
    },
    packages=setuptools.find_namespace_packages(where="python"),
    include_package_data=True,
    extras_require={"dev": dev_requires},
    license="GPL",
    project_url={
        "Bug Tracker": "https://jira.lsstcorp.org/secure/Dashboard.jspa",
        "Source Code": "https://github.com/lsst-ts/ts_utils",
    },
)
