from __future__ import annotations

from unittest.mock import Mock, patch

import numpy as np
import pytest

from vision.capture import WindowCapture, WindowInfo


def test_capture_reuses_mss_server_and_converts_bgra_to_bgr() -> None:
    raw_image = np.zeros((2, 3, 4), dtype=np.uint8)
    raw_image[:, :, 3] = 255
    server = Mock()
    server.grab.return_value = raw_image
    window = WindowInfo(1, "table", 10, 20, 3, 2)

    with patch("vision.capture.mss.mss", return_value=server) as create_server:
        with WindowCapture() as capture:
            first = capture.capture_window(window)
            second = capture.capture_window(window)

        create_server.assert_called_once_with()
        assert server.grab.call_count == 2
        server.close.assert_called_once_with()

    assert first.shape == (2, 3, 3)
    assert second.shape == (2, 3, 3)


def test_capture_rejects_nonpositive_window_size() -> None:
    with WindowCapture() as capture, pytest.raises(ValueError, match="dimensions"):
        capture.capture_window(WindowInfo(1, "table", 0, 0, 0, 10))
