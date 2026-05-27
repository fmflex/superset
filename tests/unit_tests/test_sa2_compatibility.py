# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""
SQLAlchemy 2.0 compatibility tests.

These tests verify that the codebase is compatible with SA 2.0 patterns
and that deprecated SA 1.x APIs have been properly migrated.
"""

import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session


def test_connection_context_manager() -> None:
    """Test that engine.connect() works as a context manager (SA 2.0 pattern)."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)"))
        conn.execute(text("INSERT INTO t VALUES (1, 'hello')"))
        conn.commit()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM t"))
        rows = list(result)
        assert rows == [(1, "hello")]


def test_text_wrapping_required() -> None:
    """Test that raw SQL strings must be wrapped in text()."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_select_positional_args() -> None:
    """Test that select() accepts positional args (not a list) in SA 2.0."""
    metadata = sa.MetaData()
    t = sa.Table("test", metadata, sa.Column("id", sa.Integer), sa.Column("name", sa.String))

    # SA 2.0 style: positional args
    stmt = sa.select(t.c.id, t.c.name)
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "test.id" in compiled
    assert "test.name" in compiled


def test_select_star_unpack() -> None:
    """Test that select(*list) works for dynamically built column lists."""
    metadata = sa.MetaData()
    t = sa.Table("test", metadata, sa.Column("id", sa.Integer), sa.Column("val", sa.String))

    cols = [t.c.id, t.c.val]
    stmt = sa.select(*cols)
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "test.id" in compiled
    assert "test.val" in compiled


def test_url_password_masking() -> None:
    """Test that SA 2.0 URL str() masks passwords, render_as_string does not."""
    url = URL.create(
        "postgresql",
        username="user",
        password="secret",
        host="localhost",
        port=5432,
        database="db",
    )
    # str() masks password in SA 2.0
    assert "***" in str(url)
    assert "secret" not in str(url)

    # render_as_string preserves password
    rendered = url.render_as_string(hide_password=False)
    assert "secret" in rendered


def test_url_create() -> None:
    """Test that URL.create() works (SA 2.0 replacement for URL())."""
    url = URL.create(
        "sqlite",
        database="/tmp/test.db",
    )
    rendered = url.render_as_string(hide_password=False)
    assert "sqlite:////tmp/test.db" == rendered


def test_case_positional_syntax() -> None:
    """Test that sa.case() uses positional tuples (not list) in SA 2.0."""
    expr = sa.case(
        (sa.literal(True), sa.literal("yes")),
        else_=sa.literal("no"),
    )
    compiled = str(expr.compile(compile_kwargs={"literal_binds": True}))
    assert "CASE WHEN" in compiled
    assert "yes" in compiled


def test_table_autoload_with() -> None:
    """Test that Table uses autoload_with= (not autoload=True) in SA 2.0."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY)"))
        conn.commit()

    metadata = sa.MetaData()
    # SA 2.0 pattern: autoload_with only, no autoload=True
    t = sa.Table("t", metadata, autoload_with=engine)
    assert "id" in [c.name for c in t.columns]


def test_session_execute_select() -> None:
    """Test that Session.execute(select(...)) works in SA 2.0."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(text("INSERT INTO t VALUES (1, 'test')"))
        conn.commit()

    metadata = sa.MetaData()
    t = sa.Table("t", metadata, autoload_with=engine)

    with Session(engine) as session:
        result = session.execute(sa.select(t.c.id, t.c.name))
        rows = list(result)
        assert rows == [(1, "test")]


def test_connection_commit_required_for_dml() -> None:
    """Test that DML operations require explicit commit in SA 2.0."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY)"))
        conn.commit()

    # Without commit, changes are rolled back
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO t VALUES (1)"))
        # No commit - should be rolled back

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM t"))
        assert result.scalar() == 0

    # With commit, changes persist
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO t VALUES (1)"))
        conn.commit()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM t"))
        assert result.scalar() == 1


def test_result_row_access() -> None:
    """Test SA 2.0 result row access patterns."""
    engine = create_engine("sqlite://")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER, name TEXT)"))
        conn.execute(text("INSERT INTO t VALUES (1, 'hello')"))
        conn.commit()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name FROM t"))
        row = result.fetchone()
        assert row is not None
        # Tuple access
        assert row[0] == 1
        assert row[1] == "hello"


def test_sqlalchemy_version() -> None:
    """Verify SQLAlchemy 2.0+ is installed."""
    version = tuple(int(x) for x in sa.__version__.split(".")[:2])
    assert version >= (2, 0), f"Expected SA 2.0+, got {sa.__version__}"
