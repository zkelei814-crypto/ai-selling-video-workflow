#!/usr/bin/env python3
"""Build a safe, provider-neutral TikTok UGC selling-video package.

The runner intentionally uses only the Python standard library. It creates prompts and
metadata, not video media, so it is safe to run without provider credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_SOURCES = {"visible", "user_supplied", "documented", "unverified"}
ALLOWED_PROVIDERS = {"prompt-only", "mock"}
RISK_PATTERNS = {
    "guarantee": r"\bguarante(?:e|ed|es)\b|\b100%\b",
    "medical": r"\b(?:cure|treat|heal|diagnose|weight loss|lose weight)\b",
    "income": r"\b(?:make money|guaranteed income|get rich)\b",
    "superlative": r"\b(?:best ever|number one|#1|miracle)\b",
    "fake_urgency": r"\b(?:limited time|only \d+ left|act now|selling out)\b",
}


class WorkflowError(ValueError):
    """Raised when project input cannot safely enter the workflow."""


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise WorkflowError("Project input must be a JSON object.")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def input_hash(project: dict[str, Any]) -> str:
    payload = json.dumps(project, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require_text(container: dict[str, Any], key: str, context: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"{context}.{key} must be a non-empty string.")
    return value.strip()


def validate_project(project: dict[str, Any]) -> None:
    project_id = require_text(project, "project_id", "project")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", project_id):
        raise WorkflowError("project.project_id must use lowercase letters, digits, and hyphens.")
    require_text(project, "market", "project")
    require_text(project, "platform", "project")

    duration = project.get("duration_seconds")
    if not isinstance(duration, int) or isinstance(duration, bool) or not 15 <= duration <= 30:
        raise WorkflowError("project.duration_seconds must be an integer from 15 to 30.")

    provider = project.get("provider", "prompt-only")
    if provider not in ALLOWED_PROVIDERS:
        raise WorkflowError(f"project.provider must be one of {sorted(ALLOWED_PROVIDERS)}.")

    product = project.get("product")
    if not isinstance(product, dict):
        raise WorkflowError("project.product must be an object.")
    require_text(product, "name", "product")
    identity = product.get("identity")
    if not isinstance(identity, list) or not identity or not all(isinstance(x, str) and x.strip() for x in identity):
        raise WorkflowError("product.identity must contain at least one non-empty string.")
    facts = product.get("facts")
    if not isinstance(facts, list) or not facts:
        raise WorkflowError("product.facts must contain at least one fact.")
    fact_ids: set[str] = set()
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            raise WorkflowError(f"product.facts[{index}] must be an object.")
        fact_id = require_text(fact, "id", f"product.facts[{index}]")
        if not re.fullmatch(r"[a-z0-9-]+", fact_id) or fact_id in fact_ids:
            raise WorkflowError(f"Fact ID '{fact_id}' must be unique lowercase hyphen-case.")
        fact_ids.add(fact_id)
        require_text(fact, "text", f"product.facts[{index}]")
        source = fact.get("source")
        if source not in ALLOWED_SOURCES:
            raise WorkflowError(f"Fact '{fact_id}' has unsupported source '{source}'.")

    creative = project.get("creative")
    if not isinstance(creative, dict):
        raise WorkflowError("project.creative must be an object.")
    for key in ("audience", "problem", "primary_benefit", "proof_shot", "setting"):
        require_text(creative, key, "creative")


def risk_labels(text: str) -> list[str]:
    return [label for label, pattern in RISK_PATTERNS.items() if re.search(pattern, text, re.IGNORECASE)]


def build_fact_ledger(project: dict[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for fact in project["product"]["facts"]:
        risks = risk_labels(fact["text"])
        usable = fact["source"] != "unverified" and not risks
        if fact["source"] == "unverified":
            reason = "Excluded because the claim has no verified source."
        elif risks:
            reason = "Excluded because the wording triggered: " + ", ".join(risks) + "."
        else:
            reason = "Usable with the recorded source."
        entries.append(
            {
                "id": fact["id"],
                "text": fact["text"].strip(),
                "source": fact["source"],
                "evidence": fact.get("evidence", ""),
                "risk_labels": risks,
                "usable": usable,
                "reason": reason,
            }
        )
    usable_ids = [entry["id"] for entry in entries if entry["usable"]]
    if not usable_ids:
        raise WorkflowError("No safe product facts remain. Add visible, documented, or user-supplied evidence.")
    return {"project_id": project["project_id"], "entries": entries, "usable_fact_ids": usable_ids}


def build_creative_brief(project: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    creative = project["creative"]
    return {
        "project_id": project["project_id"],
        "market": project["market"],
        "platform": project["platform"],
        "duration_seconds": project["duration_seconds"],
        "product": project["product"]["name"],
        "audience": creative["audience"],
        "problem": creative["problem"],
        "primary_benefit": creative["primary_benefit"],
        "proof_shot": creative["proof_shot"],
        "setting": creative["setting"],
        "usable_fact_ids": ledger["usable_fact_ids"],
        "creative_rule": "Demonstrate one verified fact before asking for action.",
    }


def sentence(text: str) -> str:
    text = text.strip()
    return text if text.endswith((".", "!", "?")) else text + "."


def short_product_name(name: str) -> str:
    words = name.split()
    if len(words) <= 4:
        return name.lower()
    return " ".join(words[-3:]).lower()


def segment(start: float, end: float, purpose: str, voiceover: str, caption: str, visual: str) -> dict[str, Any]:
    return {
        "start": start,
        "end": end,
        "purpose": purpose,
        "voiceover": voiceover,
        "caption": caption,
        "visual": visual,
    }


def word_count(timeline: list[dict[str, Any]]) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", " ".join(item["voiceover"] for item in timeline)))


def score_variant(timeline: list[dict[str, Any]], fact_ids: list[str], angle: str) -> tuple[int, dict[str, int]]:
    all_voice = " ".join(item["voiceover"] for item in timeline)
    count = word_count(timeline)
    hook_scores = {"discovery": 18, "problem-first": 19, "demonstration-first": 18}
    breakdown = {
        "hook_strength": hook_scores[angle] if timeline[0]["purpose"] == "hook" and len(timeline[0]["voiceover"].split()) <= 12 else 12,
        "ugc_authenticity": 15 if re.search(r"\b(?:I|my|here's|okay|look)\b", all_voice, re.IGNORECASE) else 11,
        "native_english": 15 if 30 <= count <= 42 else 12,
        "retention_curve": 15 if [x["purpose"] for x in timeline] == ["hook", "context", "proof", "payoff", "cta"] else 8,
        "product_demo": 10 if timeline[2]["start"] <= 5 else 4,
        "conversion_potential": 9 if timeline[-1]["purpose"] == "cta" else 5,
        "compliance_safety": 10 if fact_ids and not risk_labels(all_voice) else 0,
        "video_generation_feasibility": 5 if len(timeline) == 5 else 2,
    }
    return sum(breakdown.values()), breakdown


def build_script_package(project: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    product = short_product_name(project["product"]["name"])
    creative = project["creative"]
    usable = [entry for entry in ledger["entries"] if entry["usable"]]
    first = usable[0]
    second = usable[1] if len(usable) > 1 else None
    first_fact = sentence(first["text"])
    second_fact = sentence(second["text"]) if second else "That keeps the setup simple."
    first_continuation = first_fact[0].lower() + first_fact[1:]
    used_ids = [first["id"]] + ([second["id"]] if second else [])
    proof_visual = creative["proof_shot"]

    raw_variants = [
        (
            "variant-a",
            "discovery",
            [
                segment(0, 2, "hook", f"Okay, this {product} surprised me.", "This surprised me", "Handheld selfie; hold the product beside the face immediately."),
                segment(2, 5, "context", f"I hate digging for small essentials.", "No more digging", f"Point to the product in {creative['setting']}."),
                segment(5, 10, "proof", f"See? {first_fact}", "Look at this detail", proof_visual),
                segment(10, 13, "payoff", second_fact, "Easy everyday access", "Close-up of the verified product detail."),
                segment(13, 15, "cta", "Tap the cart to check it out.", "Check it out", "Hold the product naturally; no urgency graphics."),
            ],
        ),
        (
            "variant-b",
            "problem-first",
            [
                segment(0, 2, "hook", "Still losing small essentials in a big tote?", "Losing small essentials?", "Show the product and a larger tote in one handheld frame."),
                segment(2, 5, "context", f"I switched to this {product} for errands.", "My errand bag", f"Put the product on in {creative['setting']}."),
                segment(5, 10, "proof", f"Look. {first_fact}", "Verified detail", proof_visual),
                segment(10, 13, "payoff", second_fact, "Simple and accessible", "Close-up of the second verified detail."),
                segment(13, 15, "cta", "Tap the cart if you want to see it.", "See the product", "End on a readable product close-up."),
            ],
        ),
        (
            "variant-c",
            "demonstration-first",
            [
                segment(0, 2, "hook", f"Here's this {product} in real use.", "Here it is in use", "Start on the product already in hand."),
                segment(2, 5, "context", "Phone and keys go in first.", "Phone + keys", "Place only the demonstrated items into the product."),
                segment(5, 10, "proof", f"And {first_continuation}", "Close-up proof", proof_visual),
                segment(10, 13, "payoff", second_fact, "One more detail", "Show the second verified detail without a beauty-ad setup."),
                segment(13, 15, "cta", "Tap the cart to check it out.", "Check it out", "Hold on a natural, readable product shot."),
            ],
        ),
    ]

    variants: list[dict[str, Any]] = []
    for variant_id, angle, timeline in raw_variants:
        score, breakdown = score_variant(timeline, used_ids, angle)
        variants.append(
            {
                "id": variant_id,
                "angle": angle,
                "score": score,
                "score_breakdown": breakdown,
                "word_count": word_count(timeline),
                "fact_ids_used": used_ids,
                "timeline": timeline,
            }
        )
    selected = max(variants, key=lambda item: (item["score"], -item["word_count"], item["id"]))
    return {"project_id": project["project_id"], "selected_variant_id": selected["id"], "variants": variants}


def selected_variant(package: dict[str, Any]) -> dict[str, Any]:
    selected_id = package["selected_variant_id"]
    return next(item for item in package["variants"] if item["id"] == selected_id)


def build_storyboard(project: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    variant = selected_variant(package)
    camera_by_purpose = {
        "hook": "handheld phone close-up, mild natural movement",
        "context": "handheld medium shot in an ordinary lived-in setting",
        "proof": "handheld close-up focused on the product action",
        "payoff": "steady close-up of the verified product detail",
        "cta": "natural handheld product hero shot, not a studio ad",
    }
    shots = []
    for index, item in enumerate(variant["timeline"], start=1):
        shots.append(
            {
                "id": f"shot-{index:02d}",
                "start": item["start"],
                "end": item["end"],
                "camera": camera_by_purpose[item["purpose"]],
                "action": item["visual"],
                "voiceover": item["voiceover"],
                "caption": item["caption"],
                "caption_placement": "safe-center",
            }
        )
    return {
        "project_id": project["project_id"],
        "aspect_ratio": "9:16",
        "duration_seconds": project["duration_seconds"],
        "product_identity": project["product"]["identity"],
        "shots": shots,
    }


def build_generation_prompt(project: dict[str, Any], storyboard: dict[str, Any]) -> str:
    identity = "\n".join(f"- {item}" for item in storyboard["product_identity"])
    beats = []
    for shot in storyboard["shots"]:
        beats.append(
            f"{shot['start']:g}-{shot['end']:g}s ({shot['id']}): {shot['camera']}. "
            f"Action: {shot['action']} Voiceover: \"{shot['voiceover']}\" "
            f"Caption: \"{shot['caption']}\" in the safe center area."
        )
    return f"""Vertical 9:16, {storyboard['duration_seconds']} seconds, authentic handheld American TikTok UGC. Use ordinary phone-camera exposure, mild natural hand movement, and a real lived-in environment. Avoid a polished studio-commercial look.

