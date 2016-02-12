from flask import Flask, redirect
app = Flask(__name__)

import simplejson as json
from flask import render_template
from flask import request
import ledMatrix

@app.route('/lcd/<message_string>')
def lcdMessage(message_string):
    ledMatrix.sendMessageToMatrix(message_string)
    return True

if __name__ == '__main__':
    app.debug = True
    app.run()