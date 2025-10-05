"""Utilities to expose the current application version."""

from __future__ import annotations

import os


def discover_version() -> str:
    """Return the version string for the running application.

    The order of precedence is:

    1. An explicit ``APP_VERSION`` environment variable – useful for
       manual deployments or custom pipelines.
    2. The ``VERCEL_GIT_COMMIT_SHA`` (or ``GIT_COMMIT_SHA``) provided by
       Vercel/Git integrations. The hash is truncated to the first seven
       characters to keep the UI compact while still uniquely
       identifying the build.
    3. The literal string ``"dev"`` as a sensible fallback for local
       development where neither variable is set.
    """

    explicit_version = os.getenv("APP_VERSION")
    if explicit_version:
        return explicit_version

    commit_sha = os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("GIT_COMMIT_SHA")
    if commit_sha:
        return commit_sha[:7]

    return "dev"

