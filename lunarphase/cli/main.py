import argparse
import asyncio
import sys
from lunarphase.migrations.runner import MigrationRunner
from lunarphase.db.engine import get_engine

async def run_cli():
    parser = argparse.ArgumentParser(prog="lunarphase", description="LunarPhaseORM CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    make_mig = subparsers.add_parser("make:migration", help="Generate a new DDL schema migration file")
    make_mig.add_argument("name", help="Name of the migration e.g. create_users_table")

    subparsers.add_parser("migrate", help="Apply pending database migrations")
    subparsers.add_parser("rollback", help="Rollback the last applied migration")
    subparsers.add_parser("status", help="Show migration status")

    args = parser.parse_args()
    runner = MigrationRunner()

    try:
        if args.command == "make:migration":
            # Imports user models registered in current working directory if available
            await runner.make_migration(args.name, [])
        elif args.command == "migrate":
            await runner.migrate()
        elif args.command == "rollback":
            await runner.rollback()
        elif args.command == "status":
            engine = get_engine()
            await runner.init_migration_table()
            rows = await engine.fetch_all("SELECT name, applied_at FROM _lunarphase_migrations ORDER BY id ASC;")
            print("\n--- LunarPhaseORM Migration Status ---")
            if not rows:
                print("No migrations applied yet.")
            else:
                for r in rows:
                    print(f" [X] {r['name']} (applied: {r['applied_at']})")
            print("--------------------------------------\n")
        else:
            parser.print_help()
    finally:
        engine = get_engine()
        await engine.disconnect()


def cli_entrypoint():
    asyncio.run(run_cli())

if __name__ == "__main__":
    cli_entrypoint()
