from pprint import pprint

from podman_api import PodmanApi, PodmanSocket

socket_path = '/run/user/1000/podman/podman.sock'
pod_sock = PodmanSocket(socket_path)
api = PodmanApi(podman_socket=pod_sock)


# api.image_pull('alpine')

# api.image_build(
#     dockerfile_path='https://raw.githubusercontent.com/AndreasSchwalb/Containerfiles/master/alpine-ssh-rsync/Dockerfile',
#     tag='test:0.0.1'
# )

print(api.image_exists('test:0.0.1'))

# con = api.container_create(
#     image='test:0.0.1',
#     name='test-alpine',
#     env={
#         'test': 'test-val'
#     },
#     expose={
#         5555: 'tcp'
#     },
#     volumes=[
#         {
#             'Dest': '/vol_1',
#             'Name': 'test_vol'
#         }
#     ],
#     mounts=[
#         {
#             'Destination': '/test',
#             'Source': '/home/andy/Dokumente/python/podman_backup',
#             'Options': ['rbind']
#         }
#     ],
#     #command=['/usr/bin/tail', '-f', '/dev/null'],
#     command=["sh", "-c", 'echo "asdf" ; sleep 3'],
#     remove=False,
#     portmappings=[
#         {
#             "container_port": 1234,
#             "host_port": 1234
#         }
#     ]
# )

# print(f'container_id: {con}')

# api.container_start('test-alpine')

logs = api.container_logs('test-alpine',timestamp=True)


pprint(logs)

# api.container_pause('test-alpine')
# 
# api.container_unpause('test-alpine')

# api.container_stop('test-alpine')

# api.container_wait('test-alpine')

# api.container_delete('test-alpine')

# api.image_prune()

# pprint(api.image_list())
