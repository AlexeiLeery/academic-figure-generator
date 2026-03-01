"""
Preset color schemes for academic figure generation.

Each scheme is a dict mapping 8 semantic roles to hex color strings:

  primary:     Main structural elements and key component accents
  secondary:   Secondary highlights and alternate data-flow color
  tertiary:    Supporting elements, third-category color
  text:        All text and labels
  fill:        Main canvas background (must be white or near-white)
  section_bg:  Panel / sub-region background tints (very light)
  border:      Borders and separator lines
  arrow:       Flow arrows and connectors

All schemes satisfy:
  - WCAG AA contrast ratio ≥ 4.5:1 between text and fill colors
  - Okabe-Ito and Blue-Monochrome schemes are colorblind-safe
  - fill colors are ≥ 95% lightness (suitable as print backgrounds)

Usage:
    from app.core.prompts.color_schemes import PRESET_COLOR_SCHEMES, OKABE_ITO

    colors = PRESET_COLOR_SCHEMES.get("okabe_ito", OKABE_ITO)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Individual scheme definitions
# ---------------------------------------------------------------------------

# Okabe-Ito palette — recommended by Nature Methods for colorblind accessibility.
# Safe for deuteranopia (most common form of color blindness, ~6% of males).
# Default choice for CVPR / NeurIPS / Nature / Science submissions.
OKABE_ITO: dict[str, str] = {
    "primary":    "#0072B2",  # Blue       — main structural elements
    "secondary":  "#E69F00",  # Orange     — secondary highlights
    "tertiary":   "#009E73",  # Green      — third-category elements
    "text":       "#333333",  # Dark gray  — all text and labels
    "fill":       "#FFFFFF",  # White      — main canvas background
    "section_bg": "#F7F7F7",  # Off-white  — panel backgrounds
    "border":     "#CCCCCC",  # Light gray — borders and separators
    "arrow":      "#4D4D4D",  # Mid gray   — flow arrows
}

# Blue monochrome — ideal for single-color publications, module detail figures,
# and figures that must reproduce clearly in grayscale.
BLUE_MONOCHROME: dict[str, str] = {
    "primary":    "#1565C0",  # Deep blue     — main structural elements
    "secondary":  "#42A5F5",  # Light blue    — secondary highlights
    "tertiary":   "#90CAF9",  # Pale blue     — tertiary elements
    "text":       "#212121",  # Near-black    — all text and labels
    "fill":       "#FFFFFF",  # White         — main canvas background
    "section_bg": "#F5F8FC",  # Very pale blue — panel backgrounds
    "border":     "#B0BEC5",  # Blue-gray     — borders and separators
    "arrow":      "#37474F",  # Dark blue-gray — flow arrows
}

# Warm earth tones — suitable for biology, ecology, medical imaging papers.
# Evokes warmth and organic processes. Not optimized for colorblind safety;
# pair with shape encoding for accessibility.
WARM_EARTH: dict[str, str] = {
    "primary":    "#C0392B",  # Brick red    — main structural elements
    "secondary":  "#E67E22",  # Burnt orange — secondary highlights
    "tertiary":   "#F39C12",  # Amber        — tertiary elements
    "text":       "#2C2C2C",  # Charcoal     — all text and labels
    "fill":       "#FFFFFF",  # White        — main canvas background
    "section_bg": "#FDF6EC",  # Warm cream   — panel backgrounds
    "border":     "#D5C5A1",  # Sand         — borders and separators
    "arrow":      "#5D4037",  # Brown        — flow arrows
}

# Purple-green complementary — high visual contrast for data visualization,
# comparison figures, and ablation studies. Suitable for IEEE papers.
PURPLE_GREEN: dict[str, str] = {
    "primary":    "#6A1B9A",  # Deep purple  — main structural elements
    "secondary":  "#2E7D32",  # Forest green — secondary highlights
    "tertiary":   "#AB47BC",  # Medium purple — tertiary elements
    "text":       "#1A1A1A",  # Near-black   — all text and labels
    "fill":       "#FFFFFF",  # White        — main canvas background
    "section_bg": "#F8F5FC",  # Lavender tint — panel backgrounds
    "border":     "#CE93D8",  # Light purple — borders and separators
    "arrow":      "#4A148C",  # Dark purple  — flow arrows
}

# Grayscale professional — for venues requiring black-and-white figures,
# or authors who prefer maximum print compatibility. All distinctions
# encoded via lightness levels only.
GRAYSCALE: dict[str, str] = {
    "primary":    "#212121",  # Near-black   — main structural elements
    "secondary":  "#616161",  # Medium gray  — secondary highlights
    "tertiary":   "#9E9E9E",  # Light gray   — tertiary elements
    "text":       "#111111",  # Black        — all text and labels
    "fill":       "#FFFFFF",  # White        — main canvas background
    "section_bg": "#F5F5F5",  # Off-white   — panel backgrounds
    "border":     "#BDBDBD",  # Silver       — borders and separators
    "arrow":      "#424242",  # Dark gray    — flow arrows
}

# Teal-coral — modern, vibrant aesthetic popular in HCI/CHI papers.
# Good contrast between teal (cool) and coral (warm). Not optimal for
# deuteranopia; pair with patterns for full colorblind safety.
TEAL_CORAL: dict[str, str] = {
    "primary":    "#00695C",  # Dark teal    — main structural elements
    "secondary":  "#E64A19",  # Coral/red-orange — secondary highlights
    "tertiary":   "#26A69A",  # Medium teal  — tertiary elements
    "text":       "#212121",  # Near-black   — all text and labels
    "fill":       "#FFFFFF",  # White        — main canvas background
    "section_bg": "#F0F9F8",  # Pale teal tint — panel backgrounds
    "border":     "#80CBC4",  # Light teal   — borders and separators
    "arrow":      "#004D40",  # Very dark teal — flow arrows
}

# ML Top-Conference common (Matplotlib Tab10 defaults) — widely used in
# NeurIPS / ICML / ICLR plots when authors keep default matplotlib cycles.
ML_TOPCONF_TAB10: dict[str, str] = {
    "primary":    "#1F77B4",  # tab:blue
    "secondary":  "#FF7F0E",  # tab:orange
    "tertiary":   "#2CA02C",  # tab:green
    "text":       "#1F2937",  # slate-800
    "fill":       "#FFFFFF",  # White
    "section_bg": "#F8FAFC",  # slate-50
    "border":     "#CBD5E1",  # slate-300
    "arrow":      "#334155",  # slate-700
}

# ML Top-Conference common (Seaborn colorblind palette) — preserves category
# discrimination under common color-vision deficiencies.
ML_TOPCONF_COLORBLIND: dict[str, str] = {
    "primary":    "#0173B2",
    "secondary":  "#DE8F05",
    "tertiary":   "#029E73",
    "text":       "#1F2937",
    "fill":       "#FFFFFF",
    "section_bg": "#F8FAFC",
    "border":     "#CBD5E1",
    "arrow":      "#334155",
}

# ML Top-Conference common (Seaborn deep palette) — softer but still
# publication-friendly for multi-panel ablations and performance charts.
ML_TOPCONF_DEEP: dict[str, str] = {
    "primary":    "#4C72B0",
    "secondary":  "#DD8452",
    "tertiary":   "#55A868",
    "text":       "#1F2937",
    "fill":       "#FFFFFF",
    "section_bg": "#F8FAFC",
    "border":     "#CBD5E1",
    "arrow":      "#334155",
}

# ---------------------------------------------------------------------------
# Registry: maps URL-safe string keys to scheme dicts
# ---------------------------------------------------------------------------

PRESET_COLOR_SCHEMES: dict[str, dict[str, str]] = {
    "okabe-ito":      OKABE_ITO,
    "blue-monochrome": BLUE_MONOCHROME,
    "warm-earth":     WARM_EARTH,
    "purple-green":   PURPLE_GREEN,
    "grayscale":      GRAYSCALE,
    "teal-coral":     TEAL_CORAL,
    "ml-topconf-tab10": ML_TOPCONF_TAB10,
    "ml-topconf-colorblind": ML_TOPCONF_COLORBLIND,
    "ml-topconf-deep": ML_TOPCONF_DEEP,
}

# Human-readable display names for the API / frontend
COLOR_SCHEME_DISPLAY_NAMES: dict[str, str] = {
    "okabe-ito":       "Okabe-Ito (Colorblind Safe, Recommended)",
    "blue-monochrome": "Blue Monochrome (Grayscale Compatible)",
    "warm-earth":      "Warm Earth (Biology / Medical)",
    "purple-green":    "Purple-Green (High Contrast)",
    "grayscale":       "Grayscale (Print-Only)",
    "teal-coral":      "Teal-Coral (HCI / CHI)",
    "ml-topconf-tab10": "ML TopConf (Matplotlib Tab10)",
    "ml-topconf-colorblind": "ML TopConf (Seaborn Colorblind)",
    "ml-topconf-deep": "ML TopConf (Seaborn Deep)",
}

# Default scheme to use when none is specified
DEFAULT_COLOR_SCHEME: str = "okabe-ito"


def get_color_scheme(name: str, custom_overrides: dict[str, str] | None = None) -> dict[str, str]:
    """
    Retrieve a color scheme by name, optionally applying custom overrides.

    Normalizes underscores to hyphens before lookup so both ``okabe_ito``
    and ``okabe-ito`` resolve correctly.

    Args:
        name:             Key from PRESET_COLOR_SCHEMES, or "custom".
        custom_overrides: Dict of role -> hex to override specific roles.

    Returns:
        Complete 8-role color dict suitable for passing to the prompt builder.

    Raises:
        KeyError: If name is not found and no custom_overrides provided.
    """
    normalized = name.replace("_", "-")
    base = PRESET_COLOR_SCHEMES.get(normalized, OKABE_ITO).copy()
    if custom_overrides:
        # Validate that overridden keys are known roles
        valid_roles = {"primary", "secondary", "tertiary", "text", "fill",
                       "section_bg", "border", "arrow"}
        for role, value in custom_overrides.items():
            if role in valid_roles:
                base[role] = value
    return base


__all__ = [
    "OKABE_ITO",
    "BLUE_MONOCHROME",
    "WARM_EARTH",
    "PURPLE_GREEN",
    "GRAYSCALE",
    "TEAL_CORAL",
    "ML_TOPCONF_TAB10",
    "ML_TOPCONF_COLORBLIND",
    "ML_TOPCONF_DEEP",
    "PRESET_COLOR_SCHEMES",
    "COLOR_SCHEME_DISPLAY_NAMES",
    "DEFAULT_COLOR_SCHEME",
    "get_color_scheme",
]
