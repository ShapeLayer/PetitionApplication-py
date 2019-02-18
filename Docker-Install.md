# Docker-install.md

## Installation
stable
```
$ docker pull kpjhg0124/fetea           # latest commit
$ docker pull kpjhg0124/fetea:arm32v7   # arm32v7
```

dev
```
$ docker pull kpjhg0124/fetea-dev
```

## Start Application
```
$ docker run -d --name <name> -v <data-path>:/app/data -p <port>:2500 kpjhg0124/fetea(-dev)
$ docker urn -d --name fetea -v data:/app/data -p 2500:2500 kpjhg0124/fetea(-dev)
```