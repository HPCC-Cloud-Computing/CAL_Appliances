# Rabbit-MQ Notes

## Install

```bash
cong@cong-HP-ProBook-450-G1:~$ docker pull rabbitmq:3.6.12
cong@cong-HP-ProBook-450-G1:~$ docker run -d --hostname mcos-mq --name mcos-mq -p 4369:4369 -p 5671:5671 -p 5672:5672 -p 25672:25672 rabbitmq:3.6.12
cong@cong-HP-ProBook-450-G1:~$ docker exec -it mcos-mq /bin/bash
root@mcos-mq:/#rabbitmqctl add_user mcos bkcloud
root@mcos-mq:/#rabbitmqctl set_permissions mcos ".*" ".*" ".*"
```

## Exchange\_type and routing\_key binding relation

```bash

```

To illustrate how an RPC service could be used we're going to create a simple client class. It's going to expose a method named call which sends an RPC request and blocks until the answer is received:

## Celery

### What’s a Task Queue

Task queues are used as a mechanism to distribute work across threads or machines.

A task queue’s input is a unit of work called a task. Dedicated worker processes constantly monitor task queues for new work to perform.

Celery communicates via messages, usually using a broker to mediate between clients and workers. To initiate a task the client adds a message to the queue, the broker then delivers that message to a worker.

A Celery system can consist of multiple workers and brokers, giving way to high availability and horizontal scaling.

Celery is written in Python, but the protocol can be implemented in any language. In addition to Python there’s node-celery for Node.js, and a PHP client.

Language interoperability can also be achieved exposing an HTTP endpoint and having a task that requests it (webhooks).
