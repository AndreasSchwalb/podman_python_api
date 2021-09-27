import json

from typing import Any, Dict, List

import requests


class PodmanApiResponse:

    successfully: bool = False
    message: Dict = {}

    def __init__(
        self,
        response: requests.Response
    ) -> None:

        self._successfull_satus_codes = [200, 201, 204]
        self._response = response

        self._analyze_response()

        self._data_as_dict = {
            'successfully': self.successfully,
            'message': self.message
        }

    def _analyze_response(self) -> None:
        parsed_response = [json.loads(c) for c in self._response.iter_lines()]

        if self._response.status_code in self._successfull_satus_codes:
            self.successfully = True

        self.message = self._join_dict(parsed_response)
        for a in self.message:
            if isinstance(a, dict) and 'error' in a.keys():
                self.successfully = False

    """
    Retruns a result dictonary with lower keys
    """

    def _join_dict(self, dict_list: List[Dict]) -> Dict:
        result: Dict[str, Any] = {}
        for dict_item in dict_list:

            if isinstance(dict_item, dict):
                keys = list(dict_item.keys())
                for key in keys:
                    lower_result_key = key[0].lower() + key[1:]

                    if lower_result_key in result.keys():
                        result[lower_result_key] = result[lower_result_key] + dict_item[key]
                    else:
                        result[lower_result_key] = dict_item[key]
            else:
                return dict_list[0]

        return result

    def __repr__(self) -> str:
        return json.dumps(self._data_as_dict)

    def json(self) -> Dict:
        return self._data_as_dict
