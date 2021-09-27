
from pprint import pprint
from typing import Any, Dict, List

from extended_config_parser import ExtendedConfigParser

import requests
import json
import requests_unixsocket
import time


from logger import Logger

logger = Logger.setup('podman-backup')
config = ExtendedConfigParser()


class PodmanSocket:

    def __init__(self, socket_path: str) -> None:
        socket_path = socket_path.replace('/', '%2F')
        self.session = requests_unixsocket.Session()
        self.socket = f'http+unix://{socket_path}'
        self._max_connection_retry = int(config['http']['connection_retry'])
        self._connection_retry = 0

    def get(self, url: str, **kwargs: Dict) -> requests.Response:

        try:
            return self.session.get(f"{self.socket}{url}", timeout=1)

        except requests.exceptions.ConnectionError:
            time.sleep(1)
            self._connection_retry += 1
            logger.warning(f'no connection to host {url}. Retry: {self._connection_retry}')
            if self._connection_retry < self._max_connection_retry:
                return self.get(
                    url=url,
                    **kwargs
                )
            else:
                raise

    def post(
        self,
        url: str,
        query_params: Dict = None,
        body: Dict = None,
        timeout=10,
        **kwargs: Dict
    ) -> requests.Response:
        try:
            response = self.session.post(
                url=f"{self.socket}{url}",
                timeout=timeout,
                params=query_params,
                json=body,
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json'
                },
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


