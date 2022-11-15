#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from dateutil import parser


# Basic full refresh stream
class PhilosophersApiStream(HttpStream, ABC):

    url_base = ""
    primary_key = "phil_id"

    def __init__(
        self,
        base_url: str,
    ):
        super().__init__()
        self.url_base = base_url

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        json_response = response.json()
        yield from json_response


# class Philosophers(PhilosophersApiStream):
#     def path(self, **kwargs) -> str:
#         return "philosophers"


# Basic incremental stream
class IncrementalPhilosophersApiStream(PhilosophersApiStream, ABC):
    @property
    def cursor_field(self) -> str:
        return "date_modified"

    def __init__(self,  base_url: str,):
        super().__init__(base_url)
        self._state = {self.cursor_field: "1970-01-01T00:00:00+00:00"}

    @property
    def state(self) -> Mapping[str, str]:
        return self._state

    @state.setter
    def state(self, value: Mapping[str, str]):
        self._state = value

    def read_records(self, *args, **kwargs) -> Iterable[Mapping[str, Any]]:
        for record in super().read_records(*args, **kwargs):
            current_cursor_value = parser.parse(
                self.state[self.cursor_field]).isoformat("T", "seconds")
            latest_cursor_value = parser.parse(
                record[self.cursor_field]).isoformat("T", "seconds")
            if latest_cursor_value > current_cursor_value:
                self.state = {
                    self.cursor_field: latest_cursor_value}
                yield record

    def request_headers(self, **kwargs) -> Mapping[str, Any]:
        last_modified = self.state[self.cursor_field]
        last_modified_date = parser.parse(last_modified)
        last_modified_iso = last_modified_date.isoformat("T", "seconds")
        return {
            "Modified-Since": last_modified_iso,
        }


class Philosophers(IncrementalPhilosophersApiStream):
    def path(self, **kwargs) -> str:
        return "philosophers"


# Source
class SourcePhilosophersApi(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        base_url = config["base_url"]

        try:
            resp = requests.get(base_url)
            if resp.status_code == 200:
                return True, None
            return False, "Connection failed"
        except Exception as e:
            return False, e

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        base_url = config["base_url"]
        return [Philosophers(base_url)]
