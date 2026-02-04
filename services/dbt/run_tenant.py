#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys

_SAFE_IDENT = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def tenant_schema_name(tenant_id: str) -> str:
    schema = f"tenant_{tenant_id.strip().lower().replace('-', '_')}"
    if not _SAFE_IDENT.fullmatch(schema):
        raise ValueError("Invalid tenant_id for schema name")
    return schema


def main() -> int:
    parser = argparse.ArgumentParser(description="Run dbt for a tenant schema")
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--dbt-bin", default="dbt")
    parser.add_argument("--profiles-dir", default=".")
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()

    schema = tenant_schema_name(args.tenant_id)
    cmd = [
        args.dbt_bin,
        "build",
        "--profiles-dir",
        args.profiles_dir,
        "--vars",
        json.dumps({"tenant_schema": schema}),
    ]
    if args.full_refresh:
        cmd.append("--full-refresh")

    result = subprocess.run(cmd, text=True, capture_output=True)
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
