Workers need a RabbitMQ server to communicate with, you can start a rabbitmq server using docker

get docker image
docker pull rabbitmq

start docker image
docker run -d --hostname botnet-rabbitmq --name botnet-rabbitmq -p 127.0.0.1:8080:15672 -p 5672:5672 rabbitmq:3-management



To deploy:
- copy the file workerbot/local_settings.py-example into workerbot/local_settings.py
- edit workerbot/local_settings.py with the address of your rabbitMQ installation and credentials

Bots can be controlled from the rabbitMQ console using the exchange called "command_broadcast"

