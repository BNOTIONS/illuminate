import max7219.led as led

device = led.matrix(cascaded=2)
device.orientation(270, redraw=True)

def sendMessageToMatrix(message):
    device.show_message(message)

import socket
ip = socket.gethostbyname(socket.gethostname())
sendMessageToMatrix(ip)