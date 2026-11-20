from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from config import CardRegion, LayoutConfig
from vision.card_detector import CardDetector


def _pattern(seed: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(
        0,
        256,
        size=(20, 20, 3),
        dtype=np.uint8,
    )


def _layout() -> LayoutConfig:
    return LayoutConfig(
        name="test",
        hero_card_1=CardRegion(0.0, 0.0, 0.2, 0.2),
        hero_card_2=CardRegion(0.2, 0.0, 0.2, 0.2),
        flop_1=CardRegion(0.4, 0.0, 0.2, 0.2),
        flop_2=CardRegion(0.6, 0.0, 0.2, 0.2),
        flop_3=CardRegion(0.8, 0.0, 0.2, 0.2),
        turn=CardRegion(0.0, 0.8, 0.2, 0.2),
        river=CardRegion(0.2, 0.8, 0.2, 0.2),
    )


def test_detects_hero_and_flop_turn_river(tmp_path: Path) -> None:
    cards = ("Ah", "Kh", "Qs", "Js", "2d", "4c", "5s")
    screenshot = np.random.default_rng(42).integers(
        0,
        256,
        size=(100, 100, 3),
        dtype=np.uint8,
    )
    regions = _layout().hero_regions() + _layout().board_regions()

    for seed, (card, region) in enumerate(zip(cards, regions, strict=True)):
        template = _pattern(seed)
        assert cv2.imwrite(str(tmp_path / f"{card}.png"), template)
        x1, y1, x2, y2 = region.crop_box(100, 100)
        screenshot[y1:y2, x1:x2] = template

    detector = CardDetector(tmp_path, threshold=0.90)

    hero, board = detector.detect_hero_and_board(screenshot, _layout())

    assert hero == ["Ah", "Kh"]
    assert board == ["Qs", "Js", "2d", "4c", "5s"]


def test_invalid_screenshot_is_rejected(tmp_path: Path) -> None:
    template = _pattern(10)
    assert cv2.imwrite(str(tmp_path / "Ah.png"), template)
    detector = CardDetector(tmp_path)

    with pytest.raises(ValueError, match="three-channel uint8"):
        detector.detect_hero_and_board(np.zeros((100, 100), dtype=np.uint8), _layout())
