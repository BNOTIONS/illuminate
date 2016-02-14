import time
from slackclient import SlackClient
import ledMatrix
import websocket
from threading import Thread
from Queue import Queue

token = "XXX"      # found at https://api.slack.com/web#authentication
sc = SlackClient(token)
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
                        text = message[0]['text']
                        queue.put(text)
                        print "Added to queue:", text
                    time.sleep(1)
            else:
                raise Exception

class ConsumerThread(Thread):
    def run(self):
        global queue
        while True:
           if not queue.empty():
                text = queue.get()
                ledMatrix.sendMessageToMatrix(text)
                queue.task_done()
                print "Queue Consumed:", text
                time.sleep(2)


producer = ProducerThread()
producer.daemon = True
producer.start()

consumer = ConsumerThread()
consumer.daemon = True
consumer.start()

while True:
    time.sleep(1)
