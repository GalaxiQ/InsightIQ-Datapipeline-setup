import re

_SAFE_IDENT = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def tenant_schema_name(tenant_id: str) -> str:
    schema = f"tenant_{tenant_id.strip().lower().replace('-', '_')}"
    if not _SAFE_IDENT.fullmatch(schema):
        raise ValueError("Invalid tenant_id for schema name")
    return schema


def qualified_table(schema: str, table: str) -> str:
    if not _SAFE_IDENT.fullmatch(schema):
        raise ValueError("Invalid schema name")
    if not _SAFE_IDENT.fullmatch(table):
        raise ValueError("Invalid table name")
    return f'"{schema}"."{table}"'
