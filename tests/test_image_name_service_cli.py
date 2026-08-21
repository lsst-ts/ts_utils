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

from unittest.mock import AsyncMock, patch

import pytest

from lsst.ts.utils.image_name_service_cli import main, run


async def test_run_prints_observation_ids(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("lsst.ts.utils.image_name_service_cli.ImageNameServiceClient") as client_class:
        client_class.return_value.get_next_obs_id = AsyncMock(
            return_value=([1, 2], ["EM1_O_20260729_000001", "EM1_O_20260729_000002"])
        )

        await run(None, 1, "Electrometer", 2)

    client_class.assert_called_once_with(None, 1, "Electrometer")
    client_class.return_value.get_next_obs_id.assert_awaited_once_with(2)
    assert capsys.readouterr().out == "EM1_O_20260729_000001\nEM1_O_20260729_000002\n"


def test_main_uses_site_and_electrometer_defaults() -> None:
    with patch("lsst.ts.utils.image_name_service_cli.run", new_callable=AsyncMock) as run:
        main([])

    run.assert_awaited_once_with(
        url=None,
        csc_index=3,
        source="Electrometer",
        num_images=1,
    )
