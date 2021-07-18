from my_ssd1306 import MySSD1306_I2C
from utime import sleep
import gc
import network

wlan = network.WLAN(network.STA_IF)
screen = MySSD1306_I2C()


def connect_wifi():
    screen.print("正在打开wifi...")
    wlan.active(True)
    screen.print("wifi已打开")
    screen.print("正在连接hello_world...")
    while not wlan.isconnected():
        wlan.connect("hello_world", '12345678')
        sleep(3)
    screen.print("连接成功")
    screen.print('IP:' + str(wlan.ifconfig()[0]))
    gc.collect()


if __name__ == '__main__':
    connect_wifi()
