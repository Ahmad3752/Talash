"""Lightweight psycopg2 compatibility shim backed by pg8000."""

import pg8000.dbapi as _dbapi

from pg8000.dbapi import *  # noqa: F401,F403

paramstyle = _dbapi.paramstyle
apilevel = _dbapi.apilevel
threadsafety = _dbapi.threadsafety

def connect(*args, **kwargs):
    if "dbname" in kwargs and "database" not in kwargs:
        kwargs["database"] = kwargs.pop("dbname")
    if "user" in kwargs and "username" not in kwargs:
        kwargs["user"] = kwargs.get("user")
    return _dbapi.connect(*args, **kwargs)

from . import extensions  # noqa: F401
from . import extras  # noqa: F401

Error = _dbapi.Error
Warning = _dbapi.Warning
InterfaceError = _dbapi.InterfaceError
DatabaseError = _dbapi.DatabaseError
DataError = _dbapi.DataError
OperationalError = _dbapi.OperationalError
IntegrityError = _dbapi.IntegrityError
InternalError = _dbapi.InternalError
ProgrammingError = _dbapi.ProgrammingError
NotSupportedError = _dbapi.NotSupportedError

__version__ = "2.9.9"
