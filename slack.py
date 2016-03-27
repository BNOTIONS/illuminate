import time
from slackclient import SlackClient
import unicodedata
import websocket
from threading import Thread
from Queue import Queue
import grequests
import json
import illuminate
from illuminate import tile, runTileScroller

SLACK_TOKEN = "XXXXXX"      # found at https://api.slack.com/web#authentication
SLACK_CLIENT = SlackClient(SLACK_TOKEN)
userTable = {}
queue = Queue(100)
stock = "SY"
urls = ['http://finance.google.com/finance/info?client=ig&q={0}'.format(stock)]
stock_price = "Retrieving price..."

class SlackMessageProducerThread(Thread):
    def run(self):
        global queue
        while True:
            if SLACK_CLIENT.rtm_connect():
                while True:
                    raw_message = SLACK_CLIENT.rtm_read()
                    print raw_message
                    clean_message = parse_message(raw_message)
                    if 'text' in clean_message:
                        queue.put(clean_message)
                        print "Added to queue:", clean_message
                    time.sleep(1)
            else:
                raise Exception

class SlackConsumerThread(Thread):
    def run(self):
        global queue
        seconds_been_empty = 0
        while True:
            print ("SlackConsumerThread Iteration")
            if not queue.empty():
                tiles = []
                row_counter = 0
                while not queue.empty():
                    message = queue.get()
                    loadsbel_color = message.get('label_color', illuminate.WHITE)
                    highlight_color = message.get('highlight_color', illuminate.GREEN)
                    message_tile = tile(message['username'], message['text'], row=row_counter, label_color=label_color, highlight_color=highlight_color)
                    tiles.append(message_tile)
                    row_counter += 1
                    queue.task_done()
                    if row_counter == 3:
                        break
                runTileScroller(tiles)
                seconds_been_empty = 0
                print "Queue Consumed:", message
            else:
                # Screen saver :)
                seconds_been_empty += 1
                if seconds_been_empty > 3:
                    tile1 = tile("Slack", "#General", row=0, highlight_color=illuminate.WHITE, label_color=illuminate.BLUE)
                    tile2 = tile("#General", "#General", row=1, highlight_color=illuminate.YELLOW, label_color=illuminate.RED, column_spacing=100)
                    tile3 = tile("Hack this on", "Github", row=2, highlight_color=illuminate.WHITE, label_color=illuminate.GREEN, column_spacing=125)
                    tiles = [tile1, tile2, tile3]
                    runTileScroller(tiles)
                    seconds_been_empty = 0
            time.sleep(1)

class BottomRowThread(Thread):
    def run(self):
        global stock_price
        global stock
        while True:
            print ("BottomRowThread Iteration")
            active_users = get_active_users()
            active_user_list = ', '.join(active_users)
            active_user_tile = tile(str(len(active_users)), "active users on slack: " + active_user_list, row=3)
            spacing = active_user_tile.width + 100
            request = grequests.get(urls[0], callback=set_stock_string)
            grequests.send(request, grequests.Pool(1))
            stock_tile = tile(stock_price, stock, row=3, column_spacing=spacing)
            spacing += stock_tile.width + 100
            build_tile = tile(str(3), " Broken Builds", row=3, column_spacing=spacing, highlight_color=illuminate.RED)
            tiles = [active_user_tile, stock_tile, build_tile]
            runTileScroller(tiles)
            time.sleep(1)

def set_stock_string(response, **kwargs):
    global stock_price
    global stock
    cleaned_response = response.content.replace("\n", "").replace("//", "").replace(" ", "")
    clean_json = json.loads(cleaned_response)
    stock_price = clean_json[0]['l_cur']
    stock = clean_json[0]['t']
    return response

def parse_message(raw_message):
    clean_message = {}
    if raw_message != [] and 'user' in raw_message[0]:
        raw = raw_message[0]
        username = userTable[raw['user']]['name']
        clean_message['username'] = username
        if 'text' in raw:
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
    active_users = []
    for user in userTable:
        if 'presence' in userTable[user] and userTable[user]['presence'] == 'active' and not userTable[user]['is_bot']:
            active_users.append(userTable[user]['name'])
    print "Active users:", len(active_users)
    return active_users

def build_user_table():
    usersJson = json.loads(SLACK_CLIENT.api_call("users.list", presence=1))['members']
    for user in usersJson:
        userTable[user['id']] = user

build_user_table()

producer = SlackMessageProducerThread()
producer.daemon = True
producer.start()

consumer = SlackConsumerThread()
consumer.daemon = True
consumer.start()

bottomRow = BottomRowThread()
bottomRow.daemon = True
bottomRow.start()

while True:
    time.sleep(1)
