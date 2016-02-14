import time
from slackclient import SlackClient
import ledMatrix
import websocket

token = "XXX"      # found at https://api.slack.com/web#authentication
sc = SlackClient(token)

def connect_to_slack():
    if sc.rtm_connect():
        while True:
            try:
                message = sc.rtm_read()
                print message
                if message != [] and 'text' in message[0]:
                    text = message[0]['text']
                    print text
                    ledMatrix.sendMessageToMatrix(text)
                time.sleep(1)
            except websocket._exceptions.WebSocketConnectionClosedException:
                connect_to_slack()
    else:
        print "Connection Failed, invalid token?"
