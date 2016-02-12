import time
from slackclient import SlackClient
import ledMatrix.sendMessageToMatrix

token = "XXX"      # found at https://api.slack.com/web#authentication
sc = SlackClient(token)

if sc.rtm_connect():
    while True:
        message = sc.rtm_read()
        print message
        if message != [] and 'text' in message[0]:
            text = message[0]['text']
            print text
            sendMessageToMatrix(text)
        time.sleep(1)
else:
    print "Connection Failed, invalid token?"