class PodmanApi:

    def __init__(
        self,
        podman_socket: PodmanSocket,
        api_version: str
    ) -> None:
        self.podman_socket = podman_socket
        self.api_version = api_version

    def image_list(self) -> List:
        logger.info(f'List images')
        url = f'/{self.api_version}/libpod/images/json'
        resp = self.podman_socket.get(url)
        result = PodmanApiResponse(resp)

        if result.successfully and isinstance(result.message, list):
            return result.message
        else:
            return []

    def image_inspect(self, name: str) -> Dict[str, Any]:
        logger.debug(f'Inspect image {name}')
        url = f'/{self.api_version}/libpod/images/{name}/json'
        resp = self.podman_socket.get(url)
        result = PodmanApiResponse(resp)

        if result.successfully and isinstance(result.message, dict):
            return result.message
        else:
            return {}

    def image_pull(self, name: str) -> str:
        logger.info(f'Pull image {name}')
        url = f'/{self.api_version}/libpod/images/pull'
        params = {'reference': name}
        resp = self.podman_socket.post(
            url=url,
            query_params=params,
        )

        result = PodmanApiResponse(resp)

        if result.successfully and result.message:
            id = result.message.get('id')
            if isinstance(id, str):
                image_name = name
                image_tags = (self.image_inspect(id)).get('repoTags')
                if isinstance(image_tags, list):
                    image_name = image_tags[0]

                logger.info(f'Pulled image {image_name}')
                return id

        return ''

    def container_create(
        self,
        image: str,
        name: str = None,
        env: Dict[str, str] = None,
        expose: Dict[int, str] = None,
        labels: Dict[str, Any] = None,
        volumes: List[Dict] = None,
        mounts: List[Dict] = None,
        portmappings: List[Dict] = None,
        command: List[str] = None,
        privileged: bool = False,
        remove: bool = False,
        user: str = None,
    ) -> str:
        logger.info(f'Create container from image {image}')
        body = {
            'image': image,
            'name': name,
            'env': env,
            'expose': expose,
            'labels': labels,
            'volumes': volumes,
            'mounts': mounts,
            'portmappings': portmappings,
            'command': command,
            'privileged': privileged,
            'remove': remove,
            'user': user
        }

        url = f'/{self.api_version}/libpod/containers/create'

        resp = self.podman_socket.post(
            url=url,
            body=body,
        )

        result = PodmanApiResponse(resp)

        if result.successfully:
            logger.info(f"Created container {name}")
            container_id = result.message.get('id')
            if isinstance(container_id, str):
                return container_id
        else:
            logger.warning(f"Could not create container {name}. {result.message.get('cause')}")

        return ''

    def container_delete(self, name: str) -> None:
        logger.info(f'Delete container {name}')
        container_exists = self.container_exists(name)
        if container_exists:
            container_status = 'unkown'
            container_details = self.container_inspect(name)
            container_states = container_details.get('state')
            if container_states:
                container_status = container_states.get('Status')

            if container_status == 'exited' or container_status == 'configured':
                url = f'/{self.api_version}/libpod/containers/{name}'
                resp = self.podman_socket.delete(url=url)
                result = PodmanApiResponse(resp)
            else:
                logger.warning(f"Can not delete container with status {container_status}")
                return
        else:
            logger.warning(f"container {name} does not exist")
            return

        if result.successfully:
            logger.info(f"Deleted container {name}")
        else:
            logger.warning(f"Could not delete Container {name}")
            if result.message:
                logger.warning(f"{result.message.get('cause')}")

    def container_start(self, name: str) -> None:
        logger.info(f'Start container {name}')
        container_exists = self.container_exists(name)
        if container_exists:
            url = f'/{self.api_version}/libpod/containers/{name}/start'
            resp = self.podman_socket.post(url=url)

            result = PodmanApiResponse(resp)
        else:
            logger.warning(f"Could not start container {name}. Container does not exists")
            return

        if result.successfully:
            logger.info(f"Started container {name}")
        else:
            logger.warning(f"Could not start container {name}. {result.message.get('cause')}")

    def container_stop(self, name: str) -> None:
        logger.info(f'Stop container {name}')
        if self.container_exists(name):
            url = f'/{self.api_version}/libpod/containers/{name}/stop'
            resp = self.podman_socket.post(url=url, timeout=60)
            result = PodmanApiResponse(resp)
        else:
            logger.warning(f"Could not stop container {name}. Container does not exists")
            return

        if result.successfully:
            logger.info(f"Stopped container {name}")
        else:
            logger.warning(f"Could not stop container {name}. {result.message.get('cause')}")

    def container_inspect(self, name: str) -> Dict[str, Any]:
        logger.debug(f'Inspect container {name}')
        if self.container_exists(name):
            url = f'/{self.api_version}/libpod/containers/{name}/json'
            resp = self.podman_socket.get(url)
            result = PodmanApiResponse(resp)
        else:
            logger.warning(f"container {name} does not exist")
            return {}

        if result.successfully and isinstance(result.message, dict):
            return result.message
        else:
            return {}

    def container_exists(self, name: str) -> bool:

        if name:
            url = f'/{self.api_version}/libpod/containers/{name}/exists'
            resp = self.podman_socket.get(url)
            result = PodmanApiResponse(resp)
        else:
            logger.warning("No container name was given")
            return False

        if result.successfully:
            return True
        else:
            return False


if __name__ == '__main__':

    socket_path = '/run/user/1000/podman/podman.sock'
    pod_sock = PodmanSocket(socket_path)
    api = PodmanApi(
        podman_socket=pod_sock,
        api_version="v3.0.0"
    )

    #pull = api.image_pull('alpine')

    api.container_stop('test-alpine')
    api.container_delete('test-alpine')
    con = api.container_create(
        image='alpine',
        name='test-alpine',
        env={
            'test': 'test-val'
        },
        expose={
            5555: 'tcp'
        },
        volumes=[
            {
                'Dest': '/vol_1',
                'Name': 'test_vol'
            }
        ],
        mounts=[
            {
                'Destination': '/test',
                'Source': '/home/andy/Dokumente/python/podman-backup',
                'Options': ['rbind']
            }
        ],
        command=['/usr/bin/tail', '-f', '/dev/null'],
        remove=False,
        portmappings=[
            {
                "container_port": 1234,
                "host_port": 1234
            }
        ]
    )

    img_list = api.image_list()
    # img_insp = api.image_inspect(pull)
    # pprint(img_insp)

    api.container_start('test-alpine')
    # pprint(api.container_inspect(con))

    print(api.image_list())
