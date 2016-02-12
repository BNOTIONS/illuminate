import max7219.led as led
import max7219.font as font

device = led.matrix(cascaded=2)
device.orientation(270, redraw=True)

def sendMessageToMatrix(message):
    device.show_message(message, font=font.LCD_FONT)

sendMessageToMatrix("Server Booting...")