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

import logging
import os

import aiohttp


_SITE_URLS = {
    "summit": "http://ccs.lsst.org",
    "base": "http://lsstcam-mcm.ls.lsst.org",
    "tucson": "http://comcam-mcm.tu.lsst.org",
}
class ImageNameServiceClient:
    """Client for the Image Name Service.

    Parameters
    ----------
    url : `str`, optional
        The image service host. If omitted, select the host using `LSST_SITE`.
    csc_index : `int`
        The index of the CSC, needed for some CSCs which have multiple
        instances running.
    source : `str`
        The CSC name used by the service for verification.

    Attributes
    ----------
    source : `str`
        The CSC name used by the service for CSC verification.
    url : `str`
        The URL of the image service.
    csc_index : `int`
        The index of the CSC, used to handle multi instance CSCs.
    log : `logging.Logger`
        The log for the object.
    """

    def __init__(
        self,
        url: str | None = None,
        csc_index: int | None = None,
        source: str | None = None,
    ) -> None:
        if csc_index is None:
            raise TypeError("csc_index is required")
        if source is None:
            raise TypeError("source is required")

        if url is None:
            site = os.getenv("LSST_SITE", "").lower()
            try:
                url = _SITE_URLS[site]
            except KeyError as exc:
                raise ValueError(f"Unsupported LSST_SITE: {site!r}") from exc
        elif not url.lower().startswith(("http://", "https://")):
            url = f"http://{url}"

        self.source = source
        self.url = url
        self.csc_index = csc_index
        self.log = logging.getLogger(__name__)

    async def get_next_obs_id(self, num_images: int) -> tuple[list[int], list[str]]:
        """Get the observing ID(s).

        Parameters
        ----------
        num_images : `int`
            The number of images to get.

        Raises
        ------
        ValueError
            If num_images is less than 1.

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
                values: list[str] = await response.json()
                self.log.info(f"{values=}")
                image_sequence_array = [int(item.split("_")[-1]) for item in values]
                return image_sequence_array, values
