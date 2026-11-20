from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from config import CardRegion, LayoutConfig
from vision.template_matcher import TemplateMatcher


class CardDetector:
    def __init__(self, template_dir: Path, threshold: float = 0.90) -> None:
        self.matcher = TemplateMatcher(template_dir, threshold)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.last_opencv_seconds = 0.0

    def _detect_region(
        self,
        screenshot: np.ndarray,
        region: CardRegion,
    ) -> tuple[str | None, float]:
        height, width = screenshot.shape[:2]
        x1, y1, x2, y2 = region.crop_box(width, height)
        crop = screenshot[y1:y2, x1:x2]
        if crop.size == 0:
            return None, -1.0
        card, score = self.matcher.match(crop)
        self.last_opencv_seconds += self.matcher.last_opencv_seconds
        self._logger.debug(
            "Card match region=(%d,%d)-(%d,%d) card=%s score=%.4f",
            x1,
            y1,
            x2,
            y2,
            card,
            score,
        )
        return card, score

    def detect_hero_and_board(
        self,
        screenshot: np.ndarray,
        layout: LayoutConfig,
    ) -> tuple[list[str], list[str]]:
        if (
            not isinstance(screenshot, np.ndarray)
            or screenshot.ndim != 3
            or screenshot.shape[2] != 3
            or screenshot.dtype != np.uint8
        ):
            raise ValueError("Screenshot must be a three-channel uint8 array.")

        self.last_opencv_seconds = 0.0
        hero: list[str] = []
        board: list[str] = []

        for region in layout.hero_regions():
            card, _ = self._detect_region(screenshot, region)
            if card is not None:
                hero.append(card)

        for region in layout.board_regions():
            card, _ = self._detect_region(screenshot, region)
            if card is not None:
                board.append(card)

        return hero, board
