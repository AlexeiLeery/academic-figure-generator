"""Claude API integration for generating academic figure prompts."""

from __future__ import annotations

import json
import logging
import re
import time

import httpx

from app.config import get_settings
from app.core.exceptions import ExternalAPIException
from app.core.prompts.system_prompt import ACADEMIC_FIGURE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ClaudeService:
    """Integration with Claude API for generating academic figure prompts."""

    def __init__(self, api_key: str | None = None, api_base_url: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        # Priority: explicit param → default Anthropic endpoint
        self.api_url = (
            api_base_url.rstrip("/") + "/v1/messages"
            if api_base_url
            else "https://api.anthropic.com/v1/messages"
        )

        if not self.api_key:
            raise ExternalAPIException(
                "Claude", "No API key configured. Provide a BYOK key or set CLAUDE_API_KEY."
            )

    # ------------------------------------------------------------------
    # Public API (synchronous -- intended for Celery tasks)
    # ------------------------------------------------------------------

    def generate_figure_prompts(
        self,
        sections: list[dict],
        color_scheme: dict,
        paper_field: str | None = None,
    ) -> dict:
        """Call Claude API synchronously to generate figure prompts.

        Parameters
        ----------
        sections:
            List of section dicts with ``title`` and ``content`` keys,
            as returned by ``DocumentService.parse()``.
        color_scheme:
            Dict with color keys (``primary``, ``secondary``, etc.).
        paper_field:
            Optional academic field context (e.g., "computer vision").

        Returns
        -------
        dict
            ``{"figures": list[dict], "input_tokens": int, "output_tokens": int, "model": str}``

        Raises
        ------
        ExternalAPIException
            On any API communication failure.
        """
        system = ACADEMIC_FIGURE_SYSTEM_PROMPT
        user_message = self._build_user_message(sections, color_scheme, paper_field)

        start_time = time.monotonic()

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    self.api_url,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": self.max_tokens,
                        "system": system,
                        "messages": [{"role": "user", "content": user_message}],
                    },
                )
                response.raise_for_status()
                result = response.json()
        except httpx.TimeoutException as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error("Claude API timeout after %d ms: %s", duration_ms, exc)
            raise ExternalAPIException(
                "Claude", f"Request timed out after {duration_ms}ms"
            ) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            detail = exc.response.text[:500]
            logger.error("Claude API HTTP %d: %s", status, detail)
            raise ExternalAPIException(
                "Claude", f"HTTP {status}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Claude API error: %s", exc)
            raise ExternalAPIException("Claude", str(exc)) from exc

        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Extract text from response content blocks
        content_blocks = result.get("content", [])
        content_text = ""
        for block in content_blocks:
            if block.get("type") == "text":
                content_text += block.get("text", "")

        figures = self._parse_figures_response(content_text)

        usage = result.get("usage", {})
        logger.info(
            "Claude API call completed in %d ms: %d figures, %d input tokens, %d output tokens",
            duration_ms,
            len(figures),
            usage.get("input_tokens", 0),
            usage.get("output_tokens", 0),
        )

        return {
            "figures": figures,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "model": self.model,
            "duration_ms": duration_ms,
        }

    # ------------------------------------------------------------------
    # Message construction
    # ------------------------------------------------------------------

    def _build_user_message(
        self,
        sections: list[dict],
        color_scheme: dict,
        paper_field: str | None,
    ) -> str:
        """Build the user message with paper sections and color palette."""
        parts: list[str] = []

        # Paper field context
        if paper_field:
            parts.append(f"**Academic Field:** {paper_field}\n")

        # Color palette
        parts.append("**Color Palette to Use:**")
        for color_key, color_value in color_scheme.items():
            parts.append(f"  - {color_key}: {color_value}")
        parts.append("")

        # Paper content (sections)
        parts.append("**Paper Content (organized by section):**\n")
        for i, section in enumerate(sections, 1):
            title = section.get("title", f"Section {i}")
            level = section.get("level", 1)
            content = section.get("content", "")

            # Truncate very long sections to avoid token overflow
            max_section_chars = 8000
            if len(content) > max_section_chars:
                content = content[:max_section_chars] + "\n[... section truncated ...]"

            heading_prefix = "#" * min(level + 1, 4)  # ## to ####
            parts.append(f"{heading_prefix} {title}")
            parts.append(content)
            parts.append("")

        parts.append(
            "---\n"
            "Based on the paper content above, generate a comprehensive set of "
            "academic figures. For each figure, provide a detailed image-generation "
            "prompt that incorporates the specified color palette. Return ONLY a "
            "JSON array of figure objects."
        )

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_figures_response(self, text: str) -> list[dict]:
        """Extract and validate the JSON array of figure dicts from Claude's response.

        Handles cases where the model wraps JSON in markdown code fences.
        """
        if not text or not text.strip():
            logger.warning("Empty response from Claude API")
            return []

        cleaned = text.strip()

        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            # Remove opening fence (```json or ```)
            first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
            cleaned = cleaned[first_newline + 1 :]
            # Remove closing fence
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3].rstrip()

        # Try direct parse first
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return self._validate_figures(parsed)
        except json.JSONDecodeError:
            pass

        # Fallback: search for JSON array in the text
        match = re.search(r"\[[\s\S]*\]", cleaned)
        if match:
            try:
                parsed = json.loads(match.group())
                if isinstance(parsed, list):
                    return self._validate_figures(parsed)
            except json.JSONDecodeError:
                pass

        logger.warning("Could not parse JSON figures from Claude response")
        return []

    @staticmethod
    def _validate_figures(figures: list) -> list[dict]:
        """Validate and normalize the list of figure dicts."""
        valid: list[dict] = []
        for i, fig in enumerate(figures):
            if not isinstance(fig, dict):
                logger.warning("Skipping non-dict figure at index %d", i)
                continue

            # Ensure required fields exist with defaults
            validated = {
                "figure_number": fig.get("figure_number", i + 1),
                "title": fig.get("title", f"Figure {i + 1}"),
                "suggested_figure_type": fig.get("suggested_figure_type", "diagram"),
                "suggested_aspect_ratio": fig.get("suggested_aspect_ratio", "16:9"),
                "prompt": fig.get("prompt", ""),
                "source_section_titles": fig.get("source_section_titles", []),
                "rationale": fig.get("rationale", ""),
            }

            # Skip figures with empty prompts
            if not validated["prompt"]:
                logger.warning(
                    "Skipping figure %d: empty prompt", validated["figure_number"]
                )
                continue

            valid.append(validated)

        return valid
