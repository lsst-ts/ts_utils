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

import unittest

import pytest
from aiohttp import web
from lsst.ts.utils.image_name_service_client import ImageNameServiceClient


async def image_array(request: web.Request) -> web.Response:
    """Handle the name service request.

    Takes 3 parameters based on the real image service.
    It's very simple in scope and is meant to make sure that the
    format is at least basically correct.

    Parameters
    ----------
    request : `web.Request`
        Contains the information from the http request.

    Returns
    -------
    web.Response
        A string representation of an array of strings.

    """
    n = request.rel_url.query["n"]
    source_index = request.rel_url.query["sourceIndex"]
    source_prefix = {"FiberSpectrograph": "FS"}[request.rel_url.query["source"]]

    reply = []
    for image in range(int(n)):
        image += 1
        msg = source_prefix + source_index
        msg += "_O"
        msg += "_20221130"
        msg += "_" + f"{image:06d}"
        reply.append(msg)
    return web.json_response(reply)


class GeneratorTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        app = web.Application()
        app.add_routes([web.get("/ImageUtilities/rest/imageNameService", image_array)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 8080)
        await site.start()
        # wait for finish signal
        # await runner.cleanup()
        self.image_name_service_client = ImageNameServiceClient(
            url="http://127.0.0.1:8080", csc_index=3, source="FiberSpectrograph"
        )
        return super().setUp()

    async def test_get_next_obs_id(self) -> None:
        (
            image_sequence_array,
            data,
        ) = await self.image_name_service_client.get_next_obs_id(num_images=1)
        assert image_sequence_array == [1]
        assert data == ["FS3_O_20221130_000001"]
        (
            image_sequence_array,
            data,
        ) = await self.image_name_service_client.get_next_obs_id(num_images=2)
        assert image_sequence_array == [1, 2]
        assert data == ["FS3_O_20221130_000001", "FS3_O_20221130_000002"]
        with pytest.raises(ValueError):
            (
                image_sequence_array,
                data,
            ) = await self.image_name_service_client.get_next_obs_id(num_images=0)
            (
                image_sequence_array,
                data,
            ) = await self.image_name_service_client.get_next_obs_id(num_images=-1)


@pytest.mark.parametrize(
    ("site", "url"),
    [
        ("summit", "http://ccs.lsst.org"),
        ("base", "http://lsstcam-mcm.ls.lsst.org"),
        ("tucson", "http://comcam-mcm.tu.lsst.org"),
    ],
)
def test_site_url(monkeypatch: pytest.MonkeyPatch, site: str, url: str) -> None:
    monkeypatch.setenv("LSST_SITE", site)
    client = ImageNameServiceClient(csc_index=3, source="Electrometer")
    assert client.url == url


@pytest.mark.parametrize(
    ("url", "expected_url"),
    [
        ("mcm.example.org", "http://mcm.example.org"),
        ("http://mcm.example.org", "http://mcm.example.org"),
        ("https://mcm.example.org", "https://mcm.example.org"),
    ],
)
def test_explicit_url(url: str, expected_url: str) -> None:
    client = ImageNameServiceClient(url=url, csc_index=3, source="Electrometer")
    assert client.url == expected_url


def test_source_is_not_restricted() -> None:
    source = "NewCsc"
    client = ImageNameServiceClient(
        url="http://mcm.example.org", csc_index=3, source=source
    )
    assert client.source == source


@pytest.mark.parametrize("site", ["", "unknown"])
def test_invalid_site(monkeypatch: pytest.MonkeyPatch, site: str) -> None:
    monkeypatch.setenv("LSST_SITE", site)
    with pytest.raises(ValueError, match="Unsupported LSST_SITE"):
        ImageNameServiceClient(csc_index=3, source="Electrometer")


if __name__ == "__main__":
    unittest.main()
