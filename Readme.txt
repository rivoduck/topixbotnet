get docker image
docker pull rabbitmq

start docker image
docker run -d --hostname botnet-rabbitmq --name botnet-rabbitmq -p 127.0.0.1:8080:15672 -p 5672:5672 rabbitmq:3-management


