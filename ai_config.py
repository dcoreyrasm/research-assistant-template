"""
Shared Gemini setup for the research assistant template.

This is the one place to control which model the scripts use.

By default the scripts auto-detect a working model from your API key, so the
template keeps running even when Google retires older model names. To force a
specific model, set MODEL_NAME below, or set the GEMINI_MODEL environment
variable (no code change needed).

Current model names: https://ai.google.dev/gemini-api/docs/models
"""

import os
import google.generativeai as genai

# Leave the default to auto-detect, or set a specific model name.
# Environment override:  export GEMINI_MODEL="gemini-2.5-flash"
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")

# Fallback order used when the configured model is not available to your key.
# Cheapest and fastest first. Update from the link above as models change.
PREFERRED_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash",
]

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")


def setup_gemini(verbose=True):
    """
    Connect to Gemini and return a GenerativeModel, or None on failure.

    Selection order:
      1. MODEL_NAME / GEMINI_MODEL, if your key can call it.
      2. The first available model from PREFERRED_MODELS.
      3. Any model your key offers that supports generateContent.
    """
    if not GEMINI_KEY:
        print("  [Setup Error] GEMINI_API_KEY is not set.")
        return None

    try:
        # REST transport is more reliable inside GitHub Actions than gRPC.
        genai.configure(api_key=GEMINI_KEY, transport="rest")
    except Exception as e:
        print(f"  [Setup Error] Could not configure Gemini: {e}")
        return None

    try:
        available = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
    except Exception as e:
        print(f"  [Setup Error] Could not list models. Is the Generative Language API enabled? {e}")
        return None

    if not available:
        print("  [Setup Error] Key is valid, but no usable models are available for it.")
        print("  ACTION: enable the Generative Language API for this key, then retry.")
        return None

    # Try the configured model first, then the preferred fallbacks.
    wanted = [MODEL_NAME] + [m for m in PREFERRED_MODELS if m != MODEL_NAME]
    for target in wanted:
        for name in available:
            if target in name:  # API names look like "models/gemini-2.5-flash-lite"
                if verbose:
                    print(f"  [Setup] Using model: {name}")
                return genai.GenerativeModel(name)

    # Nothing preferred matched; use whatever is available.
    fallback = available[0]
    if verbose:
        print(f"  [Setup] Preferred models not found for this key. Using: {fallback}")
    return genai.GenerativeModel(fallback)
