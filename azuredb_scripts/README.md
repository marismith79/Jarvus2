# Database Management Scripts

This directory contains scripts for managing the application's database.

## Available Scripts

### init_db.py
Initializes the database by creating all necessary tables using `db.create_all()`.
```bash
python azuredb_scripts/init_db.py
```
**Note**: This bypasses Alembic migrations. For production, consider using the migration-based approach below.

### reset_db.py
Resets the database by removing the existing database file and creating a new one.
```bash
python azuredb_scripts/reset_db.py
```
**Note**: This bypasses Alembic migrations. For production, consider using the migration-based approach below.

### check_db.py
Checks the database status, showing all tables, their columns, and row counts.
```bash
python azuredb_scripts/check_db.py
```

## Usage Order

### For Development (Quick Setup):
1. For first-time setup:
   ```bash
   python azuredb_scripts/init_db.py
   ```

2. To check database status:
   ```bash
   python azuredb_scripts/check_db.py
   ```

3. To reset the database (during development):
   ```bash
   python azuredb_scripts/reset_db.py
   ```

### For Production (Recommended):
1. For first-time setup:
   ```bash
   make migrations
   ```

2. To check migration status:
   ```bash
   make migration-current
   ```

3. To apply new migrations:
   ```bash
   make migrations
   ```

## Migration Commands (Recommended for Production)

Use these Makefile commands for proper database version control:

```bash
make migrations           # Apply all pending migrations
make migration-current    # Check current migration status
make migration-history    # Show migration history
make migration-generate   # Generate new migration from model changes
make migration-downgrade  # Downgrade to previous migration
```

## Recent Updates

The following discrepancies have been fixed:

1. **Missing Model Imports**: All scripts now import all models including `History`, `OAuthCredentials`, `ToolPermission`, and `UserTool`
2. **Migration Warnings**: Scripts that bypass migrations now show warnings
3. **Consistent Environment Handling**: All scripts now use the same environment variable logic as the main application

## Azure SQL via CLI

Quick commands to manage the remote database from your terminal:

```bash
# Login to Azure (if not already)
az login

# Allow Azure App Service outbound traffic to reach the SQL server (opens to all Azure services)
az sql server firewall-rule create \
  --name AllowAzure \
  --resource-group Jarvus \
  --server sql-server-jarvus \
  --start-ip-address 0.0.0.0 \
  --end-ip-address   0.0.0.0

# Connect interactively with sqlcmd (requires sqlcmd tool)
sqlcmd -S tcp:sql-server-jarvus.database.windows.net,1433 -d sqlserver-jarvus -U <user> -P <password> -G

# Restore the DB from a bacpac (example)
az sql db import --admin-user <user> --admin-password <pwd> \
  --name sqlserver-jarvus --resource-group Jarvus \
  --storage-uri https://<storage-account>.blob.core.windows.net/backups/latest.bacpac
```

### Connection-string tip

Use the same **ODBC Driver 18** syntax locally and in Azure App Service to avoid surprises:

```
mssql+pyodbc://<user>:<password>@sql-server-jarvus.database.windows.net:1433/sqlserver-jarvus?driver=ODBC+Driver+18+for+SQL+Server&encrypt=yes&TrustServerCertificate=yes&timeout=300&connect_timeout=300
```

Set this value in the portal under **Configuration → Application settings → AZURE_SQL_CONNECTION_STRING**.

## Migration vs Direct Creation

- **Direct Creation** (`init_db.py`, `reset_db.py`): Uses `db.create_all()` - fast for development but bypasses version control
- **Migration-based** (`make migrations`): Uses Alembic - slower but provides proper version control and rollback capabilities

For production environments, always use the migration-based approach. 