"""Minimal psycopg2.extensions compatibility layer."""

from pg8000.dbapi import (  # noqa: F401
    Binary,
    Connection,
    Cursor,
    DataError,
    DatabaseError,
    Error,
    IntegrityError,
    InterfaceError,
    InternalError,
    NotSupportedError,
    OperationalError,
    ProgrammingError,
    Warning,
)

ISOLATION_LEVEL_AUTOCOMMIT = 0


class register_adapter:
    def __init__(self, *args, **kwargs):
        pass


def adapt(value):
    return value


def register_type(*args, **kwargs):
    return None


def new_type(*args, **kwargs):
    return None


def new_array_type(*args, **kwargs):
    return None


def register_default_json(*args, **kwargs):
    return None


def register_default_jsonb(*args, **kwargs):
    return None


def set_wait_callback(*args, **kwargs):
    return None


class QuotedString(str):
    pass


class AsIs(str):
    pass
