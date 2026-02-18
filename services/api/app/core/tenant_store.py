from app.core.settings import settings

# Since all tenants are now on the same remote PostgreSQL instance (galaxiq_tenants),
# we return the configuration derived from settings instead of querying a registry table.

async def get_tenant_db(db, tenant_id):
    # This logic assumes all tenants exist on the same host/port/db configured in settings.
    # The caller will use this config to create a session to the remote DB.
    
    # We extract the components from settings.MASTER_DB_URL
    # URL format: postgresql+asyncpg://postgres:galaxiq@66.135.22.167:5432/galaxiq_tenants
    
    # In a more complex setup, we might split the URL parts in settings,
    # but for now, we know the production credentials.
    
    return {
        "host": "66.135.22.167",
        "port": 5432,
        "db_name": "galaxiq_tenants",
        "user": "postgres",
        "password": "galaxiq"
    }
