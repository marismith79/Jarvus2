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