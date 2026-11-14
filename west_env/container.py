# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import shlex
import subprocess

from west_env.engine import get_engine

CONTAINER_WORKDIR = "/work"


def _west_topdir():
    from west.util import west_topdir

    return west_topdir()


def workspace_volume_name(workspace) -> str:
    """Name of the engine volume holding the synced workspace copy.

    Must match the name `west env sync` populates (see
    west_commands/env.py and west_env/sync.py).
    """
    from west_env.sync import _workspace_slug

    return f"west-env-ws-{_workspace_slug(Path(workspace))}"


def _container_workdir(workspace, host_cwd):
    try:
        rel = host_cwd.relative_to(workspace)
        return f"{CONTAINER_WORKDIR}/{rel.as_posix()}"
    except ValueError:
        return CONTAINER_WORKDIR


def _container_args(cfg, command, interactive=False, workspace=None, host_cwd=None):
    if not cfg.image:
        raise RuntimeError("no container image configured")

    engine, warned = get_engine(cfg.engine)

    # Canonical west topdir (directory containing .west/)
    workspace = Path(workspace or _west_topdir()).resolve()

    # Host cwd (perhaps inside the workspace)
    host_cwd = Path(host_cwd or Path.cwd()).resolve()
    container_wd = _container_workdir(workspace, host_cwd)

    # -------------------------------------------------
    # Prepare container invocation
    # -------------------------------------------------
    # workspace_mode decides what is mounted at /work; the mount spec
    # comes from WorkspaceSync.volume_args, the single source of
    # truth shared with `west env sync`:
    #   bind          -> the host workspace directory itself
    #   sync/copy/tmpfs -> the volume that `west env sync` populated
    # This function previously hand-rolled an unconditional bind
    # mount, silently ignoring the configured mode and rebuilding
    # against the host tree (on Windows a C:\ bind mount, the exact
    # failure sync mode exists to avoid).
    from west_env.sync import WorkspaceSync

    mode = getattr(cfg, "workspace_mode", "bind")
    mount_args = WorkspaceSync(workspace_mode=mode).volume_args(workspace, engine.name)

    args = [
        "run",
        "--rm",
        *mount_args,
        "-w",
        container_wd,
        "-e",
        "PYTHONPATH=/work/modules/west-env",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
    ]

    if interactive:
        args.extend(["-i", "-t"])

    # -------------------------------------------------
    # Git safety + command execution
    #
    # Git >= 2.35 refuses to operate on mounted repos
    # unless explicitly marked safe. If this step is
    # missing, Zephyr west extension commands (build,
    # flash, etc.) will NOT load.
    # -------------------------------------------------
    git_prep = "git config --global safe.directory '*'"
    full_cmd = shlex.join(command)

    args.append(cfg.image)
    args.extend(
        [
            "sh",
            "-c",
            f"{git_prep} && exec {full_cmd}",
        ]
    )
    return engine, warned, args


def run_container(cfg, command, interactive=False):
    engine, warned, args = _container_args(cfg, command, interactive=interactive)

    if warned:
        print("[WARN] Both Docker and Podman detected; using Docker")

    mode = getattr(cfg, "workspace_mode", "bind")
    if mode != "bind":
        # The engine would auto-create an empty volume here, and the
        # command would then fail against an empty /work with a
        # confusing error. Fail fast with the actual remedy instead.
        volume = workspace_volume_name(_west_topdir())
        res = subprocess.run(
            [engine.name, "volume", "inspect", volume],
            capture_output=True,
        )
        if res.returncode != 0:
            raise RuntimeError(
                f"workspace volume {volume} does not exist "
                f"(workspace_mode={mode}); run 'west env sync' first"
            )

    engine.run(args)


def check_container(cfg):
    try:
        engine, warned = get_engine(cfg.engine)
        subprocess.check_output([engine.name, "--version"])
        print(f"[PASS] container engine: {engine.name}")

        if warned:
            print("[WARN] both Docker and Podman detected")
            print("       using Docker by default")
            print("       consider setting engine explicitly")

    except Exception as e:
        print(f"[FAIL] container engine error: {e}")
        return False

    if not cfg.image:
        print("[FAIL] no container image configured")
        return False

    try:
        subprocess.check_output(
            [engine.name, "image", "inspect", cfg.image],
            stderr=subprocess.DEVNULL,
        )
        print(f"[PASS] container image available: {cfg.image}")
    except Exception:  # noqa
        print(f"[WARN] container image not present locally: {cfg.image}")
        print("       it will be pulled on first use")

    return True


def check_container_workspace(cfg, workspace, manifest_rel):
    quoted_manifest = shlex.quote(manifest_rel)
    command = [
        "sh",
        "-c",
        f"test -d .west && test -f {quoted_manifest}",
    ]

    engine, _, args = _container_args(
        cfg,
        command,
        workspace=workspace,
        host_cwd=workspace,
    )
    subprocess.check_output(
        [engine.name] + args,
        stderr=subprocess.DEVNULL,
    )
