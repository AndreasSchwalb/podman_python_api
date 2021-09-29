from typing import Any, Dict, List
from pprint import pformat

from extended_config_parser import ExtendedConfigParser
from custom_logger import Logger

from .podman_api_response import PodmanApiResponse
from .podman_socket import PodmanSocket

logger = Logger.setup('podman-api')
config = ExtendedConfigParser()


class PodmanApi:

    def __init__(
        self,
        podman_socket: PodmanSocket,
    ) -> None:
        self.podman_socket = podman_socket
        self.api_version = 'v3.0.0'

    def image_list(self) -> List:
        logger.info('List images')
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

    def image_build(
        self,
        tag: str,
        dockerfile_path: str = None,
        dockerfile_remote_url: str = None,
    ) -> None:
        logger.info('Build image')
        url = f'/{self.api_version}/libpod/build'
        params = {
            'dockerfile': dockerfile_path,
            'remote': dockerfile_remote_url,
            't': tag,
            'rm': True

        }
        resp = self.podman_socket.post(
            url=url,
            query_params=params,
            headers={
                'Accept': 'application/json'
            },

        )

        result = PodmanApiResponse(resp)

        logger.debug(pformat(result.message))

        if result.successfully:
            logger.info(f'build image {tag}')
        else:
            logger.warning(f"Could not build image {tag}. {result.message.get('cause')}")

    def image_exists(self, name: str) -> bool:

        if name:
            url = f'/{self.api_version}/libpod/images/{name}/exists'
            resp = self.podman_socket.get(url)
            result = PodmanApiResponse(resp)
        else:
            logger.warning("No image name was given")
            return False

        if result.successfully:
            return True
        else:
            return False

    def image_prune(self) -> None:
        logger.info('Prune unused images')
        url = f'/{self.api_version}/libpod/images/prune'
        params = {'filters': 'dangling=true'}
        resp = self.podman_socket.post(
            url=url,
            query_params=params,
            headers={
                'Accept': 'application/json'
            },

        )

        result = PodmanApiResponse(resp)
        if result.successfully:
            logger.info(f'deleted {len(result.message)} images')
        else:
            logger.warning(f"Could not prune images. {result.message.get('cause')}")

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

    def container_pause(self, name: str) -> None:
        logger.info(f'Pause container {name}')
        container_exists = self.container_exists(name)
        if container_exists:

            url = f'/{self.api_version}/libpod/containers/{name}/pause'
            resp = self.podman_socket.post(url=url)
            result = PodmanApiResponse(resp)
        else:
            logger.warning(f"container {name} does not exist")
            return

        if result.successfully:
            logger.info(f"Paused container {name}")
        else:
            logger.warning(f"Could not pause Container {name}")
            if result.message:
                logger.warning(f"{result.message.get('cause')}")

    def container_unpause(self, name: str) -> None:
        logger.info(f'Unpause container {name}')
        container_exists = self.container_exists(name)
        if container_exists:

            url = f'/{self.api_version}/libpod/containers/{name}/unpause'
            resp = self.podman_socket.post(url=url)
            result = PodmanApiResponse(resp)
        else:
            logger.warning(f"container {name} does not exist")
            return

        if result.successfully:
            logger.info(f"Unpaused container {name}")
        else:
            logger.warning(f"Could not unpause container {name}")
            if result.message:
                logger.warning(f"{result.message.get('cause')}")

    def container_wait(
        self,
        name: str,
        condition: str = "exited",
        request_interval: str = "250ms"
    ) -> None:
        logger.info(f'Wait for container {name}')
        container_exists = self.container_exists(name)
        if container_exists:

            url = f'/{self.api_version}/libpod/containers/{name}/wait'
            resp = self.podman_socket.post(
                url=url,
                query_params={
                    'condition': condition,
                    'interval': request_interval
                },
                timeout=1000
            )
            result = PodmanApiResponse(resp)
        else:
            logger.warning(f"container {name} does not exist")
            return

        if result.successfully:
            logger.info(f"Contidion {condition} of container {name} reached")
        else:
            logger.warning(f"Could not wait for container {name}")
            if result.message:
                logger.warning(f"{result.message.get('cause')}")
