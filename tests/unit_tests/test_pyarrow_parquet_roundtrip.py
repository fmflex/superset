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
"""Test Parquet read/write round-trip with current pyarrow version."""

import tempfile

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def test_parquet_roundtrip():
    """Write and read a Parquet file to verify pyarrow Parquet compatibility."""
    df = pd.DataFrame(
        {
            "int_col": [1, 2, 3],
            "str_col": ["a", "b", "c"],
            "float_col": [1.1, 2.2, 3.3],
        }
    )
    table = pa.Table.from_pandas(df)

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        pq.write_table(table, tmp.name)
        restored = pd.read_parquet(tmp.name)

    pd.testing.assert_frame_equal(df, restored)


def test_parquet_file_metadata():
    """Verify ParquetFile metadata access works (used by columnar_reader)."""
    df = pd.DataFrame({"col_a": [1], "col_b": ["x"]})
    table = pa.Table.from_pandas(df)

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        pq.write_table(table, tmp.name)
        parquet_file = pq.ParquetFile(tmp.name)
        column_names = parquet_file.metadata.schema.names

    assert "col_a" in column_names
    assert "col_b" in column_names
