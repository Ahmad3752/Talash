"""Add CrossRef enrichment columns to publications table.

No Alembic environment is currently configured in this project.
Use the SQL_STATEMENTS below with your DB client or migration runner.
"""

SQL_STATEMENTS = [
    "ALTER TABLE publications ADD COLUMN IF NOT EXISTS doi VARCHAR(255) NULL;",
    "ALTER TABLE publications ADD COLUMN IF NOT EXISTS publisher VARCHAR(255) NULL;",
    "ALTER TABLE publications ADD COLUMN IF NOT EXISTS journal_name VARCHAR(255) NULL;",
    "ALTER TABLE publications ADD COLUMN IF NOT EXISTS conference_name VARCHAR(255) NULL;",
    "ALTER TABLE publications ADD COLUMN IF NOT EXISTS conference_maturity VARCHAR(255) NULL;",
    "ALTER TABLE publications ADD COLUMN IF NOT EXISTS proceedings_publisher VARCHAR(255) NULL;",
]


def get_sql_statements() -> list[str]:
    return SQL_STATEMENTS.copy()


if __name__ == "__main__":
    for stmt in SQL_STATEMENTS:
        print(stmt)
