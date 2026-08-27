"""Ollama Local AI Provider Client and Local Fallback Analyzer."""

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from src.domain.ai_models import AIStatus, Analysis, AnalysisType
from src.utilities.exceptions import StudioAIError
from src.utilities.logging import get_logger

logger = get_logger()


class OllamaProvider:
    """Ollama local AI client for qwen3:8b REST endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:8b",
        timeout_seconds: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def check_health(self) -> AIStatus:
        """Probe Ollama server and verify model availability."""
        url = f"{self.base_url}/api/tags"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    if any(self.model in m for m in models):
                        return AIStatus.AVAILABLE
                    else:
                        logger.warning(f"Ollama reachable but model '{self.model}' not found in {models}")
                        return AIStatus.UNAVAILABLE
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError) or "timed out" in str(e).lower():
                return AIStatus.TIMEOUT
            logger.info(f"Ollama server offline or unreachable at {self.base_url}: {e}")
            return AIStatus.OFFLINE
        except Exception as e:
            logger.error(f"Error probing Ollama server: {e}")
            return AIStatus.UNAVAILABLE

        return AIStatus.UNAVAILABLE

    def generate_json_response(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Call Ollama /api/generate with format='json'."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "format": "json",
            "stream": False,
        }

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if resp.status == 200:
                    raw_res = json.loads(resp.read().decode("utf-8"))
                    response_text = raw_res.get("response", "{}")
                    parsed = json.loads(response_text)
                    return parsed
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError) or "timed out" in str(e).lower():
                raise StudioAIError(f"Ollama AI request timed out after {self.timeout_seconds}s.")
            raise StudioAIError(f"Ollama connection error: {e}") from e
        except Exception as e:
            raise StudioAIError(f"Ollama API call failed: {e}") from e

        return {}


class LocalFallbackAnalyzer:
    """Deterministic local fallback story analyzer when Ollama is offline or local-only mode is active."""

    def analyze_story_locally(
        self, project_id: str, chapter_id: str, text: str, source_hash: str
    ) -> Analysis:
        """Perform heuristic rule-based local analysis."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        first_p = paragraphs[0] if paragraphs else text[:200]

        summary = f"Local Summary: {first_p[:200]}..." if len(first_p) > 200 else first_p

        # Extract uppercase potential character names
        potential_chars = sorted(
            list(
                set(
                    re.findall(
                        r"\b[A-Z][a-z]+\b",
                        re.sub(r"^(The|A|An|In|On|At|When|If|Then|CHAPTER|Chapter)\b", "", text),
                    )
                )
            )
        )[:5]

        words = text.split()
        estimated_seconds = (len(words) / 150.0) * 60.0  # ~150 words per minute narration speed

        return Analysis(
            project_id=project_id,
            chapter_id=chapter_id,
            summary=summary,
            characters=potential_chars,
            character_details={c: "Character extracted locally" for c in potential_chars},
            locations=["Local Scene Location"],
            events=[f"Event in paragraph {i+1}" for i in range(min(3, len(paragraphs)))],
            scenes=[{"paragraph_index": i, "excerpt": p[:100]} for i, p in enumerate(paragraphs[:3])],
            tone="Neutral / Narrative",
            mood="Dramatic",
            themes=["Story Theme"],
            dialogue=[],
            narration=[p for p in paragraphs],
            hooks=[paragraphs[0][:100]] if paragraphs else [],
            visual_opportunities=["Character introduced", "Climactic moment"],
            estimated_duration_seconds=round(estimated_seconds, 2),
            analysis_type=AnalysisType.LOCAL_FALLBACK,
            model_used="LOCAL_FALLBACK",
            source_text_hash=source_hash,
        )
