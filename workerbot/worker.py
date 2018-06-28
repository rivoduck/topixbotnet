import pika
import subprocess
import os


exch_command_broadcast = "command_broadcast"
queue_status_report = "status_report"

running_jobs = []
current_status = 'IDLE'

try:
    rabbit_pw = os.environ['PWD']
except KeyError:
    print ("Password is a mandatory field.")
    exit(-1)

try:
    from local_settings import rabbit_user
except ImportError:
    try:
        rabbit_user = os.environ['USER']
    except KeyError:
        print ("User is a mandatory field.")
        exit(-1)

try:
    from local_settings import rabbit_host
except ImportError:
    try:
        rabbit_host = os.environ['HOST']
    except KeyError:
        print ("Host is a mandatory field.")
        exit(-1)


credentials = pika.PlainCredentials(rabbit_user, rabbit_pw)
parameters = pika.ConnectionParameters(rabbit_host,
                                   5672,
                                   '/',
                                   credentials)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()




def publish_message(message):
    print(message)
    channel.basic_publish(exchange='', routing_key="status_report", body=message)


def spawn_subprocesses(command, count=1):
    global running_jobs
    global current_status

    if current_status == 'IDLE':
        message = "going to run %d instances of command [%s]" % (count, command)
        publish_message(message)

        current_status = 'STARTING'
        for i in range(count):
            running_jobs.append("job %d" % i)
        current_status = 'STARTED'
    else:
        message = "worker status is %s. Cannot start new jobs" % current_status
        publish_message(message)



def do_status(com=[]):
    global running_jobs
    global current_status

    publish_message ("status is %s" % current_status)
    for job in running_jobs:
        print(job)


def do_unleash(com=[]):
    syntaxerror = True
    arg=None
    if len(com)>0:
        arg = com.pop(0)
        if arg == "wowza":
            if len(com)>0:
               arg = com.pop(0)
               server = arg
               if len(com)>0:
                   arg = com.pop(0)
                   app = arg
                   if len(com)>0:
                       arg = com.pop(0)
                       stream = arg
                       syntaxerror = False

                       instance = "_definst_"
                       client_num = 3

                       ffmpeg_url="http://%s/%s/%s/%s/playlist.m3u8" % (server, app, instance, stream)

                       commandline="ffmpeg -i %s > /dev/null 2>&1" % ffmpeg_url

                       spawn_subprocesses(commandline, client_num)


    if syntaxerror:
        publish_message ("usage: unleash <wowza> <server> <application> <streamname> [number_of_streams_to_open] [application_instance]")

def do_stop(com=[]):
    global running_jobs
    global current_status

    current_status = 'STOPPING'
    message = ""
    for i in range(len(running_jobs)):
        job=running_jobs.pop()
        message = message + "stopping [%s]\n" % job
    current_status = 'IDLE'
    publish_message(message)







def callback(ch, method, properties, body):

    allowed_commands = {
        "unleash": do_unleash,
        "stop": do_stop,
        "status": do_status,

    }



    body = body.decode("utf-8")
    # print(" [x] Received %r" % body)
    command_arr = body.split()

    # interpret command
    if len(command_arr)>0:
        command = command_arr.pop(0)



        if command in allowed_commands:
            allowed_commands[command](command_arr)

        else:
            publish_message ("unrecognized command [%s]\nallowed commands %s" % (command, list(allowed_commands.keys())))
    else:
        publish_message ("nothing to do...\nallowed commands %s" % list(allowed_commands.keys()))





channel.queue_declare(queue=queue_status_report)

channel.exchange_declare(exchange=exch_command_broadcast, exchange_type='fanout')
result = channel.queue_declare(exclusive=True)
broadcast_queue_name = result.method.queue
channel.queue_bind(exchange=exch_command_broadcast, queue=broadcast_queue_name)

channel.basic_consume(callback, queue=broadcast_queue_name, no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
