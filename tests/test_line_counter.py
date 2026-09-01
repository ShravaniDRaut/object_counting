"""
Unit tests for the LineCrossingCounter geometry and logic.
"""
import pytest
from backend.ml.line_counter import LineCrossingCounter


def test_line_counter_crossing_in():
    """Test object moving downwards across a horizontal line."""
    counter = LineCrossingCounter(
        line_start=(0, 100),
        line_end=(200, 100),
        direction_mode="bidirectional"
    )

    # First point above line
    ev1 = counter.process_track(track_id=1, centroid=(100, 50), class_name="car", frame_idx=1)
    assert ev1 is None

    # Second point below line -> crossed!
    ev2 = counter.process_track(track_id=1, centroid=(100, 150), class_name="car", frame_idx=2)
    assert ev2 is not None
    assert ev2["direction"] in ["IN", "OUT"]
    assert counter.total_in + counter.total_out == 1


def test_line_counter_crossing_out():
    """Test object moving upwards across a horizontal line."""
    counter = LineCrossingCounter(
        line_start=(0, 100),
        line_end=(200, 100),
        direction_mode="bidirectional"
    )

    # First point below line
    ev1 = counter.process_track(track_id=2, centroid=(100, 150), class_name="person", frame_idx=1)
    assert ev1 is None

    # Second point above line -> crossed opposite direction!
    ev2 = counter.process_track(track_id=2, centroid=(100, 50), class_name="person", frame_idx=2)
    assert ev2 is not None
    assert counter.total_in + counter.total_out == 1


def test_line_counter_no_crossing():
    """Test object moving parallel to the line without crossing."""
    counter = LineCrossingCounter(
        line_start=(0, 100),
        line_end=(200, 100),
        direction_mode="bidirectional"
    )

    counter.process_track(track_id=3, centroid=(50, 50), class_name="car", frame_idx=1)
    ev = counter.process_track(track_id=3, centroid=(150, 50), class_name="car", frame_idx=2)
    assert ev is None
    assert counter.total_in == 0
    assert counter.total_out == 0


def test_line_counter_double_count_prevention():
    """Test that cooldown prevents the same track ID from being counted twice immediately."""
    counter = LineCrossingCounter(
        line_start=(0, 100),
        line_end=(200, 100),
        direction_mode="bidirectional",
        cooldown_frames=60
    )

    counter.process_track(track_id=4, centroid=(100, 50), class_name="truck", frame_idx=1)
    ev1 = counter.process_track(track_id=4, centroid=(100, 150), class_name="truck", frame_idx=2)
    assert ev1 is not None

    # Jitter back and forth within cooldown window
    ev2 = counter.process_track(track_id=4, centroid=(100, 50), class_name="truck", frame_idx=3)
    assert ev2 is None
    assert counter.total_in + counter.total_out == 1
