import asyncio
import json
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
    try:
        await get_tenant_db(master_db, req.tenant_id)
        tenant_schema = tenant_schema_name(req.tenant_id)
    except Exception:
        raise HTTPException(401, "Invalid tenant")

    dbt_project_dir = Path(settings.DBT_PROJECT_DIR)
    dbt_bin = Path(settings.DBT_BIN)
    if not dbt_bin.is_absolute():
        dbt_bin = (dbt_project_dir / dbt_bin).resolve()

    cmd = [
        str(dbt_bin),
        "build",
        "--profiles-dir",
        ".",
        "--vars",
        json.dumps({"tenant_schema": tenant_schema}),
    ]
    if req.full_refresh:
        cmd.append("--full-refresh")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(dbt_project_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_b, stderr_b = await process.communicate()
    stdout = stdout_b.decode(errors="ignore")
    stderr = stderr_b.decode(errors="ignore")

    if process.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "dbt build failed",
                "tenant_id": req.tenant_id,
                "schema": tenant_schema,
                "stderr_tail": _tail(stderr),
            },
        )

    return {
        "status": "ok",
        "tenant_id": req.tenant_id,
        "schema": tenant_schema,
        "full_refresh": req.full_refresh,
        "dbt_output_tail": _tail(stdout, 800),
    }
