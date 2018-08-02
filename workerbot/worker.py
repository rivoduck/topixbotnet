import pika
import subprocess
import os
from time import sleep
from random import randint

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


# spawn subprocesses directly without shell
# output redirection is done in the function,
# do no use ">" or other output redirections in the command!!
def spawn_subprocesses(commandarray, count=1):
    global running_jobs
    global current_status
    
    start_delay_sec=20
    
    if current_status == 'IDLE':
        current_status = 'STARTING'
        
        for i in range(count):
            # running_jobs.append("job %d" % i)
            
            delay=start_delay_sec/count
            if delay < 1:
                delay=1
            
            delay=int(round(delay))
            
            sleep(randint(1,delay))
            #process = subprocess.Popen(commandarray, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            process = subprocess.Popen(commandarray, shell=False, stdout=subprocess.DEVNULL)
            
            running_jobs.append(str(process.pid))
            
        current_status = 'STARTED'
        message = "started %d instances of command [%s], PIDs [%s]" % ( count, " ".join(commandarray), ",".join(running_jobs) )
        publish_message(message)
    else:
        message = "worker status is %s. Cannot start new jobs" % current_status
        publish_message(message)



def do_status(com=[]):
    global running_jobs
    global current_status
    
    running_jobs_verified=[]
    for i in range(len(running_jobs)):
        return_code = subprocess.call("ps -o pid= -p %s" % running_jobs[i], shell=True)
        if return_code == 0:
            running_jobs_verified.append(running_jobs[i])
    
    running_jobs=running_jobs_verified
    
    if len(running_jobs) == 0:
        current_status = 'IDLE'
        
    publish_message ("status is %s, %d jobs running" % (current_status, len(running_jobs)))
    # subprocess.Popen("ps -ef", shell=True)


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

                       # commandarray=["./ffmpeg", "-i", ffmpeg_url, "-f", "rawvideo", "-", ">", "/dev/null", "2>&1"]
                       commandarray=["./ffmpeg", "-re", "-i", ffmpeg_url, "-f", "rawvideo", "-"]
                       
                       # get optional client number
                       if len(com)>0:
                           arg = com.pop(0)
                           try:
                               client_num = int(arg)
                               
                               # get optional wowza app instance
                               if len(com)>0:
                                   arg = com.pop(0)
                                   instance = arg
                               
                           except Exception as e:
                               syntaxerror = True

                       spawn_subprocesses(commandarray, client_num)
                       

    if syntaxerror:
        publish_message ("usage: unleash <wowza> <server> <application> <streamname> [number_of_streams_to_open] [application_instance]")

def do_stop(com=[]):
    global running_jobs
    global current_status
    if current_status == "STARTED":
        current_status = 'STOPPING'
        pidlist = []
        for i in range(len(running_jobs)):
            job=running_jobs.pop()
            pidlist.append(job)
        
            subprocess.Popen("kill -9 %s" % job, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        current_status = 'IDLE'
        publish_message("stopped PIDs [%s]" % ",".join(pidlist))
    else:
        message = "worker status is %s. Cannot stop jobs" % current_status
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
