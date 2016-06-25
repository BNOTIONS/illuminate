import time
from slackclient import SlackClient
import unicodedata
import websocket
from threading import Thread
from Queue import Queue
import grequests
import json
import socket
import websocket
import illuminate
from illuminate import tile, runTileScroller

SLACK_TOKEN = "XXXXXX"      # found at https://api.slack.com/web#authentication
SLACK_CLIENT = SlackClient(SLACK_TOKEN)
JENKINS_BASE_URL = "https://XXX.com"
JENKINS_HEADERS = {}
JENKINS_HEADERS['Authorization'] = "Basic XXXX"
userTable = {}
queue = Queue(100)
stock = "SY"
stock_url = 'http://finance.google.com/finance/info?client=ig&q={0}'.format(stock)
stock_price = "Retrieving price..."
broken_build_count = 0
pr_count = '0'

class SlackMessageProducerThread(Thread):
    def run(self):
        global queue
        while True:
            if SLACK_CLIENT.rtm_connect():
                while True:
                    try:
                        raw_message = SLACK_CLIENT.rtm_read()
                        print raw_message
                        clean_message = parse_message(raw_message)
                        if 'text' in clean_message:
                            queue.put(clean_message)
                            print "Added to queue:", clean_message
                    except socket.error as e:
                        print "Socket error: {0}".format(e.message)
                        break
                    except websocket.WebSocketConnectionClosedException as e:
                        print "WebSocket error: {0}".format(e.message)
                        break
                    time.sleep(1)
            else:
                time.sleep(1)


class SlackConsumerThread(Thread):
    # This thread handles the first three rows of text on the LED Matrix
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
                    label_color = message.get('label_color', illuminate.WHITE)
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
        global broken_build_count
        global pr_count
        while True:
            print ("BottomRowThread Iteration")
            active_users = get_active_users()
            active_user_list = ', '.join(active_users)
            active_user_tile = tile(str(len(active_users)), "active users on slack: " + active_user_list, row=3)
            spacing = active_user_tile.width + 100
            make_async_requests()
            stock_tile = tile(stock_price, stock, row=3, column_spacing=spacing)
            spacing += stock_tile.width + 100
            build_tile = tile(str(broken_build_count), " Broken Builds", row=3, column_spacing=spacing, highlight_color=illuminate.RED)
            spacing += build_tile.width + 100
            pr_tile = tile(str(pr_count), " Pull Requests Merged", row=3, column_spacing=spacing, highlight_color=illuminate.BLUE)
            tiles = [active_user_tile, stock_tile, build_tile, pr_tile]
            runTileScroller(tiles)
            time.sleep(1)

def set_build_counter(response, **kwargs):
    global broken_build_count
    builds = response.json()['jobs']
    counter = {}
    for build in builds:
        if 'color' in build and counter.get(build['color'], None):
            counter[build['color']] = counter[build['color']] + 1 
        else:
            counter[build['color']] = 1
    broken_build_count = counter['red']
    print "Build update:{0}".format(broken_build_count)
    return response

def set_pr_counter(response, **kwargs):
    global pr_count
    pr_count = response.content
    print "{0} PRS".format(pr_count)
    return response

def make_async_requests():
    stock_request = grequests.get(stock_url, callback=set_stock_string)
    grequests.send(stock_request, grequests.Pool(1))    
    jenkins_url = "{0}/api/json?tree=jobs[name,color]".format(JENKINS_BASE_URL)
    jenkins_request = grequests.get(jenkins_url, headers=JENKINS_HEADERS, callback=set_build_counter)
    grequests.send(jenkins_request, grequests.Pool(1))
    # github_url = "http://utils.bnotions.com/bnotions/pulls?state=closed"
    # github_request = grequests.get(github_url, callback=set_pr_counter)
    # grequests.send(github_request, grequests.Pool(1))

def set_stock_string(response, **kwargs):
    global stock_price
    global stock
    cleaned_response = response.content.replace("\n", "").replace("//", "").replace(" ", "")
    clean_json = json.loads(cleaned_response)
    stock_price = clean_json[0]['l_cur']
    stock = clean_json[0]['t']
    print "Stock update:{0}".format(stock_price)
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
    usersJson = SLACK_CLIENT.api_call("users.list", presence=1)['members']
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
