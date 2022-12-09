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

__all__ = ["ImageNameServiceClient"]

import aiohttp
import json
import io
import logging


class ImageNameServiceClient:
    def __init__(
        self,
        url: str,
        csc_index: int,
        source: str,
    ) -> None:
        """Implement a client for the Image Name Service.

        Parameters
        ----------
        url : `str`
            The image service host.
            Must be handled by CSC configuration.
        csc_index : `int`
            The index of the CSC, needed for some CSCs which have multiple
            instances running.
        source : `str`
            The two letter ID that the service uses for CSC verification.
            * Electrometer: EM,
            * FiberSpectrograph: FS,
            * ComCam: CM,
            * GenericCamera: GC,
            * MainCamera: MC,
            * AuxTel: AT,
            * TestStand: TS

        Attributes
        ----------
        source : `str`
            The ID used by the service for CSC verification.
        url : `str`
            The URL of the image service.
        csc_index : `str`
            The index of the CSC, used to handle multi instance CSCs.
        log : `logging.Logger`
            The log for the object.
        """
        self.source = source
        self.url = url
        self.csc_index = csc_index
        self.log = logging.getLogger(__name__)

    async def get_next_obs_id(self, num_images: int) -> tuple:
        """Get the observing ID(s).

        Parameters
        ----------
        num_images : `int`
            The number of images to get.

        Raises
        ------
        ValueError
            Raised when num_images is less than 1.

        Returns
        -------
        image_sequence_array : `list` of `int`
            The sequence numbers (e.g. 2).
        values : `list` of `str`
            The returned IDs (e.g ['EM1_O_20221208_000008'])
        """
        if num_images < 1:
            raise ValueError("num_images cannot be less than one.")
        params = {
            "n": num_images,
            "sourceIndex": self.csc_index,
            "source": self.source,
        }
        url = self.url
        call_url = "/ImageUtilities/rest/imageNameService"
        async with aiohttp.ClientSession(
            url, raise_for_status=True, connector=aiohttp.TCPConnector(ssl=False)
        ) as session:
            async with session.get(url=call_url, params=params) as response:
                fd: io.StringIO = io.StringIO()
                async for chunk in response.content.iter_chunked(1024):
                    decoded_chunk = chunk.decode()
                    self.log.info(f"{decoded_chunk=}")
                    fd.write(decoded_chunk)
                    self.log.info(f"{fd=}")
                fd.seek(0)
                values = fd.read()
                self.log.debug(f"{values=}")
                values = json.loads(values)
                self.log.info(f"{values=}")
                image_sequence_array = [int(item.split("_")[-1]) for item in values]
                return image_sequence_array, values
