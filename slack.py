import time
from slackclient import SlackClient
import ledMatrix
import websocket
from threading import Thread
from Queue import Queue
import json

token = "XXX"      # found at https://api.slack.com/web#authentication
sc = SlackClient(token)
userTable = {}
queue = Queue(10)

class ProducerThread(Thread):
    def run(self):
        global queue
        while True:
            if sc.rtm_connect():
                while True:
                    message = sc.rtm_read()
                    print message
                    if message != [] and 'text' in message[0]:
                        user = userTable[message[0]['user']]
                        text = message[0]['text']
                        message = '{0}: {1}'.format(user, text)
                        queue.put(message)
                        print "Added to queue:", message
                    time.sleep(1)
            else:
                raise Exception

class ConsumerThread(Thread):
    def run(self):
        global queue
        while True:
           if not queue.empty():
                message = queue.get()
                ledMatrix.sendMessageToMatrix(message)
                queue.task_done()
                print "Queue Consumed:", message
                time.sleep(2)

def buildUserTable():
    usersJson = json.loads(sc.api_call("users.list"))['members']
    for user in usersJson:
        try:
            userTable[user['id']] = user['profile']['first_name']
        except:
            pass

buildUserTable()

producer = ProducerThread()
producer.daemon = True
producer.start()

consumer = ConsumerThread()
consumer.daemon = True
consumer.start()

while True:
    time.sleep(1)
