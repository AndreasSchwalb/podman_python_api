import time
from logging import getLogger
from typing import Dict

import requests
import requests_unixsocket
from extended_config_parser import ExtendedConfigParser

logger = getLogger('podman-api')
config = ExtendedConfigParser()


class PodmanSocket:

    def __init__(self, socket_path: str) -> None:
        socket_path = socket_path.replace('/', '%2F')
        self.session = requests_unixsocket.Session()
        self.socket = f'http+unix://{socket_path}'
        self._max_connection_retry = int(config['http']['connection_retry'])
        self._connection_retry = 0

    def get(
            self,
            url: str,
            query_params: Dict = None,
            **kwargs: Dict) -> requests.Response:

        try:
            return self.session.get(f"{self.socket}{url}", params=query_params, timeout=1)

        except requests.exceptions.ConnectionError:
            time.sleep(1)
            self._connection_retry += 1
            logger.warning(f'no connection to host {url}. Retry: {self._connection_retry}')
            if self._connection_retry < self._max_connection_retry:
                return self.get(
                    url=url,
                    query_params=query_params,
                    **kwargs
                )
            else:
                raise

    def post(
        self,
        url: str,
        query_params: Dict = None,
        body: Dict = None,
        timeout: int = 10,
        headers: Dict[str, str] = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        },
        **kwargs: Dict
    ) -> requests.Response:
        try:
            response = self.session.post(
                url=f"{self.socket}{url}",
                timeout=timeout,
                params=query_params,
                json=body,
                headers=headers,
                **kwargs
            )
            self._connection_retry = 0
            return response
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            self._connection_retry += 1
            logger.warning(f'no connection to host {url}. Retry: {self._connection_retry}')
            if self._connection_retry < self._max_connection_retry:
                return self.post(
                    url=url,
                    query_params=query_params,
                    body=body,
                    timeout=timeout,
                    **kwargs
                )
            else:
                raise

    def delete(self, url: str, **kwargs: Dict) -> requests.Response:
        try:
            return self.session.delete(
                url=f"{self.socket}{url}",
                timeout=10,
                headers={
                    'Accept': 'application/json'
                },
                **kwargs
            )
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            self._connection_retry += 1
            logger.warning(f'no connection to host {url}. Retry: {self._connection_retry}')
            if self._connection_retry < self._max_connection_retry:
                return self.delete(
                    url=url,
                    **kwargs
                )
            else:
                raise
