from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from vision.template_matcher import TemplateMatcher


def _pattern(seed: int, shape: tuple[int, int] = (20, 20)) -> np.ndarray:
    return np.random.default_rng(seed).integers(
        0,
        256,
        size=(*shape, 3),
        dtype=np.uint8,
    )


def _write_template(template_dir: Path, card: str, image: np.ndarray) -> None:
    assert cv2.imwrite(str(template_dir / f"{card}.png"), image)


def test_exact_card_template_matches_inside_region(tmp_path: Path) -> None:
    template = _pattern(1)
    _write_template(tmp_path, "Ah", template)
    matcher = TemplateMatcher(tmp_path, threshold=0.90)

    region = _pattern(2, (40, 40))
    region[8:28, 11:31] = template

    card, score = matcher.match(region)

    assert card == "Ah"
    assert score == pytest.approx(1.0)


def test_unrelated_region_is_rejected(tmp_path: Path) -> None:
    _write_template(tmp_path, "Ah", _pattern(3))
    matcher = TemplateMatcher(tmp_path, threshold=0.99)

    card, score = matcher.match(_pattern(4))

    assert card is None
    assert score < 0.99


def test_constant_template_is_rejected(tmp_path: Path) -> None:
    _write_template(
        tmp_path,
        "Ah",
        np.full((20, 20, 3), (40, 80, 120), dtype=np.uint8),
    )

    with pytest.raises(ValueError, match="color detail"):
        TemplateMatcher(tmp_path)


def test_constant_region_is_not_a_match(tmp_path: Path) -> None:
    _write_template(tmp_path, "Ah", _pattern(5))
    matcher = TemplateMatcher(tmp_path)

    card, score = matcher.match(
        np.full((20, 20, 3), (40, 80, 120), dtype=np.uint8)
    )

    assert card is None
    assert score == -1.0


@pytest.mark.parametrize("threshold", [-0.01, 1.01, float("nan")])
def test_invalid_threshold_is_rejected(tmp_path: Path, threshold: float) -> None:
    with pytest.raises(ValueError, match="threshold"):
        TemplateMatcher(tmp_path, threshold)


def test_invalid_region_shape_is_rejected(tmp_path: Path) -> None:
    _write_template(tmp_path, "Ah", _pattern(6))
    matcher = TemplateMatcher(tmp_path)

    with pytest.raises(ValueError, match="three-channel uint8"):
        matcher.match(np.zeros((20, 20), dtype=np.uint8))
