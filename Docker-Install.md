# Docker-install.md

## Installation
stable
```
$ docker pull kpjhg0124/fetea
```

dev
```
$ docker pull kpjhg0124/fetea-dev
```

## Start Application
```
docker run -d --name fetea(<name>) -v db(<data-path>):/app/data -p 2500(<port>):2500 kpjhg0124/fetea-dev
```