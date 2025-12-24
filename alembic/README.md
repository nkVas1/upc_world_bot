# Alembic migrations

This directory contains database migration scripts for UPC World Bot.

## Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field"

# Manual migration
alembic revision -m "Add new table"
```

## Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade [revision_id]

# Go back one version
alembic downgrade -1
```

## Checking Status

```bash
# Current version
alembic current

# History
alembic history
```

Each migration is a separate Python file with `upgrade()` and `downgrade()` functions.
