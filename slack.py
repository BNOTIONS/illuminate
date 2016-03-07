import time
from slackclient import SlackClient
# import ledMatrix
import unicodedata
import websocket
from threading import Thread
from Queue import Queue
import json

SLACK_TOKEN = "XXXXX"      # found at https://api.slack.com/web#authentication
SLACK_CLIENT = SlackClient(SLACK_TOKEN)
userTable = {}
queue = Queue(100)

class ProducerThread(Thread):
    def run(self):
        global queue
        while True:
            if SLACK_CLIENT.rtm_connect():
                while True:
                    raw_message = SLACK_CLIENT.rtm_read()
                    print raw_message
                    print "Active users:", get_active_users()
                    clean_message = parse_message(raw_message)
                    if clean_message:
                        queue.put(clean_message)
                        print "Added to queue:", clean_message
                    time.sleep(1)
            else:
                raise Exception

class ConsumerThread(Thread):
    def run(self):
        global queue
        while True:
           if not queue.empty():
                message = queue.get()
                # ledMatrix.sendMessageToMatrix(message)
                queue.task_done()
                print "Queue Consumed:", message
                time.sleep(2)

def parse_message(raw_message):
    clean_message = None
    if raw_message != [] and 'user' in raw_message[0]:
        raw = raw_message[0]
        username = userTable[raw['user']]['name']
        if 'text' in raw:
            # Show real messages code below:
            # text = raw['text']
            # text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
            # clean_message = '{0} says {1}'.format(user, text)
            clean_message = '{0} sent a message'.format(username)
        elif 'presence' in raw:
            presence = raw['presence']
            userTable[raw['user']]['presence'] = presence # Update user table's presence
            clean_message = '{0} became {1}'.format(username, presence)
        elif 'type' in raw and raw['type'] == 'user_typing':
            clean_message = '{0} is typing'.format(username)
    return clean_message

def get_active_users():
    active_users = 0
    for user in userTable:
        if 'presence' in userTable[user] and userTable[user]['presence'] == 'active':
            active_users += 1
    return active_users

def build_user_table():
    usersJson = json.loads(SLACK_CLIENT.api_call("users.list", presence=1))['members']
    for user in usersJson:
        userTable[user['id']] = user

build_user_table()

producer = ProducerThread()
producer.daemon = True
producer.start()

consumer = ConsumerThread()
consumer.daemon = True
consumer.start()

while True:
    time.sleep(1)
