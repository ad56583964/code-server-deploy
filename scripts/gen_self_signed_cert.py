#!/usr/bin/env python3
"""
Generate a self-signed TLS certificate for code-server using openssl.

Configuration precedence (highest first):
1. CLI arguments: --host / --out-dir / --days
2. .env.toml [cert] section:
   - domain / host
   - out_dir
   - days
   - key_bits
   - subject.*
   - san.dns[]
3. Built-in defaults:
   host     = code-server.local
   out_dir  = ~/.config/code-server
   days     = 3650
   key_bits = 2048

The default .env.toml is looked up in the repository root (../.env.toml
relative to this script). You can override it with --env-file.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


def run(cmd: list[str]) -> None:
    """Run a command and raise a readable error on failure."""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] Command failed: {' '.join(cmd)}", file=sys.stderr)
        raise SystemExit(exc.returncode)


def load_env_toml(path: Path) -> dict:
    """Load a TOML config file if it exists, otherwise return {}."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:  # pragma: no cover - fallback for older versions
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            # No TOML support, behave as if no config file
            return {}

    if not path.is_file():
        return {}

    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception as exc:  # pragma: no cover - config parse errors are rare
        print(f"[WARN] Failed to parse {path}: {exc}", file=sys.stderr)
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a self-signed certificate for code-server."
    )
    parser.add_argument(
        "--host",
        dest="host",
        default=None,
        help=(
            "Common Name / DNS name in the certificate "
            "(default: from .env.toml [cert].domain/host or code-server.local)"
        ),
    )
    parser.add_argument(
        "--out-dir",
        dest="out_dir",
        default=None,
        help=(
            "Directory to place cert.pem and key.pem "
            "(default: from .env.toml [cert].out_dir or ~/.config/code-server)"
        ),
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help=(
            "Validity period in days "
            "(default: from .env.toml [cert].days or 3650, about 10 years)"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing cert.pem/key.pem if they exist.",
    )
    parser.add_argument(
        "--env-file",
        dest="env_file",
        default=None,
        help="Path to TOML config file (default: ../.env.toml relative to script).",
    )

    args = parser.parse_args()

    # Resolve env file path
    if args.env_file:
        env_path = Path(args.env_file).expanduser()
    else:
        repo_root = Path(__file__).resolve().parents[1]
        env_path = repo_root / ".env.toml"

    env_cfg = load_env_toml(env_path)
    cert_cfg = env_cfg.get("cert", {}) if isinstance(env_cfg, dict) else {}

    # Apply precedence: CLI > .env.toml > default
    host = args.host or cert_cfg.get("domain") or cert_cfg.get("host") or "code-server.local"
    out_dir_val = args.out_dir or cert_cfg.get("out_dir") or "~/.config/code-server"
    days = args.days or cert_cfg.get("days") or 3650
    key_bits = int(cert_cfg.get("key_bits") or 2048)

    subject_cfg = cert_cfg.get("subject", {}) if isinstance(cert_cfg, dict) else {}
    san_cfg = cert_cfg.get("san", {}) if isinstance(cert_cfg, dict) else {}

    country = subject_cfg.get("country", "CN")
    state = subject_cfg.get("state", "Zhejiang")
    locality = subject_cfg.get("locality", "Hangzhou")
    organization = subject_cfg.get("organization", "Example")
    organizational_unit = subject_cfg.get("organizational_unit", "Code Server")
    email = subject_cfg.get("email", "admin@example.com")

    dns_names = san_cfg.get("dns")
    if not dns_names:
        dns_names = [host]
    elif isinstance(dns_names, str):
        dns_names = [dns_names]
    else:
        dns_names = list(dns_names)

    alt_names_lines = "\n".join(
        f"DNS.{i+1} = {name}" for i, name in enumerate(dns_names)
    )

    out_dir = os.path.expanduser(out_dir_val)
    key_dir = os.path.join(out_dir, "key")

    cert_path = os.path.join(out_dir, "cert.pem")
    key_path = os.path.join(out_dir, "key.pem")
    key_conf_path = os.path.join(key_dir, "key.conf")

    os.makedirs(key_dir, exist_ok=True)

    if not args.force and (os.path.exists(cert_path) or os.path.exists(key_path)):
        print(
            f"[ERROR] {cert_path} or {key_path} already exists.\n"
            "Use --force to overwrite existing files.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    key_conf = dedent(
        f"""\
        [req]
        prompt = no
        default_bits = {key_bits}
        default_md = sha512
        distinguished_name = dn
        x509_extensions = v3_req

        [dn]
        C={country}
        ST={state}
        L={locality}
        O={organization}
        OU={organizational_unit}
        CN={host}
        emailAddress={email}

        [v3_req]
        keyUsage = nonRepudiation, digitalSignature, keyEncipherment
        subjectAltName=@alt_names

        [alt_names]
        {alt_names_lines}
        """
    )

    with open(key_conf_path, "w", encoding="utf-8") as f:
        f.write(key_conf)

    if env_cfg:
        print(f"[INFO] Using env file: {env_path}")
    else:
        print("[INFO] No env file found, using CLI/default values.")
    print(f"[INFO] Writing openssl config to {key_conf_path}")

    cmd = [
        "openssl",
        "req",
        "-newkey",
        f"rsa:{key_bits}",
        "-new",
        "-nodes",
        "-x509",
        "-days",
        str(int(days)),
        "-config",
        key_conf_path,
        "-keyout",
        key_path,
        "-out",
        cert_path,
    ]

    print(f"[INFO] Generating self-signed certificate for host: {host}")
    run(cmd)

    print("[OK] Certificate generated.")
    print(f"     Key : {key_path}")
    print(f"     Cert: {cert_path}")


if __name__ == "__main__":
    main()
