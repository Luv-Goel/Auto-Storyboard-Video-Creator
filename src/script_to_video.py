"""
Script-to-video conversion module.

Takes a text script and generates storyboard frames representing
each scene or key moment described in the script.
"""

import os
import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class StoryboardFrame:
    """A single storyboard frame representing one scene."""
    index: int
    scene_number: int
    description: str
    visual_prompt: str
    camera_angle: str = "medium shot"
    lighting: str = "natural"
    mood: str = "neutral"
    characters: List[str] = field(default_factory=list)
    background: str = ""
    output_path: Optional[str] = None


@dataclass
class Storyboard:
    """Complete storyboard generated from a script."""
    title: str
    frames: List[StoryboardFrame] = field(default_factory=list)

    @property
    def total_frames(self) -> int:
        return len(self.frames)


# ---------------------------------------------------------------------------
# Script Parser
# ---------------------------------------------------------------------------


def parse_script(script_text: str) -> List[dict]:
    """
    Split a text script into individual scenes.

    Scenes can be separated by blank lines, numbered lines like
    "Scene 1:", or headers like "INT. LOCATION - DAY".
    """
    if not script_text or not script_text.strip():
        return []

    lines = script_text.strip().split("\n")
    scenes = []
    current_scene = []
    scene_num = 0

    scene_starters = re.compile(
        r"^(?:scene\s*\d+|int\.|ext\.|fade\s+(?:in|out)|cut\s+to|dissolve)",
        re.IGNORECASE
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_scene:
                scenes.append({
                    "number": scene_num,
                    "text": " ".join(current_scene),
                })
                current_scene = []
                scene_num += 1
            continue

        if scene_starters.match(stripped) and current_scene:
            scenes.append({
                "number": scene_num,
                "text": " ".join(current_scene),
            })
            current_scene = []
            scene_num += 1

        current_scene.append(stripped)

    if current_scene:
        scenes.append({
            "number": scene_num,
            "text": " ".join(current_scene),
        })

    return scenes if scenes else [{"number": 0, "text": script_text.strip()}]


# ---------------------------------------------------------------------------
# Visual Prompt Generator
# ---------------------------------------------------------------------------


def _generate_visual_prompt(scene_text: str) -> str:
    """Extract a concise visual prompt from a scene description."""
    text = scene_text.lower()

    # Remove dialogue markers
    text = re.sub(r'"[^"]*"', "", text)
    text = re.sub(r"'[^']*'", "", text)

    # Remove character names in ALL CAPS before dialogue
    text = re.sub(r'^[A-Z\s]{2,}$', "", text, flags=re.MULTILINE)

    # Clean up whitespace
    text = re.sub(r'\s+', " ", text).strip()

    # Take first 100 chars as the visual prompt
    return text[:100] if text else "generic scene"


def _extract_characters(scene_text: str, known_characters: List[str] = None) -> List[str]:
    """Extract likely character names from scene text."""
    known = known_characters or []
    found = []

    for name in known:
        if name.lower() in scene_text.lower():
            found.append(name)

    # Also look for ALL CAPS words (common in screenplays for character names)
    caps_words = re.findall(r'\b[A-Z][A-Z]+\b', scene_text)
    for w in caps_words:
        wl = w.lower()
        if wl not in ("i", "a", "an", "the", "int", "ext", "cut", "fade", "dissolve"):
            if w not in found:
                found.append(w)

    return found


def _guess_camera_angle(scene_text: str) -> str:
    """Guess camera angle from scene description keywords."""
    text = scene_text.lower()
    if any(w in text for w in ("close-up", "close up", "closeup", "extreme close")):
        return "close-up"
    if any(w in text for w in ("wide", "wide shot", "establishing", "panoramic")):
        return "wide shot"
    if any(w in text for w in ("overhead", "bird's eye", "top-down", "aerial")):
        return "overhead"
    if any(w in text for w in ("low angle", "low-angle", "looking up")):
        return "low angle"
    if any(w in text for w in ("high angle", "high-angle", "looking down")):
        return "high angle"
    if any(w in text for w in ("dutch", "tilted", "canted")):
        return "dutch angle"
    if any(w in text for w in ("over shoulder", "over-the-shoulder", "ots")):
        return "over-the-shoulder"
    return "medium shot"


def _guess_lighting(scene_text: str) -> str:
    """Guess lighting conditions from scene description keywords."""
    text = scene_text.lower()
    if any(w in text for w in ("dark", "night", "shadow", "dim", "moonlight")):
        return "dim / night"
    if any(w in text for w in ("bright", "sunny", "sunlight", "daylight", "morning")):
        return "bright / daylight"
    if any(w in text for w in ("neon", "artificial", "streetlight", "lamp")):
        return "artificial / neon"
    if any(w in text for w in ("candle", "warm", "fire", "sunset", "golden hour")):
        return "warm / golden hour"
    if any(w in text for w in ("storm", "cloudy", "overcast", "gloomy", "fog")):
        return "overcast / moody"
    return "natural"


def _guess_mood(scene_text: str) -> str:
    """Guess the mood/tone of a scene."""
    text = scene_text.lower()
    positive = ("happy", "joy", "peaceful", "hopeful", "beautiful", "love", "triumph")
    negative = ("sad", "dark", "angry", "fear", "tense", "gloomy", "tragic", "violent")
    action = ("action", "chase", "fight", "explosion", "rush", "fast", "intense")
    mystery = ("mystery", "suspense", "strange", "weird", "unknown", "curious")

    if any(w in text for w in positive):
        return "hopeful / joyful"
    if any(w in text for w in negative):
        return "dark / tense"
    if any(w in text for w in action):
        return "action / intense"
    if any(w in text for w in mystery):
        return "mysterious / suspenseful"
    return "neutral"


# ---------------------------------------------------------------------------
# Storyboard Generator
# ---------------------------------------------------------------------------


def generate_storyboard(
    script_text: str,
    title: str = "Untitled Storyboard",
    known_characters: List[str] = None,
) -> Storyboard:
    """
    Generate a full Storyboard from a text script.

    Args:
        script_text: Raw script text to parse into scenes.
        title: A title for the storyboard.
        known_characters: Optional list of character names to recognize.

    Returns:
        A Storyboard object containing parsed frames.
    """
    scenes = parse_script(script_text)
    frames = []

    for i, scene in enumerate(scenes):
        scene_text = scene["text"]
        visual_prompt = _generate_visual_prompt(scene_text)

        frame = StoryboardFrame(
            index=i,
            scene_number=scene["number"],
            description=scene_text[:200] if len(scene_text) > 200 else scene_text,
            visual_prompt=visual_prompt,
            camera_angle=_guess_camera_angle(scene_text),
            lighting=_guess_lighting(scene_text),
            mood=_guess_mood(scene_text),
            characters=_extract_characters(scene_text, known_characters),
            background=visual_prompt,
        )
        frames.append(frame)

    return Storyboard(title=title, frames=frames)


# ---------------------------------------------------------------------------
# Image Rendering
# ---------------------------------------------------------------------------

# Default frame colors
FRAME_COLORS = {
    "background": (30, 30, 40),
    "frame_bg": (45, 45, 60),
    "border": (100, 120, 200),
    "text": (220, 220, 240),
    "accent": (150, 170, 250),
    "field_label": (180, 200, 255),
    "field_value": (220, 220, 240),
}


def render_frame_image(
    frame: StoryboardFrame,
    output_path: str,
    size: Tuple[int, int] = (1280, 720),
    font_path: Optional[str] = None,
) -> str:
    """
    Render a single storyboard frame as an image.

    Args:
        frame: The StoryboardFrame to render.
        output_path: Where to save the image.
        size: Image dimensions (width, height).
        font_path: Path to a .ttf font file. Falls back to default.

    Returns:
        The path to the saved image.
    """
    width, height = size
    img = Image.new("RGB", size, FRAME_COLORS["background"])
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        if font_path and os.path.exists(font_path):
            title_font = ImageFont.truetype(font_path, 28)
            label_font = ImageFont.truetype(font_path, 20)
            value_font = ImageFont.truetype(font_path, 18)
            scene_font = ImageFont.truetype(font_path, 22)
        else:
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            scene_font = ImageFont.load_default()
    except (IOError, OSError):
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
        scene_font = ImageFont.load_default()

    # Frame border
    margin = 20
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        fill=FRAME_COLORS["frame_bg"],
        outline=FRAME_COLORS["border"],
        width=3,
    )

    # Scene number badge
    badge_x, badge_y = margin + 15, margin + 15
    badge_text = f"#{frame.index + 1}"
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + 70, badge_y + 36],
        radius=8,
        fill=FRAME_COLORS["border"],
    )
    draw.text((badge_x + 35, badge_y + 18), badge_text, fill=(255, 255, 255),
              font=title_font, anchor="mm")

    # Title area
    title_y = margin + 20
    draw.text((width // 2, title_y), f"Scene {frame.scene_number}",
              fill=FRAME_COLORS["accent"], font=title_font, anchor="mt")

    # --- Left column: metadata fields ---
    left_x = margin + 30
    fields_y_start = margin + 75
    field_height = 55

    fields = [
        ("Camera Angle", frame.camera_angle),
        ("Lighting", frame.lighting),
        ("Mood", frame.mood),
    ]

    for i, (label, value) in enumerate(fields):
        fy = fields_y_start + i * field_height
        draw.text((left_x, fy), label, fill=FRAME_COLORS["field_label"],
                  font=label_font)
        draw.text((left_x, fy + 24), value, fill=FRAME_COLORS["field_value"],
                  font=value_font)

    # Characters
    chars_y = fields_y_start + 3 * field_height + 10
    draw.text((left_x, chars_y), "Characters", fill=FRAME_COLORS["field_label"],
              font=label_font)
    chars_text = ", ".join(frame.characters) if frame.characters else "--"
    draw.text((left_x, chars_y + 24), chars_text, fill=FRAME_COLORS["field_value"],
              font=value_font)

    # --- Right column: scene description ---
    right_x = width // 2 + 20
    desc_y = margin + 75
    draw.text((right_x, desc_y), "Scene Description", fill=FRAME_COLORS["field_label"],
              font=label_font)

    # Word-wrap description
    max_text_width = width - right_x - margin - 30
    words = frame.description.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        try:
            bbox = draw.textbbox((0, 0), test_line, font=value_font)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(test_line) * 10
        if tw > max_text_width and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    line_y = desc_y + 28
    for line in lines[:12]:  # Max 12 lines
        draw.text((right_x, line_y), line, fill=FRAME_COLORS["field_value"],
                  font=value_font)
        line_y += 22

    # Visual prompt area (bottom of frame)
    prompt_y = height - margin - 60
    draw.rectangle(
        [margin + 15, prompt_y, width - margin - 15, height - margin - 15],
        fill=(55, 55, 75),
        outline=FRAME_COLORS["border"],
        width=1,
    )
    draw.text((width // 2, prompt_y + 12), f"Visual: {frame.visual_prompt[:80]}",
              fill=FRAME_COLORS["accent"], font=scene_font, anchor="mt")

    # Footer
    draw.text((width // 2, height - 10), f"Frame {frame.index + 1} — {frame.scene_number}",
              fill=(120, 120, 150), font=value_font, anchor="mb")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path)
    logger.info(f"Saved frame image: {output_path}")

    frame.output_path = output_path
    return output_path


def render_storyboard(
    storyboard: Storyboard,
    output_dir: str,
    size: Tuple[int, int] = (1280, 720),
    font_path: Optional[str] = None,
) -> List[str]:
    """
    Render all frames of a storyboard as images.

    Args:
        storyboard: The Storyboard to render.
        output_dir: Directory to save frame images.
        size: Image dimensions.
        font_path: Optional path to .ttf font.

    Returns:
        List of paths to rendered frame images.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for frame in storyboard.frames:
        filename = f"frame_{frame.index:03d}_scene_{frame.scene_number:03d}.png"
        filepath = os.path.join(output_dir, filename)
        path = render_frame_image(frame, filepath, size, font_path)
        paths.append(path)

    return paths


# ---------------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------------


def script_to_storyboard(
    script_text: str,
    output_dir: str = "storyboard_output",
    title: str = "Storyboard",
    known_characters: List[str] = None,
    size: Tuple[int, int] = (1280, 720),
    font_path: Optional[str] = None,
) -> Storyboard:
    """
    High-level function: parse a script and render its storyboard frames.

    Args:
        script_text: The full script text.
        output_dir: Directory for output images.
        title: Title for the storyboard.
        known_characters: Known character names to identify.
        size: Output image dimensions.
        font_path: Optional font path.

    Returns:
        The generated Storyboard object.
    """
    storyboard = generate_storyboard(script_text, title, known_characters)
    render_storyboard(storyboard, output_dir, size, font_path)
    return storyboard
