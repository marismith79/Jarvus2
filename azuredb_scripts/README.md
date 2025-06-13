# Database Management Scripts

This directory contains scripts for managing the application's database.

## Available Scripts

### init_db.py
Initializes the database by creating all necessary tables.
```bash
python scripts/init_db.py
```

### populate_db.py
Populates the database with initial data (e.g., default users, tools).
```bash
python scripts/populate_db.py
```

### reset_db.py
Resets the database by removing the existing database file and creating a new one.
Optionally populates the database with initial data.
```bash
python scripts/reset_db.py
```

### check_db.py
Checks the database status, showing all tables, their columns, and row counts.
```bash
python scripts/check_db.py
```

## Usage Order

1. For first-time setup:
   ```bash
   python scripts/init_db.py
   python scripts/populate_db.py
   ```

2. To check database status:
   ```bash
   python scripts/check_db.py
   ```

3. To reset the database (during development):
   ```bash
   python scripts/reset_db.py
   ```

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