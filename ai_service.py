import json
import os
import re
from typing import Any, Dict, List

import httpx


INFERENCE_URL = "https://inference.do-ai.run/v1/chat/completions"
MODEL_NAME = os.getenv("DO_INFERENCE_MODEL", "anthropic-claude-4.6-sonnet")


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


def _coerce_unstructured_payload(raw_text: str) -> dict[str, object]:
    compact = raw_text.strip()
    normalized = compact.replace("\n", ",")
    tags = [part.strip(" -•\t") for part in normalized.split(",") if part.strip(" -•\t")]
    if not tags:
        tags = ["guided plan", "saved output", "shareable insight"]
    headline = tags[0].title()
    items = []
    for index, tag in enumerate(tags[:3], start=1):
        items.append({
            "title": f"Stage {index}: {tag.title()}",
            "detail": f"Use {tag} to move the request toward a demo-ready outcome.",
            "score": min(96, 80 + index * 4),
        })
    highlights = [tag.title() for tag in tags[:3]]
    return {
        "note": "Model returned plain text instead of JSON",
        "raw": compact,
        "text": compact,
        "summary": compact or f"{headline} fallback is ready for review.",
        "tags": tags[:6],
        "items": items,
        "score": 88,
        "insights": [f"Lead with {headline} on the first screen.", "Keep one clear action visible throughout the flow."],
        "next_actions": ["Review the generated plan.", "Save the strongest output for the demo finale."],
        "highlights": highlights,
    }

def _normalize_inference_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return _coerce_unstructured_payload(str(payload))
    normalized = dict(payload)
    summary = str(normalized.get("summary") or normalized.get("note") or "AI-generated plan ready")
    raw_items = normalized.get("items")
    items: list[dict[str, object]] = []
    if isinstance(raw_items, list):
        for index, entry in enumerate(raw_items[:3], start=1):
            if isinstance(entry, dict):
                title = str(entry.get("title") or f"Stage {index}")
                detail = str(entry.get("detail") or entry.get("description") or title)
                score = float(entry.get("score") or min(96, 80 + index * 4))
            else:
                label = str(entry).strip() or f"Stage {index}"
                title = f"Stage {index}: {label.title()}"
                detail = f"Use {label} to move the request toward a demo-ready outcome."
                score = float(min(96, 80 + index * 4))
            items.append({"title": title, "detail": detail, "score": score})
    if not items:
        items = _coerce_unstructured_payload(summary).get("items", [])
    raw_insights = normalized.get("insights")
    if isinstance(raw_insights, list):
        insights = [str(entry) for entry in raw_insights if str(entry).strip()]
    elif isinstance(raw_insights, str) and raw_insights.strip():
        insights = [raw_insights.strip()]
    else:
        insights = []
    next_actions = normalized.get("next_actions")
    if isinstance(next_actions, list):
        next_actions = [str(entry) for entry in next_actions if str(entry).strip()]
    else:
        next_actions = []
    highlights = normalized.get("highlights")
    if isinstance(highlights, list):
        highlights = [str(entry) for entry in highlights if str(entry).strip()]
    else:
        highlights = []
    if not insights and not next_actions and not highlights:
        fallback = _coerce_unstructured_payload(summary)
        insights = fallback.get("insights", [])
        next_actions = fallback.get("next_actions", [])
        highlights = fallback.get("highlights", [])
    return {
        **normalized,
        "summary": summary,
        "items": items,
        "score": float(normalized.get("score") or 88),
        "insights": insights,
        "next_actions": next_actions,
        "highlights": highlights,
    }


async def _call_inference(messages: List[Dict[str, str]], max_tokens: int = 512) -> Dict[str, Any]:
    token = os.getenv("GRADIENT_MODEL_ACCESS_KEY", "") or os.getenv("DIGITALOCEAN_INFERENCE_KEY", "")
    if not token:
        return {
            "note": "AI is temporarily unavailable because the inference API key is missing.",
            "fallback": True,
        }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_completion_tokens": max(256, min(max_tokens, 2048)),
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(INFERENCE_URL, headers=headers, json=payload)
            resp.raise_for_status()
            body = resp.json()

        choices = body.get("choices", [])
        if not choices:
            return {
                "note": "AI is temporarily unavailable because no completion choices were returned.",
                "fallback": True,
            }

        message = choices[0].get("message", {})
        content = message.get("content", "")
        extracted = _extract_json(content)
        try:
            return json.loads(extracted)
        except Exception:
            return {
                "note": "AI is temporarily unavailable because the model response was not valid JSON.",
                "fallback": True,
                "raw": content[:800],
            }
    except Exception as exc:
        return {
            "note": f"AI is temporarily unavailable due to an inference error: {str(exc)}",
            "fallback": True,
        }


async def generate_meal_plan_structured(query: str, preferences: str) -> Dict[str, Any]:
    system = (
        "You are a meal-prep planning engine. Return JSON only with keys: "
        "summary, score, items, structured_brief, weekly_board, grocery_basket, prep_steps, explainability. "
        "items should be an array of 3-7 concise strings. "
        "weekly_board must be array of objects with day, slot, recipe_name, macros(protein_g,carbs_g,fat_g), "
        "prep_minutes, cost_per_serving, portions, dietary_tags, rationale. "
        "grocery_basket must be array of objects with ingredient, quantity, unit, estimated_cost, pantry. "
        "prep_steps must be array of objects with step, parallelizable, minutes, container_outputs."
    )
    user = f"Goal: {query}\nPreferences: {preferences}"
    return await _call_inference([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], max_tokens=512)


async def generate_plan_insights(selection: str, context: str) -> Dict[str, Any]:
    system = (
        "You are a meal-plan rebalance analyst. Return JSON only with keys: insights, next_actions, highlights. "
        "insights must be a list of objects with title, impact, why. "
        "next_actions must be list of short strings. highlights must include budget_delta, protein_delta, time_delta."
    )
    user = f"Selection: {selection}\nContext: {context}"
    return await _call_inference([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], max_tokens=512)
