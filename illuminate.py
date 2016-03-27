import atexit
from PIL import Image, ImageDraw, ImageFont
import math
import os
import time
from rgbmatrix import Adafruit_RGBmatrix

# Configurable stuff ---------------------------------------------------------
width          = 64  # Matrix size (pixels) -- change for different matrix
height         = 32  # types (incl. tiling).  Other code may need tweaks.
matrix         = Adafruit_RGBmatrix(32, 2) # rows, chain length
fps            = 22  # Scrolling speed (ish)

WHITE     = (255, 255, 255) # Color for route labels (usu. numbers)
descColor      = (110, 110, 110) # " for route direction/description
GREEN  = (  0, 255,   0)
YELLOW   = (255, 255,   0)
RED = (255,   0,   0)
minsColor      = (110, 110, 110) # Commans and 'minutes' labels
BLUE   = (  0,   0, 255)

# TrueType fonts are a bit too much for the Pi to handle -- slow updates and
# it's hard to get them looking good at small sizes.  A small bitmap version
# of Helvetica Regular taken from X11R6 standard distribution works well:
font           = ImageFont.load(os.path.dirname(os.path.realpath(__file__))
                   + '/helvR08.pil')
fontYoffset    = -2  # Scoot up a couple lines so descenders aren't cropped


# Main application -----------------------------------------------------------

# Drawing takes place in offscreen buffer to prevent flicker
image       = Image.new('RGB', (width, height))
draw        = ImageDraw.Draw(image)

# Clear matrix on exit.  Otherwise it's annoying if you need to break and
# fiddle with some code while LEDs are blinding you.
def clearOnExit():
    matrix.Clear()

atexit.register(clearOnExit)

class tile:
    def __init__(self, highlight, label, row=0, column_spacing=0, highlight_color=GREEN, label_color=WHITE):
        self.x = width + column_spacing
        self.y = row * 8
        self.highlight = highlight
        self.highlight_color = highlight_color
        self.label_color = label_color
        self.label = label
        self.width = font.getsize(highlight + label)[0]+8

    def draw(self):
        draw.rectangle((0, self.y, width, self.y + 8), fill=(0, 0, 0)) # Clear background
        highlight_text = self.highlight
        draw.text((self.x, self.y + fontYoffset), highlight_text, font=font, fill=self.highlight_color)
        label_x = self.x + font.getsize(highlight_text)[0] + 2
        label_text = self.label
        draw.text((label_x, self.y + fontYoffset), label_text, font=font, fill=self.label_color)

def runTileScroller(tileList):
    tilesAcross = len(tileList)
    currentTime = 0.0
    prevTime    = 0.0
    while True:
        # draw.rectangle((0, 0, width, height), fill=(0, 0, 0)) # Clear background
        for t in tileList:
            if t.x < width:        # Draw tile if onscreen
                t.draw()
            t.x -= 1               # Move left 1 pixel
            if(t.x <= -t.width): # Off left edge?
                # t.x += t.width * tilesAcross     # Move off right &
                tileList.remove(t)
        if len(tileList) == 0:
            return True
        # Try to keep timing uniform-ish; rather than sleeping a fixed time,
        # interval since last frame is calculated, the gap time between this
        # and desired frames/sec determines sleep time...occasionally if busy
        # (e.g. polling server) there'll be no sleep at all.
        currentTime = time.time()
        timeDelta   = (1.0 / fps) - (currentTime - prevTime)
        if(timeDelta > 0.0):
            time.sleep(timeDelta)
        prevTime = currentTime

        # Offscreen buffer is copied to screen
        matrix.SetImage(image.im.id, 0, 0)
