from __future__ import annotations

import argparse
import logging
import math
import sys
import time
from pathlib import Path

from config import AppConfig
from vision.capture import WindowCapture, WindowInfo
from vision.card_detector import CardDetector


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def choose_window(capture: WindowCapture, title_hint: str) -> WindowInfo:
    windows = capture.list_windows()
    matches = [
        window
        for window in windows
        if title_hint.lower() in window.title.lower()
    ]

    if len(matches) == 1:
        return matches[0]

    if not windows:
        raise RuntimeError("No visible application windows were found.")

    print("Available windows:")
    for index, window in enumerate(windows):
        print(f"  [{index}] {window.title} ({window.width}x{window.height})")

    selection = input("Select a window number: ").strip()
    if not selection.isdigit():
        raise ValueError("Window selection must be a number.")

    index = int(selection)
    if index < 0 or index >= len(windows):
        raise IndexError("Window selection is outside the available range.")
    return windows[index]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GGPoker card recognition learning assistant (analysis only)"
    )
    parser.add_argument(
        "--window",
        default="GGPoker",
        help="Window-title text used to select a poker table.",
    )
    parser.add_argument(
        "--layout",
        default="ggpoker_default",
        help="Card-position layout name from config.py.",
    )
    parser.add_argument(
        "--template-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "templates",
        help="Directory containing card template PNG files.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.90,
        help="Normalized template-matching threshold.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.05,
        help="Minimum seconds between recognition cycles.",
    )
    parser.add_argument(
        "--timings",
        action="store_true",
        help="Log window refresh, screenshot, recognition, and total durations.",
    )
    return parser.parse_args()


def format_card(card: str) -> str:
    ranks = {"T": "10", "J": "J", "Q": "Q", "K": "K", "A": "A"}
    suits = {"h": "♥", "d": "♦", "c": "♣", "s": "♠"}
    if len(card) != 2:
        return card
    return f"{ranks.get(card[0], card[0])}{suits.get(card[1], card[1])}"


def main() -> int:
    configure_logging()
    args = parse_args()
    config = AppConfig()
    layout = config.layouts.get(args.layout)
    if layout is None:
        raise KeyError(f"Unknown layout: {args.layout}")
    if not math.isfinite(args.interval) or args.interval < 0:
        raise ValueError("Recognition interval must be finite and nonnegative.")

    with WindowCapture() as capture:
        capture.enable_dpi_awareness()
        window = choose_window(capture, args.window)
        detector = CardDetector(args.template_dir, args.threshold)

        print(f"Capturing: {window.title}")
        try:
            while True:
                cycle_start = time.perf_counter()
                refresh_start = cycle_start
                window = capture.refresh_window(window)
                refresh_done = time.perf_counter()
                screenshot = capture.capture_window(window)
                screenshot_done = time.perf_counter()
                hero, board = detector.detect_hero_and_board(screenshot, layout)
                recognition_done = time.perf_counter()
                print(
                    "\rHero:",
                    " ".join(format_card(card) for card in hero),
                    "| Board:",
                    " ".join(format_card(card) for card in board),
                    end="",
                    flush=True,
                )

                if args.timings:
                    logging.getLogger(__name__).info(
                        "window_refresh=%.2fms screenshot=%.2fms opencv=%.2fms recognition=%.2fms total=%.2fms",
                        (refresh_done - refresh_start) * 1000,
                        (screenshot_done - refresh_done) * 1000,
                        detector.last_opencv_seconds * 1000,
                        (recognition_done - screenshot_done) * 1000,
                        (recognition_done - cycle_start) * 1000,
                    )

                remaining = args.interval - (time.perf_counter() - cycle_start)
                if remaining > 0:
                    time.sleep(remaining)
        except KeyboardInterrupt:
            print("\nStopped.")
            return 0


if __name__ == "__main__":
    sys.exit(main())
