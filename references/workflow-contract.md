# Workflow contract

## State machine

Advance through these states in order:

`INGESTED -> FACT_CHECKED -> SCRIPTED -> APPROVED -> STORYBOARDED -> PROMPT_READY -> QA_COMPLETE`

Use `NEEDS_INPUT` when required information or safe facts are missing. Use `QA_FAILED` when a deterministic check fails. Prompt-only and mock providers must never emit `RENDERED`.

## Canonical 15-second timeline

| Time | Purpose | Required evidence |
|---|---|---|
| 0-2s | Hook | Product visible and idea understandable without sound |
| 2-5s | Context | One audience problem and product introduction |
| 5-10s | Proof | One safe use action and one close-up detail |
| 10-13s | Payoff | Practical outcome without exaggeration |
| 13-15s | CTA | Low-pressure next step |

Target 30-45 English words. Extend to 20-30 seconds only when a safe demonstration needs more time.

## Artifact ownership

- `fact_ledger.json`: source of truth for usable claims.
- `creative_brief.json`: one audience, problem, benefit, proof, and setting.
- `script_package.json`: three variants plus the selected variant ID.
- `storyboard.json`: timed, provider-neutral visual and audio instructions.
- `generation_prompt.txt`: ready-to-paste prompt built only from approved artifacts.
- `render_job.json`: provider handoff status; never a claim that media exists.
- `qa_report.json`: deterministic results and pending manual checks.
- `state.json`: input hash, current state, and history for resume behavior.

Do not silently change approved facts or the selected script after `APPROVED`. Create a new run when material inputs change.
