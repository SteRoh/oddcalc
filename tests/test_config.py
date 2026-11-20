from __future__ import annotations

import pytest

from config import AppConfig, CardRegion


@pytest.mark.parametrize(
    ("x", "y", "width", "height"),
    [
        (-0.1, 0.0, 0.2, 0.2),
        (0.0, 0.0, 0.0, 0.2),
        (0.9, 0.0, 0.2, 0.2),
        (0.0, float("nan"), 0.2, 0.2),
    ],
)
def test_invalid_regions_are_rejected(
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    with pytest.raises(ValueError):
        CardRegion(x, y, width, height)


def test_region_scales_to_image_dimensions() -> None:
    region = CardRegion(0.25, 0.5, 0.25, 0.25)

    assert region.crop_box(800, 600) == (200, 300, 400, 450)


def test_default_layout_is_available(app_config: AppConfig) -> None:
    assert "ggpoker_default" in app_config.layouts
