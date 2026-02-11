import asyncio
import json
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.core.db import get_db
from app.core.settings import settings
from app.core.tenant_schema import tenant_schema_name
from app.core.tenant_store import get_tenant_db
from app.models.transform import TransformRequest

router = APIRouter()


def _tail(text: str, size: int = 2000) -> str:
    if len(text) <= size:
        return text
    return text[-size:]


@router.post("/run")
async def run_transform(req: TransformRequest, master_db=Depends(get_db)):
    # -------------------------
    # 1️⃣ Validate tenant
    # -------------------------
    try:
        await get_tenant_db(master_db, req.tenant_id)
        tenant_schema = tenant_schema_name(req.tenant_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid tenant")

    # -------------------------
    # 2️⃣ Resolve dbt paths
    # -------------------------
    dbt_project_dir = Path(settings.DBT_PROJECT_DIR).resolve()
    dbt_bin = Path(settings.DBT_BIN).resolve()

    if not dbt_bin.exists():
        raise HTTPException(
            status_code=500,
            detail=f"dbt binary not found at {dbt_bin}"
        )

    # -------------------------
    # 3️⃣ Build dbt command
    # -------------------------
    cmd = [
        str(dbt_bin),
        "build",
        "--profiles-dir",
        str(dbt_project_dir),
        "--vars",
        json.dumps({"tenant_schema": tenant_schema}),
    ]

    if req.full_refresh:
        cmd.append("--full-refresh")

    # -------------------------
    # 4️⃣ Clean environment (CRITICAL FIX)
    # -------------------------
    env = os.environ.copy()

    # Remove Python contamination from other venvs
    env.pop("PYTHONPATH", None)

    # Force correct virtualenv
    env["VIRTUAL_ENV"] = str(dbt_bin.parent.parent)

    # Ensure correct venv bin is first in PATH
    env["PATH"] = f"{dbt_bin.parent}:{env.get('PATH', '')}"

    # -------------------------
    # 5️⃣ Run dbt subprocess
    # -------------------------
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(dbt_project_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    stdout_b, stderr_b = await process.communicate()
    stdout = stdout_b.decode(errors="ignore")
    stderr = stderr_b.decode(errors="ignore")

    # -------------------------
    # 6️⃣ Handle failure
    # -------------------------
    if process.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "dbt build failed",
                "tenant_id": req.tenant_id,
                "schema": tenant_schema,
                "stderr_tail": _tail(stderr),
                "dbt_bin_used": str(dbt_bin),
                "cwd": str(dbt_project_dir),
            },
        )

    # -------------------------
    # 7️⃣ Success response
    # -------------------------
    return {
        "status": "ok",
        "tenant_id": req.tenant_id,
        "schema": tenant_schema,
        "full_refresh": req.full_refresh,
        "dbt_output_tail": _tail(stdout, 800),
        "dbt_bin_used": str(dbt_bin),
    }
