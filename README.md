## Illuminate - Realtime LED Matrix Monitor
This project is based off of the Adafruit NextBus transit clock (found here: https://learn.adafruit.com/nextbus-transit-clock-for-raspberry-pi/overview). We have repurposed the hardware and code to show realtime slack updates and more!

![alt text](https://learn.adafruit.com/system/assets/assets/000/023/584/original/led_matrix_scroll-large.gif?1448316740)

## Hardware Set Up & Parts
1. You will need to buy and set up the following hardware list:
	* Raspberry Pi 2 or Raspberry Pi 3
	  *  We used a Raspberry pi 2 on a Raspbian distro
	  *  Will need to have network connectivity (wired or wireless)
	  *  Should be powered on its own power supply
	  *  Will need an SSH server set up
	* [Adafruit Matrix-HAT](https://www.adafruit.com/products/2345)
	  * We use this "HAT" to sit on top of the raspberry pi and interface with the LED Matrices seamlessly. This hardware makes life easy.
	  * The power supply below will connect to this to power the LEDs
	* [LED Matrix Panels](https://www.adafruit.com/products/1484) (We used two 32x32 6mm pitch LED Matrix Panels for this project.
	* [5V 10A Power Supply](https://www.adafruit.com/product/658) (This is going to be plugged into the Matrix-HAT. Should be enough power for up to 4 LED Matrices)
	* Slack admin access

2. I used the nextbus transit tutorial to set up and test the Matrix Panels and hardware. Please follow the tutorial here: [Adafruit NextBus Transit Clock Hardware Setup](https://learn.adafruit.com/nextbus-transit-clock-for-raspberry-pi/pi-setup)

3. Once you have the hardware set up and tested, we can move onto getting our software up and running.


## Software Installation

1. Clone this repo
2. Create your slack bot on the [slack admin panel](https://bnotions.slack.com/apps/new/A0F7YS25R-bots) and copy the API Token to your clipboard.
3. Add the API token to `SLACK_TOKEN` in the slack.py file
4. Run `sudo python slack.py` on the Raspberry Pi
5. Add your bot to any channels you want it listening on, and watch the LED matrix panels display the activity!
