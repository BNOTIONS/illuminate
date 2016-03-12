import time
from slackclient import SlackClient
import unicodedata
import websocket
from threading import Thread
from Queue import Queue
import json
import illuminate
from illuminate import tile, runTileScroller

SLACK_TOKEN = "XXXXXX"      # found at https://api.slack.com/web#authentication
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
                    get_active_users()
                    clean_message = parse_message(raw_message)
                    if 'text' in clean_message:
                        queue.put(clean_message)
                        print "Added to queue:", clean_message
                    time.sleep(1)
            else:
                raise Exception

class ConsumerThread(Thread):
    def run(self):
        global queue
        while True:
            print ("run consumer")
            if not queue.empty():
                tiles = []
                row_counter = 0
                while not queue.empty():
                    message = queue.get()
                    label_color = message.get('label_color', illuminate.WHITE)
                    highlight_color = message.get('highlight_color', illuminate.GREEN)
                    message_tile = tile(message['username'], message['text'], row=row_counter, label_color=label_color, highlight_color=highlight_color)
                    tiles.append(message_tile)
                    row_counter += 1
                    queue.task_done()
                    if row_counter == 3:
                        break
                runTileScroller(tiles)
                print "Queue Consumed:", message
            time.sleep(1)

class BottomRowThread(Thread):
    def run(self):
        while True:
            print ("run bottom")
            tiles = []
            active_user_tile = tile(str(get_active_users()), "active users on slack", row=3)
            tilehell = tile(str(0.25), " SY TSX:V", row=3, column_spacing=200)
            tiles.append(active_user_tile)
            tiles.append(tilehell)
            runTileScroller(tiles)
            time.sleep(1)

def parse_message(raw_message):
    clean_message = {}
    if raw_message != [] and 'user' in raw_message[0]:
        raw = raw_message[0]
        username = userTable[raw['user']]['name']
        clean_message['username'] = username
        if 'text' in raw:
            # Show real messages code below:
            text = raw['text']
            clean_message['text'] = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
            # clean_message = '{0} sent a message'.format(username)
        elif 'presence' in raw:
            presence = raw['presence']
            userTable[raw['user']]['presence'] = presence # Update user table's presence
            clean_message['text'] = 'became {0}'.format(presence)
            clean_message['label_color'] = illuminate.RED
        elif 'type' in raw and raw['type'] == 'user_typing':
            clean_message['text'] = 'is typing'
            clean_message['label_color'] = illuminate.YELLOW
    return clean_message

def get_active_users():
    active_users = 0
    for user in userTable:
        if 'presence' in userTable[user] and userTable[user]['presence'] == 'active' and not userTable[user]['is_bot']:
            active_users += 1
    print "Active users:", active_users
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

bottomRow = BottomRowThread()
bottomRow.daemon = True
bottomRow.start()

while True:
    time.sleep(1)
