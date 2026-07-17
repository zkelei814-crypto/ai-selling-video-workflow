# Provider contract

Provider adapters consume an approved storyboard and return a render-job record.

Required input:

- project ID
- 9:16 aspect ratio
- duration
- product identity lock
- timestamped shots and exact voiceover
- caption policy
- negative constraints

Required output:

```json
{
  "provider": "prompt-only",
  "status": "PROMPT_READY",
  "media": null,
  "prompt_file": "generation_prompt.txt",
  "requires_human_approval": true
}
```

`prompt-only` creates a provider-neutral prompt. `mock` is test-only and creates no media. A future live adapter must be explicitly authorized, store the provider job ID, poll asynchronously, preserve the original prompt, and distinguish `SUBMITTED`, `RUNNING`, `FAILED`, and `RENDERED`.

Never infer provider success from an accepted HTTP request. Mark `RENDERED` only after a media artifact is returned and verified.
