"""Shared tooling for live support (scripts and live tests).

The canonical home for environment, target, settings, and diagnostic models
that both scripts and live tests rely on. Submodules:

  - environment: CompatibilityTarget, LiveSettings, LiveTarget, Environment,
    LiveSetupError, parse_target, parse_environment.
  - diagnostics: VERIFICATION_CODE, redact, scan_for_secrets,
    is_canary_response.
"""

from __future__ import annotations

from tools.live_support import diagnostics, environment

__all__ = ["diagnostics", "environment"]
