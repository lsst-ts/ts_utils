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

"""Command-line client for the Image Name Service."""

import argparse
import asyncio
from collections.abc import Sequence

from .image_name_service_client import ImageNameServiceClient


async def run(url: str | None, csc_index: int, source: str, num_images: int) -> None:
    """Request image IDs and print one ID per line."""
    client = ImageNameServiceClient(url, csc_index, source)
    _, observation_ids = await client.get_next_obs_id(num_images)
    print(*observation_ids, sep="\n")


def main(args: Sequence[str] | None = None) -> None:
    """Run the Image Name Service command-line client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Image Name Service URL (default: selected by LSST_SITE).")
    parser.add_argument("--csc-index", type=int, default=3, help="CSC instance index.")
    parser.add_argument("--source", default="Electrometer", help="CSC name.")
    parser.add_argument("num_images", type=int, nargs="?", default=1, metavar="num-images")
    parsed_args = parser.parse_args(args)
    asyncio.run(
        run(
            url=parsed_args.url,
            csc_index=parsed_args.csc_index,
            source=parsed_args.source,
            num_images=parsed_args.num_images,
        )
    )


if __name__ == "__main__":
    main()
