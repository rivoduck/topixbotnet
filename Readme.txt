Workers need a RabbitMQ server to communicate with, you can start a rabbitmq server using docker

get docker image
docker pull rabbitmq

start docker image
docker run -d --hostname botnet-rabbitmq --name botnet-rabbitmq -p 127.0.0.1:8080:15672 -p 5672:5672 rabbitmq:3-management



To deploy:
- copy the file workerbot/local_settings.py-example into workerbot/local_settings.py
- edit workerbot/local_settings.py with the address of your rabbitMQ installation and credentials
- cd workerbot/
- create a docker image with docker build -t botnet-worker .
- start the image with docker run -e PYTHONUNBUFFERED=0 botnet-worker


To deploy using docker remote image (here the link: https://hub.docker.com/r/blubecks/botnet_worker/):
- docker run -e PYTHONUNBUFFERED=0 -e PWD="..." blubecks/botnet_worker

You can pass different user and host using USER and HOST env variables.


Bots can be controlled from the rabbitMQ console using the exchange called "command_broadcast"
