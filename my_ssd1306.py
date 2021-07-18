import gc
from micropython import const
from machine import SoftI2C, Pin
import framebuf
from font import fonts

SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xa4)
SET_NORM_INV = const(0xa6)
SET_DISP = const(0xae)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xa0)
SET_MUX_RATIO = const(0xa8)
SET_COM_OUT_DIR = const(0xc0)
SET_DISP_OFFSET = const(0xd3)
SET_COM_PIN_CFG = const(0xda)
SET_DISP_CLK_DIV = const(0xd5)
SET_PRECHARGE = const(0xd9)
SET_VCOM_DESEL = const(0xdb)
SET_CHARGE_PUMP = const(0x8d)


class SSD1306:
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
                SET_DISP | 0x00,
                SET_MEM_ADDR, 0x00,
                SET_DISP_START_LINE | 0x00,
                SET_SEG_REMAP | 0x01,
                SET_MUX_RATIO, self.height - 1,
                SET_COM_OUT_DIR | 0x08,
                SET_DISP_OFFSET, 0x00,
                SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
                SET_DISP_CLK_DIV, 0x80,
                SET_PRECHARGE, 0x22 if self.external_vcc else 0xf1,
                SET_VCOM_DESEL, 0x30,
                SET_CONTRAST, 0xff,
                SET_ENTIRE_ON,
                SET_NORM_INV,
                SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
                SET_DISP | 0x01):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

    def fill(self, col):
        self.framebuf.fill(col)

    def pixel(self, x, y, col):
        self.framebuf.pixel(x, y, col)

    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def show_text(self, string, x, y, col=1):
        self.framebuf.text(string, x, y, col)
        self.show()

    def hline(self, x, y, w, col):
        self.framebuf.hline(x, y, w, col)

    def vline(self, x, y, h, col):
        self.framebuf.vline(x, y, h, col)

    def line(self, x1, y1, x2, y2, col):
        self.framebuf.line(x1, y1, x2, y2, col)

    def rect(self, x, y, w, h, col):
        self.framebuf.rect(x, y, w, h, col)

    def fill_rect(self, x, y, w, h, col):
        self.framebuf.fill_rect(x, y, w, h, col)

    def blit(self, fbuf, x, y):
        self.framebuf.blit(fbuf, x, y)


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3c, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.temp[0] = self.addr << 1
        self.temp[1] = 0x40
        self.i2c.start()
        self.i2c.write(self.temp)
        self.i2c.write(buf)
        self.i2c.stop()

    # 阴码, 行列式, 等比字体
    def show_text_zh(self, text: str, x: int, y: int, isVertical: bool, size=12):
        x *= size
        y *= size
        row_max_cout_zh = self.width // size
        col_max_cout_zh = self.height // size
        cout_row, cout_col = 0, 0
        for k in text:
            if cout_row >= row_max_cout_zh:
                y += size
                x = 0
                cout_row = 0
            if cout_col >= col_max_cout_zh:
                x += size
                y = 0
                cout_col = 0
            byte_datas = fonts[k]
            y_2 = y
            for i in range(size):
                all_ch = '{:08b}'.format(byte_datas[0][i]) + '{:08b}'.format(byte_datas[1][i])
                x_2 = x
                for j in range(16):
                    if x_2 <= self.width and y_2 <= self.height:
                        self.pixel(x_2, y_2, int(all_ch[j]))
                        x_2 += 1
                    else:
                        break
                y_2 += 1
            if isVertical:
                y += size
                cout_col += 1
            else:
                x += size
                cout_row += 1
        self.show()
        gc.collect()


def MySSD1306_I2C():
    return SSD1306_I2C(128, 64, SoftI2C(scl=Pin(22), sda=Pin(21)))
