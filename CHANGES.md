# Model setup update for research-assistant-template

Date: June 17, 2026

## Why

The repo pinned Gemini 1.5 model names across five files. As of June 2026 those
models are shut down and the API returns a 404 for all of them, so a fresh clone
fails on the first Gemini call. Pinned names also go stale every time Google
retires a model. Since this repo is a template meant to get users started, the
fix is to stop depending on any single hardcoded name.

## New approach

The scripts now auto-detect a working model from the user's API key, and there
is one place to override it.

- New file `ai_config.py` holds `MODEL_NAME`, a `PREFERRED_MODELS` fallback list,
  and a shared `setup_gemini()` that asks the API which models the key can call,
  then picks one. It survives future model retirements without code edits.
- Default model: `gemini-2.5-flash-lite`. Override by editing `MODEL_NAME` or by
  setting the `GEMINI_MODEL` environment variable (no code change).
- Selection order: the configured model first, then `gemini-2.5-flash-lite`,
  `gemini-2.5-flash`, `gemini-3.5-flash`, then any model the key offers.

## What changed in each file

| File | Change |
| --- | --- |
| ai_config.py | New. Single source of truth for the model and the setup helper. |
| scholar_sync.py | Removed local setup_gemini and pinned names; imports setup_gemini from ai_config. |
| synthesize.py | Same. (Its dynamic list-models logic now lives in the shared helper.) |
| fix_metadata.py | Same. |
| manual_import.py | Same; also logs the configured model name via MODEL_NAME from ai_config. |
| audit_library.py | Same. |
| README.md | Added a "Choosing a Gemini Model" section explaining auto-detect and override. |

No other logic changed. Each script keeps its own behavior and its `__main__`
guard. requirements.txt is unchanged.

## How this was validated

- All six Python files compile.
- ai_config.py imports cleanly and exposes a callable setup_gemini.
- No leftover references to the old genai or GEMINI_KEY names in the scripts.
- End-to-end runs still require your own GEMINI_API_KEY and were not run here.

## Two things worth knowing

1. SDK version. requirements.txt still uses `google-generativeai==0.8.3`, the
   older SDK, now deprecated in favor of the unified `google-genai` SDK. The 2.5
   models are the safe default for the older SDK. `gemini-3.5-flash` sits last as
   a fallback because the older SDK may not reach the 3.x models. Moving to the
   new SDK is a larger, separate change.
2. Quick verification. Run the snippet in the README "Choosing a Gemini Model"
   section with your key to print the exact model names your project can call.

## Suggested commit message

Centralize Gemini setup in ai_config with auto-detect; retire pinned 1.5 names (404 as of June 2026)
