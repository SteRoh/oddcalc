from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CardRegion:
    """Card region expressed as fractions of the selected window."""

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Card region values must be finite.")
        if (
            self.x < 0
            or self.y < 0
            or self.width <= 0
            or self.height <= 0
            or self.x + self.width > 1
            or self.y + self.height > 1
        ):
            raise ValueError("Card region must fit inside the normalized window.")

    def crop_box(self, image_width: int, image_height: int) -> tuple[int, int, int, int]:
        if image_width <= 0 or image_height <= 0:
            raise ValueError("Image dimensions must be positive.")
        x1 = max(0, min(image_width - 1, round(self.x * image_width)))
        y1 = max(0, min(image_height - 1, round(self.y * image_height)))
        x2 = max(x1 + 1, min(image_width, round((self.x + self.width) * image_width)))
        y2 = max(y1 + 1, min(image_height, round((self.y + self.height) * image_height)))
        return x1, y1, x2, y2


@dataclass(frozen=True)
class LayoutConfig:
    name: str
    hero_card_1: CardRegion
    hero_card_2: CardRegion
    flop_1: CardRegion
    flop_2: CardRegion
    flop_3: CardRegion
    turn: CardRegion
    river: CardRegion

    def hero_regions(self) -> tuple[CardRegion, CardRegion]:
        return self.hero_card_1, self.hero_card_2

    def board_regions(self) -> tuple[CardRegion, ...]:
        return self.flop_1, self.flop_2, self.flop_3, self.turn, self.river


class AppConfig:
    """Central configuration. Replace demo coordinates for a real table layout."""

    def __init__(self) -> None:
        self.layouts: dict[str, LayoutConfig] = {
            "ggpoker_default": LayoutConfig(
                name="ggpoker_default",
                hero_card_1=CardRegion(0.40, 0.78, 0.055, 0.105),
                hero_card_2=CardRegion(0.46, 0.78, 0.055, 0.105),
                flop_1=CardRegion(0.36, 0.43, 0.052, 0.100),
                flop_2=CardRegion(0.42, 0.43, 0.052, 0.100),
                flop_3=CardRegion(0.48, 0.43, 0.052, 0.100),
                turn=CardRegion(0.54, 0.43, 0.052, 0.100),
                river=CardRegion(0.60, 0.43, 0.052, 0.100),
            )
        }
