#
# Copyright (c) 2012-2022 Snowflake Computing Inc. All rights reserved.
#
from enum import Enum
from typing import List

from snowflake.connector import SnowflakeConnection
from snowflake.connector.cursor import ResultMetadata
from snowflake.snowpark._internal.utils import result_set_to_iter, result_set_to_rows


class AsyncDataType(Enum):
    PANDAS = "pandas"
    ROW = "row"
    ITERATOR = "iterator"
    PANDAS_BATCH = "pandas_batch"


class AsyncJob:
    def __init__(
        self,
        query_id: str,
        query: str,
        conn: SnowflakeConnection,
        result_meta: List[ResultMetadata],
        data_type: AsyncDataType = AsyncDataType.ROW,
    ) -> None:
        self.query_id = query_id
        self.query = query
        self._conn = conn
        self._cursor = self._conn.cursor()
        self._data_type = data_type
        self._result_meta = result_meta

        return

    def is_done(self) -> bool:
        # return a bool value to indicate whether the query is finished
        status = self._conn.get_query_status(self.query_id)
        is_running = self._conn.is_still_running(status)

        return not is_running

    def cancel(self) -> None:
        # stop and cancel current query id
        self._conn._cancel_query(self.query, self.query_id)

    def result(self):
        # return result of the query, in the form of a list of Row object
        self._cursor.get_results_from_sfqid(self.query_id)
        result_data = self._cursor.fetchall()
        if self._data_type == AsyncDataType.ROW:
            return result_set_to_rows(result_data, self._result_meta)
        elif self._data_type == AsyncDataType.ITERATOR:
            return result_set_to_iter(result_data, self._result_meta)
        elif self._data_type == AsyncDataType.PANDAS:
            return self._cursor.fetch_pandas_all()
        elif self._data_type == AsyncDataType.PANDAS_BATCH:
            return iter([self._cursor.fetch_pandas_all()])
        else:
            raise ValueError(f"{self._data_type} is not a supported data type")
