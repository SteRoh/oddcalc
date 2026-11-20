from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np


class TemplateMatcher:
    def __init__(self, template_dir: Path, threshold: float = 0.90) -> None:
        if not np.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("Matching threshold must be between 0 and 1.")
        self.template_dir = template_dir
        self.threshold = threshold
        self.templates: dict[str, np.ndarray] = {}
        self.last_opencv_seconds = 0.0
        self._load_templates()

    def _load_templates(self) -> None:
        if not self.template_dir.exists():
            raise FileNotFoundError(
                f"Template directory does not exist: {self.template_dir}"
            )

        for path in sorted(self.template_dir.glob("*.png")):
            card = path.stem
            if (
                len(card) != 2
                or card[0] not in "23456789TJQKA"
                or card[1] not in "cdhs"
            ):
                continue
            template = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if template is None:
                raise ValueError(f"Unable to read card template: {path}")
            if (
                template.ndim != 3
                or template.shape[2] != 3
                or not np.max(np.std(template, axis=(0, 1)))
            ):
                raise ValueError(f"Card template must contain color detail: {path}")
            self.templates[card] = template

        if not self.templates:
            raise RuntimeError(
                f"No PNG card templates found in {self.template_dir}"
            )

    def match(self, region: np.ndarray) -> tuple[str | None, float]:
        self.last_opencv_seconds = 0.0
        if (
            not isinstance(region, np.ndarray)
            or region.ndim != 3
            or region.shape[2] != 3
            or region.dtype != np.uint8
        ):
            raise ValueError("Image region must be a three-channel uint8 array.")
        if region.size == 0:
            raise ValueError("Image region must not be empty.")
        if not np.max(np.std(region, axis=(0, 1))):
            return None, -1.0

        best_card: str | None = None
        best_score = -1.0

        for card, template in self.templates.items():
            if template.shape[0] > region.shape[0] or template.shape[1] > region.shape[1]:
                continue
            match_start = time.perf_counter()
            result = cv2.matchTemplate(
                region,
                template,
                cv2.TM_CCOEFF_NORMED,
            )
            self.last_opencv_seconds += time.perf_counter() - match_start
            _, score, _, _ = cv2.minMaxLoc(result)
            if np.isfinite(score) and score > best_score:
                best_score = float(score)
                best_card = card

        if best_card is None or best_score < self.threshold:
            return None, best_score
        return best_card, best_score
