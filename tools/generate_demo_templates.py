"""Generate simple demo card templates for unit tests and first-run setup.

These files are not GGPoker screenshots. Replace them with calibrated,
color-neutral reference crops from the intended table layout.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

RANKS = "23456789TJQKA"
SUITS = "cdhs"
OUTPUT_SIZE = (96, 64)


def generate_templates(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for suit in SUITS:
        suit_symbol = {"c": "C", "d": "D", "h": "H", "s": "S"}[suit]
        suit_color = (40, 40, 40) if suit in "cs" else (30, 30, 180)
        for rank in RANKS:
            card = np.full((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), 245, dtype=np.uint8)
            cv2.putText(
                card,
                rank,
                (8, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                suit_color,
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                card,
                suit_symbol,
                (38, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                suit_color,
                2,
                cv2.LINE_AA,
            )
            output_path = output_dir / f"{rank}{suit}.png"
            if not cv2.imwrite(str(output_path), card):
                raise OSError(f"Unable to write demo card template: {output_path}")


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parents[1]
    generate_templates(project_dir / "templates")
    print("Generated 52 demo template PNG files.")
