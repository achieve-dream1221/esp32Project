from my_ssd1306 import MySSD1306_I2C

screen = MySSD1306_I2C()

screen.text_zh("吴凤琳是猪", 0, 0, False)
screen.show()
