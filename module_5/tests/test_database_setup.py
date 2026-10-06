"""Verify explicit schema setup and absence of implicit credential fallbacks."""

import runpy
from unittest.mock import Mock

import pytest

import load_data
import setup_database

pytestmark = pytest.mark.db


@pytest.mark.parametrize("entrypoint", ["function", "script"])
def test_admin_setup_executes_schema_only(postgres_db, capsys, entrypoint):
    if entrypoint == "function":
        setup_database.main()
    else:
        runpy.run_path(setup_database.__file__, run_name="__main__")
    assert "schema setup completed" in capsys.readouterr().out


@pytest.mark.parametrize("name", ["DB_NAME", "DB_USER"])
def test_loader_requires_explicit_database_identity(monkeypatch, name):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DB_USER" if name == "DB_NAME" else "DB_NAME", "test-only")
    connect = Mock()
    monkeypatch.setattr(load_data.psycopg, "connect", connect)
    with pytest.raises(KeyError, match=name):
        load_data.get_connection()
    connect.assert_not_called()
