"""Command-line interface for QoderPilot."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .config import ConfigError, load_config
from .pipeline import PipelineError, QoderPilot

TARGET_LABELS = {"ide": "Qoder IDE", "agentic": "Qoder Agentic"}


def default_config_path() -> Path:
    configured = os.getenv("QODERPILOT_CONFIG")
    if configured:
        return Path(configured)
    current = Path.cwd() / "config.toml"
    if current.is_file():
        return current
    return Path(__file__).resolve().parent.parent / "config.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qoderpilot",
        description="Automated Qoder onboarding for Qoder IDE and Qoder Agentic.",
    )
    parser.add_argument("--version", action="version", version=f"QoderPilot {__version__}")
    parser.add_argument("--config", type=Path, default=default_config_path())
    commands = parser.add_subparsers(dest="command")
    run = commands.add_parser("run", help="Run signup then client login.")
    run.add_argument("-n", "--count", type=int)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--no-reset", action="store_true", help="Skip the pre-login target reset.")
    resume = commands.add_parser("resume", help="Retry pending client logins with their saved proxy.")
    resume.add_argument("--no-reset", action="store_true", help="Skip the pre-login target reset.")
    commands.add_parser("status", help="Show local result counts without passwords.")
    commands.add_parser("doctor", help="Validate the local installation.")
    patch = commands.add_parser("patch", help="Patch Qoder IDE or Qoder Agentic identity data.")
    patch.add_argument(
        "--target",
        choices=("ide", "agentic"),
        help="Application to patch; prompted interactively when omitted.",
    )
    reset = commands.add_parser("reset", help="Reset and repatch Qoder IDE or Qoder Agentic data.")
    reset.add_argument("--deep", action="store_true", help="Remove all Qoder data.")
    reset.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    reset.add_argument(
        "--target",
        choices=("ide", "agentic"),
        help="Application to reset; prompted interactively when omitted.",
    )
    return parser


def print_doctor(app: QoderPilot) -> bool:
    checks = app.doctor()
    for check in checks:
        marker = "OK" if check.ok else ("WARN" if not check.required else "FAIL")
        print(f"[{marker}] {check.label}: {check.detail}")
    return all(check.ok or not check.required for check in checks)


def select_target(explicit: Optional[str]) -> str:
    """Resolve the requested application target, prompting when omitted."""
    if explicit:
        return explicit
    print("\nPilih aplikasi tujuan:")
    print("  1. Qoder IDE")
    print(r"  2. Qoder Agentic (C:\ProgramData\Qoder\Qoder Launcher)")
    while True:
        try:
            choice = input("Masukkan pilihan [1/2], lalu tekan Enter: ").strip()
        except EOFError as exc:
            raise PipelineError(
                "Pemilihan aplikasi membutuhkan terminal interaktif."
            ) from exc
        if choice == "1":
            print("Target: Qoder IDE")
            return "ide"
        if choice == "2":
            print("Target: Qoder Agentic")
            return "agentic"
        print("Pilihan tidak valid. Masukkan angka 1 atau 2.")


def confirm_reset(deep: bool, target: str) -> bool:
    label = TARGET_LABELS[target]
    scope = f"SEMUA data {label}" if deep else f"data {label} dan menerapkan patch baru"
    answer = input(f"Tindakan ini akan menghapus {scope}. Lanjutkan? [y/N] ")
    return answer.strip().lower() == "y"


async def execute(args: argparse.Namespace, app: QoderPilot) -> int:
    if args.command == "doctor":
        return 0 if print_doctor(app) else 1
    if args.command == "status":
        status = app.status()
        print(f"Pending : {status.pending}\nSuccess : {status.successful}\nFailed  : {status.failed}")
        return 0
    if args.command == "resume":
        result = await app.resume(no_reset=args.no_reset)
        print(result.message)
        return result.exit_code
    if args.command == "patch":
        target = select_target(args.target)
        ok = app.patch_client(target)
        print("Patch berhasil." if ok else "Patch gagal.")
        return 0 if ok else 2
    if args.command == "reset":
        target = select_target(args.target)
        if not args.yes and not confirm_reset(args.deep, target):
            print("Reset dibatalkan.")
            return 0
        ok = app.reset_client(deep=args.deep, target=target)
        print("Reset berhasil." if ok else "Reset selesai dengan kegagalan.")
        return 0 if ok else 2

    count = args.count if args.count is not None else app.config.default_count
    result = await app.run(count, dry_run=args.dry_run, no_reset=args.no_reset)
    print(result.message)
    return result.exit_code


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    try:
        app = QoderPilot(load_config(args.config))
        return asyncio.run(execute(args, app))
    except (ConfigError, PipelineError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nDihentikan oleh pengguna.", file=sys.stderr)
        return 130
