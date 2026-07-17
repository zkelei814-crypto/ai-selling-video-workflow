# Prompt: TikTok Script Analyzer

Analyze the supplied TikTok Shop UGC script for the US market. Use only claims present in the fact ledger.

## Input

- Product identity
- Target audience
- Duration
- Fact ledger with usable flags
- Script
- Visual setting

## Evaluate

1. Is the 0-2 second hook understandable without sound?
2. Does the copy sound like natural American speech rather than listing copy?
3. Does the product appear immediately and enter use by second five?
4. Does each product claim map to a usable fact ID?
5. Does the timeline add information without gaps or dead air?
6. Is the CTA low pressure and compliant?
7. Can the storyboard be generated safely with simple actions?

## Return

Return structured JSON with an overall score, the eight categories in `config/scoring_rubric.json`, weak lines, safe replacements, three hook options, three CTA options, and a complete revised timeline using `0-2 / 2-5 / 5-10 / 10-13 / 13-15`.