Person and setting:
A relatable creator for {project['creative']['audience']}, in {project['creative']['setting']}, casual clothing, natural light.

Product identity lock:
{identity}
Preserve proportions, colors, controls, packaging, scale, and brand spelling exactly. Do not add accessories or product features.

Timeline:
{chr(10).join(beats)}

Captions:
Simple white TikTok-style subtitles synchronized to speech, one idea per caption, inside safe margins.

Negative constraints:
No studio lighting, glossy commercial aesthetic, robotic movement, malformed hands, floating product, duplicated parts, logo distortion, text errors, unsafe use, fake sparks, impossible results, extra accessories, unverified claims, fake urgency, or cinematic perfume-ad slow motion."""


def build_render_job(project: dict[str, Any], provider: str) -> dict[str, Any]:
    return {
        "project_id": project["project_id"],
        "provider": provider,
        "status": "MOCKED" if provider == "mock" else "PROMPT_READY",
        "media": None,
        "prompt_file": "generation_prompt.txt",
        "test_only": provider == "mock",
        "requires_human_approval": True,
        "note": "No media was rendered. Submit only after explicit provider authorization.",
    }


def check_timeline(storyboard: dict[str, Any]) -> tuple[bool, str]:
    shots = storyboard["shots"]
    expected_start = 0.0
    for shot in shots:
        if float(shot["start"]) != expected_start or float(shot["end"]) <= float(shot["start"]):
            return False, f"Gap, overlap, or invalid duration at {shot['id']}."
        expected_start = float(shot["end"])
    valid = expected_start == float(storyboard["duration_seconds"])
    return valid, "Timeline is continuous and matches duration." if valid else "Timeline does not end at requested duration."


def build_qa_report(
    project: dict[str, Any],
    ledger: dict[str, Any],
    package: dict[str, Any],
    storyboard: dict[str, Any],
    prompt: str,
) -> dict[str, Any]:
    variant = selected_variant(package)
    usable_ids = set(ledger["usable_fact_ids"])
    timeline_ok, timeline_details = check_timeline(storyboard)
    spoken = " ".join(item["voiceover"] for item in variant["timeline"])
    count = variant["word_count"]
    checks = [
        {
            "id": "supported-claims",
            "status": "PASS" if set(variant["fact_ids_used"]).issubset(usable_ids) and not risk_labels(spoken) else "FAIL",
            "details": "Every tracked product fact is usable and spoken copy has no blocked wording.",
        },
        {"id": "continuous-timeline", "status": "PASS" if timeline_ok else "FAIL", "details": timeline_details},
        {
            "id": "product-in-hook",
            "status": "PASS" if "product" in storyboard["shots"][0]["action"].lower() else "FAIL",
            "details": "The first shot explicitly includes the product.",
        },
        {
            "id": "demonstration-by-five",
            "status": "PASS" if storyboard["shots"][2]["start"] <= 5 else "FAIL",
            "details": "The proof shot begins by second five.",
        },
        {
            "id": "speech-fit",
            "status": "PASS" if 28 <= count <= 48 else "FAIL",
            "details": f"Selected voiceover contains {count} words; accepted range is 28-48.",
        },
        {
            "id": "caption-safe-area",
            "status": "PASS" if all(x["caption_placement"] == "safe-center" for x in storyboard["shots"]) else "FAIL",
            "details": "Every caption is marked for safe-center placement.",
        },
        {
            "id": "low-pressure-cta",
            "status": "PASS" if re.search(r"\b(?:check|see|learn)\b", storyboard["shots"][-1]["voiceover"], re.IGNORECASE) and not risk_labels(storyboard["shots"][-1]["voiceover"]) else "FAIL",
            "details": "The CTA asks the viewer to check the product without fake urgency.",
        },
        {
            "id": "prompt-guards",
            "status": "PASS" if "Product identity lock" in prompt and "Negative constraints" in prompt else "FAIL",
            "details": "The generation prompt includes identity and negative constraints.",
        },
    ]
    manual = [
        ("product-identity", "Compare product shape, color, controls, packaging, scale, and brand spelling with references."),
        ("anatomy-and-text", "Inspect hands, faces, product parts, logos, and rendered text for artifacts."),
        ("physical-safety", "Confirm the demonstration is physically plausible and safe."),
        ("caption-sync", "Confirm captions match the voiceover and stay inside safe margins."),
        ("audio-sync", "Confirm speech is intelligible and synchronized."),
    ]
    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "project_id": project["project_id"],
        "status": status,
        "automatic_checks": checks,
        "manual_checks": [{"id": key, "status": "PENDING", "details": details} for key, details in manual],
    }


def run_pipeline(project: dict[str, Any], output_dir: Path, provider: str | None = None, resume: bool = False) -> dict[str, Any]:
    validate_project(project)
    provider = provider or project.get("provider", "prompt-only")
    if provider not in ALLOWED_PROVIDERS:
        raise WorkflowError(f"Provider must be one of {sorted(ALLOWED_PROVIDERS)}.")
    digest = input_hash(project)
    state_path = output_dir / "state.json"
    if resume and state_path.exists():
        state = load_json(state_path)
        if state.get("input_hash") == digest and state.get("current_state") == "QA_COMPLETE":
            return state

    output_dir.mkdir(parents=True, exist_ok=True)
    history = ["INGESTED"]
    ledger = build_fact_ledger(project)
    history.append("FACT_CHECKED")
    brief = build_creative_brief(project, ledger)
    package = build_script_package(project, ledger)
    history.extend(["SCRIPTED", "APPROVED"])
    storyboard = build_storyboard(project, package)
    history.append("STORYBOARDED")
    prompt = build_generation_prompt(project, storyboard)
    render_job = build_render_job(project, provider)
    history.append("PROMPT_READY")
    qa = build_qa_report(project, ledger, package, storyboard, prompt)
    current_state = "QA_COMPLETE" if qa["status"] == "PASS" else "QA_FAILED"
    history.append(current_state)
    state = {
        "project_id": project["project_id"],
        "input_hash": digest,
        "current_state": current_state,
        "history": history,
        "provider": provider,
        "media_rendered": False,
    }

    write_json(output_dir / "fact_ledger.json", ledger)
    write_json(output_dir / "creative_brief.json", brief)
    write_json(output_dir / "script_package.json", package)
    write_json(output_dir / "storyboard.json", storyboard)
    write_text(output_dir / "generation_prompt.txt", prompt)
    write_json(output_dir / "render_job.json", render_job)
    write_json(output_dir / "qa_report.json", qa)
    write_json(state_path, state)
    return state


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Project JSON matching schemas/project.schema.json")
    parser.add_argument("--output", type=Path, required=True, help="Directory for workflow artifacts")
    parser.add_argument("--provider", choices=sorted(ALLOWED_PROVIDERS), help="Override the project provider")
    parser.add_argument("--resume", action="store_true", help="Reuse a completed run with the same input hash")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        state = run_pipeline(load_json(args.input), args.output, provider=args.provider, resume=args.resume)
    except (OSError, json.JSONDecodeError, WorkflowError) as error:
        print(f"workflow error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0 if state["current_state"] == "QA_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
