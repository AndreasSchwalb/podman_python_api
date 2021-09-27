# Podman API wrapper
This library wrappes the podman REST API to python methods.
Acctually it is just a proof of concept. None of the implementations are finished.
Even the arcitecture may change in further versions.


## Create an instance
```python
socket_path = '/run/user/1000/podman/podman.sock'
pod_sock = PodmanSocket(socket_path)
api = PodmanApi(
    podman_socket=pod_sock,
    api_version="v3.0.0"
    )
```

## Image methods
### list
list all locally available images
```python
img_list = api.image_list()
print(img_list)
```


### inspect
show the details of an image
list all locally available images

```python
img_insp = api.image_inspect()
print(img_insp)
```

### pull
pull the named image

```python
pull = api.image_pull('alpine')
print(pull)
```

## Container methods

### create
create a container with the given parameter

| parameter    | mandentory | default | description                                 |
|--------------|------------|---------|---------------------------------------------|
| image        | true       |         | the name of the base image                  |
| name         | false      |         | the name of the container                   |
| env          | false      |         | dictonary of environment variables          |
| expose       | false      |         | exposed ports                               |
| labels       | false      |         | labels of the container                     |
| volumes      | false      |         | list of volumes of the container            | 
| mounts       | false      |         |bind mounts of the container                 |
| portmappings | false      |         | List of mapped ports from container to host |
| command      | false      |         |command to run in the container              |
| privileged   | false      | false   | flag to run container in privileged mode    |
| remove       | false      | false   | remove container when it stopps             |
| user         | false      |         | uid or username th container should run with|

```
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

```

### delete
delete a container
```
api.container_delete('test-alpine')
```

### start

start a container
```
api.container_start('test-alpine')
```

### stop

stop a container
```
api.container_stop('test-alpine')
```

### inspect

get details of a container
```
api.container_inspect('test-alpine')
```

### exists

check if a container exists
```
api.container_exists('test-alpine')
```