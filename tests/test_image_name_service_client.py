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
import json
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
    source = request.rel_url.query["source"]
    reply = []
    for image in range(int(n)):
        image += 1
        msg = source + source_index
        msg += "_O"
        msg += "_20221130"
        msg += "_" + f"{image:06d}"
        reply.append(msg)
    return web.json_response(json.dumps(reply))


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
            url="http://127.0.0.1:8080", csc_index=3, source="FS"
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
        with self.assertRaises(ValueError):
            (
                image_sequence_array,
                data,
            ) = await self.image_name_service_client.get_next_obs_id(num_images=0)
            (
                image_sequence_array,
                data,
            ) = await self.image_name_service_client.get_next_obs_id(num_images=-1)


if __name__ == "__main__":
    unittest.main()
