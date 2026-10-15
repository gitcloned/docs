"""
Fluento guardrails — Python pre/post hooks.

pre_flight  → runs BEFORE agent, can block the request entirely
post_flight → runs AFTER agent, can sanitize the response

Both receive a context dict:
  { user_email, user_role, channel, project }
"""

import re


def pre_flight(prompt: str, context: dict) -> dict:
    """Return {"allow": True} or {"allow": False, "reason": "..."}"""

    role = context.get("user_role", "unknown")
    channel = context.get("channel", "cli")

    # Unknown users blocked everywhere except CLI (dev local runs)
    if role == "unknown" and channel != "cli":
        return {"allow": False, "reason": "Unrecognised user. Contact your admin."}

    # Hard blocks for support role — Python enforces, Claude never sees the prompt
    if role == "support":
        blocked_patterns = [
            r"\bbulk.{0,10}(export|download)\b",
            r"\ball students\b",
            r"\bpersonal.{0,15}data\b",
        ]
        for pattern in blocked_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                return {
                    "allow": False,
                    "reason": "This request is not available for the support role.",
                }

    return {"allow": True}


def post_flight(response: str, context: dict) -> str:
    """Sanitize the agent's response before returning it to the user."""

    # Redact any email addresses that slipped through
    response = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email redacted]", response)

    # Redact phone-like patterns
    response = re.sub(r"\b\d{10,12}\b", "[number redacted]", response)

    return response
