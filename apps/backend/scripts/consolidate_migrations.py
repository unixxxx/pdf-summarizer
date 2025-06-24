#!/usr/bin/env python3
"""
Migration Consolidation Helper Script

This script helps with consolidating database migrations for cleaner deployments.
It provides utilities for backing up current state, applying consolidated migration,
and verifying the results.
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import asyncio
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import create_async_engine


class MigrationConsolidator:
    """Helper class for migration consolidation tasks."""
    
    def __init__(self, database_url: str, alembic_dir: str = "alembic"):
        self.database_url = database_url
        self.async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.alembic_dir = Path(alembic_dir)
        self.versions_dir = self.alembic_dir / "versions"
        self.backup_dir = self.alembic_dir / "versions_backup"
        
    def backup_migrations(self) -> None:
        """Backup current migration files."""
        if self.backup_dir.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"versions_backup_{timestamp}"
            shutil.move(str(self.backup_dir), str(self.alembic_dir / backup_name))
            
        shutil.copytree(str(self.versions_dir), str(self.backup_dir))
        print(f"✓ Backed up migrations to {self.backup_dir}")
        
    def clear_migrations(self) -> None:
        """Remove all migration files except __pycache__."""
        migration_files = list(self.versions_dir.glob("*.py"))
        for file in migration_files:
            if file.name != "__init__.py":
                file.unlink()
        print(f"✓ Removed {len(migration_files)} migration files")
        
    def install_consolidated_migration(self) -> None:
        """Copy consolidated migration to versions directory."""
        consolidated_file = self.versions_dir / "consolidated_initial_migration.py"
        if not consolidated_file.exists():
            print("✗ Consolidated migration file not found!")
            print("  Please ensure consolidated_initial_migration.py exists in the versions directory")
            sys.exit(1)
        print("✓ Consolidated migration file is in place")
        
    async def check_database_state(self) -> dict:
        """Check current database state."""
        engine = create_async_engine(self.async_database_url)
        
        async with engine.begin() as conn:
            # Check if alembic_version table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename = 'alembic_version'
                )
            """))
            has_alembic = result.scalar()
            
            # Get current revision if alembic table exists
            current_revision = None
            if has_alembic:
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                row = result.fetchone()
                if row:
                    current_revision = row[0]
            
            # Get list of existing tables
            result = await conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename != 'alembic_version'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            
            # Count records in each table
            table_counts = {}
            for table in tables:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                table_counts[table] = result.scalar()
                
        await engine.dispose()
        
        return {
            'has_alembic': has_alembic,
            'current_revision': current_revision,
            'tables': tables,
            'table_counts': table_counts
        }
        
    def run_alembic_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run an alembic command."""
        cmd = ["alembic"] + command
        return subprocess.run(cmd, capture_output=True, text=True)
        
    async def verify_schema(self) -> bool:
        """Verify the schema matches expectations."""
        expected_tables = {
            'users', 'documents', 'folders', 'tags', 'summaries',
            'document_chunks', 'chats', 'chat_messages',
            'document_tags', 'folder_tags'
        }
        
        state = await self.check_database_state()
        actual_tables = set(state['tables'])
        
        missing_tables = expected_tables - actual_tables
        extra_tables = actual_tables - expected_tables
        
        if missing_tables:
            print(f"✗ Missing tables: {', '.join(missing_tables)}")
            
        if extra_tables:
            print(f"⚠ Extra tables: {', '.join(extra_tables)}")
            
        return len(missing_tables) == 0
        
    def backup_database(self, output_file: Optional[str] = None) -> str:
        """Create a database backup using pg_dump."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"backup_{timestamp}.sql"
            
        # Extract connection details from database URL
        # Format: postgresql://user:password@host:port/database
        import urllib.parse
        parsed = urllib.parse.urlparse(self.database_url)
        
        env = os.environ.copy()
        if parsed.password:
            env['PGPASSWORD'] = parsed.password
            
        cmd = [
            'pg_dump',
            '-h', parsed.hostname or 'localhost',
            '-p', str(parsed.port or 5432),
            '-U', parsed.username or 'postgres',
            '-d', parsed.path.lstrip('/'),
            '-f', output_file
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Database backed up to {output_file}")
            return output_file
        else:
            print(f"✗ Backup failed: {result.stderr}")
            sys.exit(1)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Database Migration Consolidation Helper')
    parser.add_argument('action', choices=['check', 'backup', 'consolidate', 'verify'],
                       help='Action to perform')
    parser.add_argument('--database-url', default=None,
                       help='Database URL (defaults to DATABASE_URL env var)')
    parser.add_argument('--skip-backup', action='store_true',
                       help='Skip database backup (consolidate only)')
    parser.add_argument('--force', action='store_true',
                       help='Force action without confirmation')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        print("✗ No database URL provided. Set DATABASE_URL or use --database-url")
        sys.exit(1)
        
    consolidator = MigrationConsolidator(database_url)
    
    if args.action == 'check':
        # Check current database state
        state = await consolidator.check_database_state()
        
        print("\n=== Database State ===")
        print(f"Alembic initialized: {state['has_alembic']}")
        if state['current_revision']:
            print(f"Current revision: {state['current_revision']}")
        print(f"\nTables ({len(state['tables'])}):")
        for table in state['tables']:
            count = state['table_counts'][table]
            print(f"  - {table}: {count:,} records")
            
    elif args.action == 'backup':
        # Create database backup
        consolidator.backup_database()
        
    elif args.action == 'consolidate':
        # Perform full consolidation
        print("\n=== Migration Consolidation ===")
        print("This will:")
        print("1. Backup current migration files")
        print("2. Create a database backup")
        print("3. Clear existing migrations")
        print("4. Apply consolidated migration")
        print("\n⚠️  This is a destructive operation!")
        
        if not args.force:
            response = input("\nContinue? [y/N]: ")
            if response.lower() != 'y':
                print("Aborted.")
                return
                
        # Step 1: Backup migrations
        consolidator.backup_migrations()
        
        # Step 2: Backup database
        if not args.skip_backup:
            consolidator.backup_database()
        else:
            print("⚠ Skipping database backup (--skip-backup)")
            
        # Step 3: Check consolidated migration exists
        consolidator.install_consolidated_migration()
        
        # Step 4: Get current state
        state = await consolidator.check_database_state()
        
        # Step 5: Clear migrations
        consolidator.clear_migrations()
        
        # Step 6: Downgrade if needed
        if state['has_alembic'] and state['current_revision']:
            print("\n📦 Downgrading database...")
            result = consolidator.run_alembic_command(['downgrade', 'base'])
            if result.returncode != 0:
                print(f"✗ Downgrade failed: {result.stderr}")
                print("💡 You may need to manually drop tables and try again")
                sys.exit(1)
            print("✓ Database downgraded")
            
        # Step 7: Apply consolidated migration
        print("\n🚀 Applying consolidated migration...")
        result = consolidator.run_alembic_command(['upgrade', 'head'])
        if result.returncode != 0:
            print(f"✗ Migration failed: {result.stderr}")
            sys.exit(1)
        print("✓ Consolidated migration applied")
        
        # Step 8: Verify
        if await consolidator.verify_schema():
            print("\n✅ Migration consolidation complete!")
        else:
            print("\n⚠️  Schema verification failed. Please check the database.")
            
    elif args.action == 'verify':
        # Verify schema integrity
        if await consolidator.verify_schema():
            print("✅ Schema verification passed")
        else:
            print("✗ Schema verification failed")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())