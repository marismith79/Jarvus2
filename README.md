---
# Jarvus Flask Application

Awesome jarvus2 created by marismith79

## Installation

From source:

```bash
git clone https://github.com/marismith79/Jarvus2 jarvus
cd jarvus
make virtualenv
source .venv/bin/activate
make install
```


## Executing

This application has a CLI interface that extends the Flask CLI.

Just run:

```bash
$ jarvus
```

or

```bash
$ python -m jarvus
```

To see the help message and usage instructions.

## First run

```bash
jarvus create-db   # run once
jarvus populate-db  # run once (optional)
jarvus add-user -u admin -p 1234  # ads a user
jarvus run
```

Go to:

- Website: http://localhost:5001
- Admin: http://localhost:5001/admin/
  - user: admin, senha: 1234
- API GET:
  - http://localhost:5001/api/v1/product/
  - http://localhost:5001/api/v1/product/1
  - http://localhost:5001/api/v1/product/2
  - http://localhost:5001/api/v1/product/3


> **Note**: You can do `flask run --port=5001` to run the application. 
> **Note**: You can also do `python run_dev.py` to run the application with automatic rendering.

## Azure Debugging

Run this command:
  az webapp log tail --name jarvus --resource-group Jarvus

## Environment Variables

Create a `.env` file (only used locally) with at least the following keys:

```
# Flask
FLASK_ENV=development
SECRET_KEY=dev
FLASK_SECRET_KEY=dev

# Azure SQL
AZURE_SQL_CONNECTION_STRING="mssql+pyodbc://<user>:<password>@<server>.database.windows.net:1433/<db>?driver=ODBC+Driver+18+for+SQL+Server&encrypt=yes&TrustServerCertificate=yes"

# Azure AI Inference
AZURE_AI_FOUNDRY_KEY=<your‐openai‐key>
AZURE_AI_FOUNDRY_ENDPOINT=https://<your-resource-name>.openai.azure.com
AZURE_AI_FOUNDRY_API_VERSION=<your-api-version>
AZURE_AI_FOUNDRY_DEPLOYMENT_NAME=<your-model-name>

# OAuth (for future integrations)
# NOTION_CLIENT_ID=<id>
# NOTION_CLIENT_SECRET=<secret>
# NOTION_REDIRECT_URI=http://localhost:5001/notion/callback
# SLACK_CLIENT_ID=<id>
# SLACK_CLIENT_SECRET=<secret>
# SLACK_REDIRECT_URI=http://localhost:5001/slack/callback
# ZOOM_CLIENT_ID=<id>
# ZOOM_CLIENT_SECRET=<secret>
# ZOOM_REDIRECT_URI=http://localhost:5001/zoom/callback

# Pipedream Integration (Direct OAuth)
PIPEDREAM_REDIRECT_URI=http://localhost:5001/pipedream/callback

# OAuth App IDs - for the actual OAuth flows
PIPEDREAM_DOCS_OAUTH_APP_ID=<your-pipedream-docs-oauth-app-id>
PIPEDREAM_SHEETS_OAUTH_APP_ID=<your-pipedream-sheets-oauth-app-id>
PIPEDREAM_SLIDES_OAUTH_APP_ID=<your-pipedream-slides-oauth-app-id>
PIPEDREAM_DRIVE_OAUTH_APP_ID=<your-pipedream-drive-oauth-app-id>
PIPEDREAM_GMAIL_OAUTH_APP_ID=<your-pipedream-gmail-oauth-app-id>
PIPEDREAM_CALENDAR_OAUTH_APP_ID=<your-pipedream-calendar-oauth-app-id>

# Pipedream Service Endpoints (for Google Workspace tools)
PIPEDREAM_DOCS_ENDPOINT=<your-pipedream-docs-endpoint>
PIPEDREAM_SHEETS_ENDPOINT=<your-pipedream-sheets-endpoint>
PIPEDREAM_SLIDES_ENDPOINT=<your-pipedream-slides-endpoint>
PIPEDREAM_DRIVE_ENDPOINT=<your-pipedream-drive-endpoint>
PIPEDREAM_GMAIL_ENDPOINT=<your-pipedream-gmail-endpoint>
PIPEDREAM_CALENDAR_ENDPOINT=<your-pipedream-calendar-endpoint>
```

When running in Azure App Service, set these same keys in the **Configuration → Application settings** blade instead of using a `.env` file.

## Local Development & Debugging

```bash
# 1. Create & activate virtualenv (if you have not already)
python -m venv .venv
source .venv/bin/activate

# 2. Install requirements
pip install -r requirements.txt

# 3. Run the dev server
export FLASK_ENV=development  # ensures .env is loaded
python run_dev.py  # or: flask run --port 5001 --debug
```

Live-reload & debugger are enabled, so code changes reflect automatically.

### Database helpers

The `azuredb_scripts` folder contains utilities to bootstrap or reset a local or remote DB:

```bash
python azuredb_scripts/init_db.py     # create tables
python azuredb_scripts/check_db.py    # inspect tables
python azuredb_scripts/reset_db.py    # drop & recreate
```

### Database Migrations

This project uses Alembic for database migrations. When you need to make changes to your models:

```bash
# 1. Make changes to your models
# 2. Generate migration
make migration-generate

# 3. Apply migration
make migrations

# 4. Check status
make migration-current
```

**Available migration commands:**
- `make migrations` - Apply all pending migrations
- `make migration-current` - Check current migration status
- `make migration-history` - Show migration history
- `make migration-generate` - Generate new migration from model changes
- `make migration-downgrade` - Downgrade to previous migration

**For Production:**
```bash
# Set production environment
export FLASK_ENV=production
export AZURE_SQL_CONNECTION_STRING="your_production_connection_string"

# Apply migrations
make migrations
```

## Azure Deployment Pipeline

Deployment is fully automated via GitHub Actions (see `.github/workflows/main_jarvus.yml`).
A push to `Production` will:

1. Build the project with Python 3.11
2. Install dependencies (incl. beta `azure-ai-inference`)
3. Zip **source + virtualenv**
4. Deploy to the `jarvus` Web App

No manual steps required, but you can trigger a run with the UI under **Actions → _Build & Deploy_ → _Run workflow_**.

## Azure CLI Cheat-Sheet

Real-time logs:

```bash
az webapp log tail --name jarvus --resource-group Jarvus
```

Turn on detailed application logging:

```bash
az webapp log config --name jarvus --resource-group Jarvus \
  --application-logging true --level information
```

Restart / browse:

```bash
az webapp restart --name jarvus --resource-group Jarvus
az webapp browse  --name jarvus --resource-group Jarvus
```

Stream container logs (Linux App Service):

```bash
az webapp log tail --provider containerapp --name jarvus --resource-group Jarvus
```

Scale up/down:

```bash
az appservice plan update --name jarvus-plan --resource-group Jarvus --sku P1v3
```

## Troubleshooting

* **`ModuleNotFoundError`** – ensure the package exists in `requirements.txt` **and** is successfully installed in the GitHub Action.
* **SQL login time-out** – verify firewall rules & increase `connect_timeout` in the connection string (300 s works well).
* **Env vars not picked up** – remember that `.env` is ignored in production; set keys in the portal or via

```bash
az webapp config appsettings set --name jarvus --resource-group Jarvus --settings KEY=value
```

Happy hacking! 😉