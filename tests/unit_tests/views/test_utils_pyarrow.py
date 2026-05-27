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
"""Tests for pyarrow IPC serialization/deserialization in views/utils."""

from unittest.mock import MagicMock, patch

import msgpack
import pyarrow as pa
import pytest

from superset.exceptions import SerializationError
from superset.sqllab.utils import write_ipc_buffer


def test_deserialize_results_payload_invalid_ipc_data():
    """Corrupt IPC bytes should raise SerializationError (pa.lib.ArrowInvalid)."""
    from superset.views.utils import _deserialize_results_payload

    corrupt_payload = msgpack.dumps({"data": b"this-is-not-valid-ipc"}, use_bin_type=True)
    query_mock = MagicMock()

    with pytest.raises(SerializationError, match="Unable to deserialize table"):
        _deserialize_results_payload(corrupt_payload, query_mock, use_msgpack=True)


def test_ipc_roundtrip():
    """Verify IPC write/read round-trip produces identical data."""
    table = pa.table({"col_a": [1, 2, 3], "col_b": ["x", "y", "z"]})

    buf = write_ipc_buffer(table)

    reader = pa.BufferReader(buf)
    restored = pa.ipc.open_stream(reader).read_all()

    assert restored.equals(table)


def test_pyarrow_version_not_vulnerable():
    """Guard against accidental downgrade below the CVE-2023-47248 fix."""
    major, minor, patch_v = (int(x) for x in pa.__version__.split(".")[:3])
    assert (major, minor, patch_v) >= (14, 0, 1), (
        f"pyarrow {pa.__version__} is vulnerable to CVE-2023-47248; "
        "minimum safe version is 14.0.1"
    )
