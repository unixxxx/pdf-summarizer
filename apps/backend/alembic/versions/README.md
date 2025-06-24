# Database Migrations

This directory contains both individual migration files and a consolidated migration.

## For Existing Environments

If you have an existing database, continue using the incremental migrations:

```bash
alembic upgrade head
```

## For New Deployments

For brand new deployments, you can use the consolidated migration:

1. Ensure your database is empty
2. Edit `alembic_version` table if needed
3. Run: `alembic upgrade consolidated_initial`

## Important Notes

- **DO NOT DELETE** the individual migration files - they are needed for existing environments
- The `consolidated_initial_migration.py` is a complete schema snapshot as of 2025-06-14
- Always backup your database before running migrations
- See `docs/MIGRATION_STRATEGY.md` for detailed migration management guidelines

## Current Migration Head

As of the consolidation date, the latest migration is:

- `c3988533a3ff` - Add pgvector HNSW indexes

## Files

- Individual migrations: All files with revision IDs (e.g., `648d2c7e14b6_*.py`)
- Consolidated migration: `consolidated_initial_migration.py`
