"""
Static derivation of the canonical schema from supabase/migrations/*.sql.

This parses DDL in migration order and replays CREATE TABLE / ALTER TABLE ADD COLUMN /
DROP COLUMN / RENAME COLUMN to produce the table -> column map a freshly migrated
database would have.

It is a *static derivation*, not live introspection. It exists so the ORM -> database
column contract has coverage on machines and CI runners with no PostgreSQL available.
The authoritative check remains the live-introspection test in
tests/integration/test_orm_schema_contract_postgres.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Mapping

REPO_ROOT = Path(__file__).resolve().parents[4]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"

# Item prefixes inside CREATE TABLE (...) that declare a constraint, not a column.
_CONSTRAINT_PREFIXES = (
    "constraint",
    "primary",
    "unique",
    "foreign",
    "check",
    "exclude",
    "like",
)


@dataclass
class DerivedTable:
    name: str
    columns: Dict[str, str] = field(default_factory=dict)  # column name -> declared type


def _strip_noise(sql: str) -> str:
    """Remove dollar-quoted bodies (functions/DO blocks) and comments."""
    # Dollar-quoted strings can contain semicolons and parentheses that break naive parsing.
    sql = re.sub(r"\$([A-Za-z_]*)\$.*?\$\1\$", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return sql


def _split_top_level(body: str) -> List[str]:
    """Split a CREATE TABLE body on commas that are not nested in parentheses or quotes."""
    items: List[str] = []
    depth = 0
    current: List[str] = []
    quote: str | None = None
    for ch in body:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            current.append(ch)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


def _unquote(identifier: str) -> str:
    return identifier.strip().strip('"').strip()


def _bare_table(qualified: str) -> str:
    name = _unquote(qualified)
    if "." in name:
        schema, _, name = name.partition(".")
        if schema.lower() != "public":
            return ""  # only the public schema is part of the application contract
    return name


def _column_type(definition: str) -> str:
    """Best-effort declared type for a column definition item."""
    tokens = definition.strip().split(None, 1)
    if len(tokens) < 2:
        return ""
    rest = tokens[1].strip()
    # Type runs until a column constraint keyword.
    stop = re.search(
        r"\b(NOT\s+NULL|NULL|DEFAULT|REFERENCES|PRIMARY\s+KEY|UNIQUE|CHECK|GENERATED|COLLATE)\b",
        rest,
        flags=re.IGNORECASE,
    )
    declared = rest[: stop.start()] if stop else rest
    return " ".join(declared.split()).rstrip(",").strip()


_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w\".]+)\s*\(",
    flags=re.IGNORECASE,
)
_ALTER_TABLE_RE = re.compile(
    r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?([\w\".]+)\s+(.*?);",
    flags=re.IGNORECASE | re.DOTALL,
)
_ADD_COLUMN_RE = re.compile(
    r"ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w\"]+)\s*(.*)",
    flags=re.IGNORECASE | re.DOTALL,
)
_DROP_COLUMN_RE = re.compile(
    r"DROP\s+COLUMN\s+(?:IF\s+EXISTS\s+)?([\w\"]+)",
    flags=re.IGNORECASE,
)
_RENAME_COLUMN_RE = re.compile(
    r"RENAME\s+COLUMN\s+([\w\"]+)\s+TO\s+([\w\"]+)",
    flags=re.IGNORECASE,
)
_DROP_TABLE_RE = re.compile(
    r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([\w\".]+)",
    flags=re.IGNORECASE,
)
_RENAME_TABLE_RE = re.compile(r"RENAME\s+TO\s+([\w\"]+)", flags=re.IGNORECASE)


def _matching_paren(sql: str, open_index: int) -> int:
    depth = 0
    quote: str | None = None
    for i in range(open_index, len(sql)):
        ch = sql[i]
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _apply_create_table(sql: str, tables: Dict[str, DerivedTable]) -> None:
    for match in _CREATE_TABLE_RE.finditer(sql):
        table = _bare_table(match.group(1))
        if not table:
            continue
        open_index = match.end() - 1
        close_index = _matching_paren(sql, open_index)
        if close_index < 0:
            continue
        body = sql[open_index + 1 : close_index]
        derived = tables.setdefault(table, DerivedTable(name=table))
        for item in _split_top_level(body):
            if not item:
                continue
            first = item.split(None, 1)[0].lower().strip('"')
            if first in _CONSTRAINT_PREFIXES:
                continue
            column = _unquote(item.split(None, 1)[0])
            if column:
                derived.columns.setdefault(column, _column_type(item))


def _apply_alter_table(sql: str, tables: Dict[str, DerivedTable]) -> None:
    for match in _ALTER_TABLE_RE.finditer(sql):
        table = _bare_table(match.group(1))
        if not table or table not in tables:
            # ALTER on an unknown/other-schema table is not part of the derived contract.
            if not table:
                continue
            tables.setdefault(table, DerivedTable(name=table))
        derived = tables[table]
        actions = match.group(2)

        rename = _RENAME_COLUMN_RE.search(actions)
        if rename:
            old, new = _unquote(rename.group(1)), _unquote(rename.group(2))
            if old in derived.columns:
                derived.columns[new] = derived.columns.pop(old)
            else:
                derived.columns.setdefault(new, "")
            continue

        table_rename = _RENAME_TABLE_RE.search(actions)
        if table_rename and "COLUMN" not in actions.upper():
            new_name = _unquote(table_rename.group(1))
            derived.name = new_name
            tables[new_name] = tables.pop(table)
            continue

        for action in _split_top_level(actions):
            add = _ADD_COLUMN_RE.match(action.strip())
            if add:
                column = _unquote(add.group(1))
                derived.columns.setdefault(column, _column_type(f"{column} {add.group(2)}"))
                continue
            drop = _DROP_COLUMN_RE.match(action.strip())
            if drop:
                derived.columns.pop(_unquote(drop.group(1)), None)


def _apply_drop_table(sql: str, tables: Dict[str, DerivedTable]) -> None:
    for match in _DROP_TABLE_RE.finditer(sql):
        table = _bare_table(match.group(1))
        tables.pop(table, None)


def derive_schema(migration_files: List[str] | None = None) -> Dict[str, DerivedTable]:
    """Replay migrations in contract order and return the derived public schema."""
    from app.db.schema_contract import MIGRATION_FILES

    names = migration_files if migration_files is not None else MIGRATION_FILES
    tables: Dict[str, DerivedTable] = {}
    for name in names:
        path = MIGRATIONS_DIR / name
        sql = _strip_noise(path.read_text(encoding="utf-8"))
        _apply_create_table(sql, tables)
        _apply_alter_table(sql, tables)
        _apply_drop_table(sql, tables)
    return tables


def derived_table_columns() -> Mapping[str, frozenset[str]]:
    return {name: frozenset(t.columns) for name, t in derive_schema().items()}
