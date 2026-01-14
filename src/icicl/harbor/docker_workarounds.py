"""Workarounds for Harbor Docker environment issues in local SWE-bench runs.

This project primarily provides Harbor-compatible agents. In practice, running many
SWE-bench tasks locally can fail due to Docker Desktop VM disk pressure (e.g.
"no space left on device") caused by per-task image builds.

Harbor's DockerEnvironment supports running a *prebuilt* image directly when the
task's EnvironmentConfig.docker_image is set. Many SWE-bench tasks ship an
`environment/Dockerfile` that simply wraps a prebuilt `swebench/...` base image
and adds small conveniences (e.g. `WORKDIR /testbed`, `uv` install).

For those simple wrapper Dockerfiles, we can safely skip the build step and run
the base image directly. This:
  - avoids creating many dangling build images
  - makes `docker compose down --rmi all` remove the large prebuilt image after the
    trial, keeping Docker Desktop disk usage bounded

This module monkey-patches Harbor's DockerEnvironment.start() at import time.
It is best-effort and no-ops if Harbor is not installed or APIs change.
"""

from __future__ import annotations

import asyncio
import asyncio.subprocess
import re
from pathlib import Path


_FROM_RE = re.compile(r"^\s*FROM\s+([^\s]+)", re.IGNORECASE)
_UV_VER_RE = re.compile(r"astral\.sh/uv/([0-9]+\.[0-9]+\.[0-9]+)/install\.sh")


def _parse_from_image(dockerfile_text: str) -> str | None:
    for raw in dockerfile_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.upper().startswith("ARG "):
            # Some Dockerfiles use ARGs before FROM; ignore them.
            continue
        m = _FROM_RE.match(line)
        if m:
            return m.group(1)
        # If the first non-comment instruction isn't FROM, bail.
        return None
    return None


def _is_simple_swebench_wrapper(dockerfile_text: str) -> bool:
    """Heuristic: only allow safe, minimal wrapper Dockerfiles."""
    for raw in dockerfile_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        upper = line.split(maxsplit=1)[0].upper()
        if upper == "FROM":
            continue
        if upper == "WORKDIR" and line.split(maxsplit=1)[-1] == "/testbed":
            continue
        if upper == "RUN":
            rest = line[3:].strip()
            # Common in SWE-bench Harbor tasks.
            if "astral.sh/uv" in rest:
                continue
            if rest.replace(" ", "") == "mkdir-p/logs":
                continue
            # Allow benign mkdir variants.
            if rest.startswith("mkdir -p ") and "/logs" in rest:
                continue
            return False
        # Any other instruction is treated as non-trivial.
        return False
    return True


def _maybe_get_dockerfile(environment_dir: Path) -> str | None:
    dockerfile = environment_dir / "Dockerfile"
    if not dockerfile.exists():
        return None
    try:
        return dockerfile.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _infer_uv_version(dockerfile_text: str) -> str:
    m = _UV_VER_RE.search(dockerfile_text)
    return m.group(1) if m else "0.7.13"


def apply() -> None:
    """Apply Harbor DockerEnvironment workarounds (idempotent)."""
    try:
        from harbor.environments.docker.docker import DockerEnvironment  # type: ignore
    except Exception:
        return

    if getattr(DockerEnvironment, "_icicl_swebench_prebuilt_patch", False):
        return

    original_start = DockerEnvironment.start
    original_stop = DockerEnvironment.stop

    async def patched_start(self, force_build: bool):  # type: ignore[no-untyped-def]
        used_prebuilt_override = False
        uv_version = "0.7.13"
        # Only attempt this when Harbor isn't explicitly forcing a rebuild.
        if not force_build and getattr(self, "task_env_config", None) is not None:
            try:
                # Only override when the task didn't already specify a docker_image.
                if getattr(self.task_env_config, "docker_image", None) is None:
                    dockerfile_text = _maybe_get_dockerfile(self.environment_dir)
                    if dockerfile_text:
                        base = _parse_from_image(dockerfile_text)
                        if (
                            base is not None
                            and base.startswith("swebench/")
                            and _is_simple_swebench_wrapper(dockerfile_text)
                        ):
                            # Switch Harbor into "prebuilt" mode.
                            self.task_env_config.docker_image = base
                            # Harbor caches env vars on init; update prebuilt_image_name.
                            env_vars = getattr(self, "_env_vars", None)
                            if env_vars is not None:
                                try:
                                    env_vars.prebuilt_image_name = base
                                except Exception:
                                    pass
                            used_prebuilt_override = True
                            uv_version = _infer_uv_version(dockerfile_text)
                            # Store for stop() cleanup and debugging.
                            try:
                                setattr(self, "_icicl_prebuilt_override", True)
                                setattr(self, "_icicl_prebuilt_image", base)
                            except Exception:
                                pass
            except Exception:
                # Best-effort only.
                pass

        await original_start(self, force_build)

        # If we switched to prebuilt mode, reproduce the (minimal) wrapper setup
        # steps that SWE-bench tasks rely on, without building a new image.
        if used_prebuilt_override:
            try:
                # Install uv only if not present; keep this best-effort and fast.
                cmd = (
                    "command -v uv >/dev/null 2>&1 || "
                    f"(curl -LsSf https://astral.sh/uv/{uv_version}/install.sh | sh)"
                )
                # Ensure uv/uvx are on PATH even if $HOME/.local/bin isn't.
                cmd += (
                    " && ("
                    "ln -sf \"$HOME/.local/bin/uv\" /usr/local/bin/uv 2>/dev/null || true"
                    ")"
                    " && ("
                    "ln -sf \"$HOME/.local/bin/uvx\" /usr/local/bin/uvx 2>/dev/null || true"
                    ")"
                )
                cmd += " && mkdir -p /logs 2>/dev/null || true"
                await self.exec(cmd, timeout_sec=120)  # type: ignore[attr-defined]
            except Exception:
                pass

        return None

    async def patched_stop(self, delete: bool):  # type: ignore[no-untyped-def]
        await original_stop(self, delete)

        # Keep Docker Desktop disk usage bounded: for tasks where we switched to
        # a prebuilt SWE-bench image, explicitly remove that base image after the
        # trial ends. (docker compose down --rmi all is not consistently removing
        # pulled images across Docker Compose versions.)
        if delete and getattr(self, "_icicl_prebuilt_override", False):
            image = getattr(self, "_icicl_prebuilt_image", None)
            if isinstance(image, str) and image:
                try:
                    proc = await asyncio.create_subprocess_exec(
                        "docker",
                        "image",
                        "rm",
                        "-f",
                        image,
                        stdin=asyncio.subprocess.DEVNULL,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    await proc.communicate()
                except Exception:
                    pass

    DockerEnvironment.start = patched_start  # type: ignore[assignment]
    DockerEnvironment.stop = patched_stop  # type: ignore[assignment]
    DockerEnvironment._icicl_swebench_prebuilt_patch = True


# Apply on import so Harbor trials pick it up early.
apply()

