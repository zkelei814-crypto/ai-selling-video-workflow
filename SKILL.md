---
name: tiktok-script-analyzer-skill
description: Turn verified product images, facts, and selling points into production-ready US TikTok Shop UGC video packages with fact ledgers, creative briefs, hooks, 15-30 second scripts, captions, shot lists, Seedance/Sora prompts, deterministic QA, and prompt-only render jobs. Use when Codex needs to create, analyze, revise, or quality-check AI product-selling videos while preventing unsupported claims.
---

# TikTok Selling Video Workflow

Build a believable phone-shot recommendation that demonstrates verified product value before selling it.

## Workflow

1. Inspect every supplied asset. Separate visible or documented facts from unverified claims.
2. Create a fact ledger. Never use a fact whose source is `unverified` or whose wording triggers a safety risk.
3. Identify one audience, one concrete problem, one primary benefit, and one proof shot.
4. Generate three 15-second concepts: discovery, problem-first, and demonstration-first.
5. Show the product immediately, demonstrate it by second five, and use the timeline in `references/workflow-contract.md`.
6. Analyze hooks, natural US speech, compliance, and conversion using the specialized files in `prompts/`.
7. Select the strongest safe variant and create synchronized voiceover, captions, and a timestamped storyboard.
8. Build a provider-neutral generation prompt. Read `references/provider-contract.md` before producing a render job.
9. Run deterministic QA with `scripts/run_workflow.py` and apply the manual visual checks in `references/quality-gates.md`.
10. Return `PROMPT_READY` unless an authorized video provider actually returns media. Never claim that a prompt-only or mock job rendered a video.

## Deterministic runner

Run the no-API MVP from the skill root:

```bash
python scripts/run_workflow.py examples/project_input.json --output outputs/demo --provider prompt-only
```

Use `--resume` to reuse a completed run when the input hash matches. Use `mock` only in tests; it creates no media.

The runner writes, in order:

1. `fact_ledger.json`
2. `creative_brief.json`
3. `script_package.json`
4. `storyboard.json`
5. `generation_prompt.txt`
6. `render_job.json`
7. `qa_report.json`
8. `state.json`

## Gates

- Stop and request evidence when no safe product fact remains.
- Exclude unsupported price, discount, capacity, material, certification, compatibility, warranty, scarcity, review, health, or result claims.
- Keep captions in the safe center area and use one idea per caption.
- Require a low-pressure CTA without fake urgency.
- Treat product identity, hand integrity, text accuracy, physical plausibility, and audio synchronization as manual checks after rendering.
- Require human approval before spending provider credits or publishing a video.

## Script analysis mode

When a user supplies an existing script, use `prompts/script_analyzer.md`, `prompts/hook_checker.md`, `prompts/ugc_native_checker.md`, and `prompts/compliance_guard.md`. Return fixes before generating a storyboard.

## Output contract

Follow the JSON schemas in `schemas/`. Keep generated prose natural, but preserve field names and state values exactly so downstream automation can resume reliably.
