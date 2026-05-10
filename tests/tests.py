"""Basic tests for Auto-Storyboard-Video-Creator."""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.script_to_video import (
    parse_script,
    generate_storyboard,
    Storyboard,
    StoryboardFrame,
    render_frame_image,
    render_storyboard,
    script_to_storyboard,
)


class TestParseScript:
    def test_empty_script(self):
        assert parse_script("") == []
        assert parse_script("   ") == []

    def test_single_scene(self):
        result = parse_script("A hero walks into a dark forest.")
        assert len(result) == 1
        assert "hero" in result[0]["text"]

    def test_multi_scene_by_newlines(self):
        script = """INT. CASTLE - DAY

The king sits on his throne.

EXT. FOREST - NIGHT

A lone wolf howls at the moon."""
        result = parse_script(script)
        assert len(result) >= 2

    def test_scene_numbers(self):
        script = "Scene 1: Introduction\n\nScene 2: The Confrontation"
        result = parse_script(script)
        assert len(result) >= 2


class TestGenerateStoryboard:
    def test_empty_script(self):
        sb = generate_storyboard("")
        assert sb.total_frames == 0

    def test_basic_storyboard(self):
        sb = generate_storyboard("A mysterious stranger enters the bar.")
        assert sb.total_frames >= 1
        assert sb.frames[0].scene_number == 0

    def test_custom_title(self):
        sb = generate_storyboard("Test script", title="My Movie")
        assert sb.title == "My Movie"

    def test_known_characters(self):
        sb = generate_storyboard("John walks up to Mary.", known_characters=["John", "Mary"])
        frame = sb.frames[0]
        assert len(frame.characters) > 0


class TestRenderFrameImage:
    def test_render_frame(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            frame = StoryboardFrame(
                index=0,
                scene_number=1,
                description="A test scene with some description text.",
                visual_prompt="test scene",
            )
            out_path = os.path.join(tmpdir, "frame_000.png")
            result = render_frame_image(frame, out_path)
            assert os.path.exists(result)
            assert result == out_path

    def test_render_custom_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            frame = StoryboardFrame(
                index=0,
                scene_number=1,
                description="Another test.",
                visual_prompt="another test",
            )
            out_path = os.path.join(tmpdir, "frame_custom.png")
            result = render_frame_image(frame, out_path, size=(640, 480))
            assert os.path.exists(result)

            img = __import__("PIL").Image.open(result)
            assert img.size == (640, 480)
            img.close()


class TestRenderStoryboard:
    def test_render_storyboard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sb = Storyboard(title="Test")
            sb.frames = [
                StoryboardFrame(index=0, scene_number=1, description="Scene 1", visual_prompt="s1"),
                StoryboardFrame(index=1, scene_number=2, description="Scene 2", visual_prompt="s2"),
            ]
            paths = render_storyboard(sb, tmpdir)
            assert len(paths) == 2
            for p in paths:
                assert os.path.exists(p)

    def test_empty_storyboard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sb = Storyboard(title="Empty")
            paths = render_storyboard(sb, tmpdir)
            assert paths == []


class TestScriptToStoryboard:
    def test_full_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            script = "A lone spaceship drifts through the cosmos.\n\nAn alien appears at the window."
            sb = script_to_storyboard(script, output_dir=tmpdir, title="Space Tale")
            assert sb.total_frames >= 2
            assert sb.title == "Space Tale"
            for frame in sb.frames:
                assert frame.output_path is not None
                assert os.path.exists(frame.output_path)

    def test_output_files_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            script_to_storyboard("A simple test.", output_dir=tmpdir)
            files = os.listdir(tmpdir)
            assert len(files) > 0
            assert any(f.endswith(".png") for f in files)


class TestStoryboardModel:
    def test_total_frames(self):
        sb = Storyboard(title="Test")
        assert sb.total_frames == 0
        sb.frames.append(StoryboardFrame(index=0, scene_number=1, description="Test", visual_prompt="test"))
        assert sb.total_frames == 1
