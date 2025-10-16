"""Database initialization script."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import init_db, drop_tables


def main():
    """Initialize the database by creating all tables."""
    print("Initializing database...")
    print("Creating tables...")

    try:
        init_db()
        print("✓ Database initialized successfully!")
        print("✓ All tables created.")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)


def reset_db():
    """Reset the database by dropping and recreating all tables."""
    print("⚠️  WARNING: This will delete all data in the database!")
    confirm = input("Type 'yes' to confirm: ")

    if confirm.lower() != 'yes':
        print("Database reset cancelled.")
        return

    print("Dropping all tables...")
    try:
        drop_tables()
        print("✓ All tables dropped.")

        print("Creating tables...")
        init_db()
        print("✓ Database reset successfully!")
    except Exception as e:
        print(f"✗ Error resetting database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop and recreate all tables)"
    )

    args = parser.parse_args()

    if args.reset:
        reset_db()
    else:
        main()
