# tft_draw
A set of graphic libraries for TFT and LCD displays in micropython

## File Structure:
* **draw_fb_mono.py** - A framebuffer-based, advanced SPI library for monochrome color.
* **draw_fb_g4.py** - A framebuffer-based, extended SPI library for 4-bit grayscale.
* **draw_fb_g8.py** - A framebuffer-based, extended SPI library for 8-bit color.
* **draw_fb_с16.py** - A framebuffer-based, extended SPI library for 16-bit color.
* **draw_fb_с18.py** - A framebuffer-based, extended SPI library for 18/24-bit color.
* **draw_spi_c16.py** - A direct draw, extended SPI library for 16-bit color.
* **draw_spi_c18.py** - A direct draw, extended SPI library for 18/24-bit color.

## Tools
* **tools/ font_to_py.py** - Used to convert ttf font to py script. First of all, you need to install: `pip install freetype-py`. Then run a command similar to the example:
`python font_to_py.py -x LibreBodoni-Bold.ttf 24 LibreBodoni24.py`. More details: https://github.com/peterhinch/micropython-font-to-py
* **tools/ img2rgb565.py** - Used to convert BMP-image to RAW RGB565 format. Usage: `python img2rgb565.py <your_image>`. Raw images load faster and use less memory.


# Description of functions
## Base functions:
* **swap_dimensions( )** - Swaps width and height for 90/270 degree rotation.

## Draw functions (Direct draw libaries only):
* **set_window( x0, y0, x1, y1 ):** Sets the starting position and the area of drawing on the display.
* **fill( color ):** Fill whole screen.
* **draw_pixel( x, y, color ):** Draw one pixel on display.
* **draw_line( x0, y0, x1, y1, color ):** Draw line using Bresenham's Algorithm.
* **draw_vline( x, y, height, color, thickness = 1 ):** Draw vertical line.
* **draw_hline( x, y, width, color, thickness = 1 ):** Draw horizontal line.
* **draw_rect( x, y, width, height, color, thickness = 1 ):** Draw rectangle.
* **fill_rect( x, y, width, height, color ):** Draw filled rectangle.
* **draw_circle( x, y, radius, color, border = 1 ):** Draw circle.
* **fill_circle( x, y, radius, color ):** Draw filled circle.
* **draw_arc( x, y, radius, start_angle, end_angle, color ):** Draw arc. Used in some libraries.
* **fill_arc( x, y, radius, start_angle, end_angle, thickness, color ):** Fill arc. Used in some libraries.

## Image functions:
* **draw_bmp( filename, x = 0, y = 0 ):** Draw BMP image on display.
* **draw_raw_image( filename, x, y, width, height ):** Draw RAW image (RGB565 format) on display.
* **rgb( red, green, blue ):** Convert 8,8,8 bits RGB to 16/18/24 bits (depends on the library).
* **load_mono( filename, x = 0, y = 0, color = 1 ):** - Load monochromatic BMP image on buffer. Used in some libraries.
* **load_bmp( filename, x = 0, y = 0 ):** - Load and convert 16-color BMP image on buffer. Used in some libraries.

## Text functions:
* **set_font( font ):** Set font for text. Converted font is used. See *tools/ font_to_py.py*.
* **set_text_wrap( on = True ):** - Set text wrapping. Used in some libraries.
* **draw_text( text, x, y, color ):** Draw text on display.
* **draw_bitmap( bitmap, x, y, color ):** Draw one bitmap (char) on display.

# Code examples
## How to use framebuffer-based libraries:
```python
from tft_draw.draw_fb_c16 import DRAW_FB_C16

class ST7789_SPI_FB( DRAW_FB_C16 ):
    
    def __init__( self, spi, cs_pin, dc_pin, rst_pin, width, height ):   
        #...        
        super().__init__( self.width, self.height )
        

#...
        
from machine import SPI

# Example of pin set
spi = SPI( 1, baudrate=20_000_000 )
tft = ST7789_SPI_FB( spi, cs_pin = 3, dc_pin = 5, rst_pin = 7, height = 320, width = 240 )

COLOR_RED = tft.rgb( 255, 0, 0 )
tft.fill( COLOR_RED )
tft.show()
```

## How to use direct draw libraries:
```python
from tft_draw.draw_spi_c16 import DRAW_SPI_C16

class ST7789_SPI ( DRAW_SPI_C16 ):
    def __init__( self, spi, cs_pin, dc_pin, rst_pin, width, height, offset_x = 0, offset_y = 0 ):
        self.cs  = Pin(cs_pin,  Pin.OUT, value = 1)
        self.dc  = Pin(dc_pin,  Pin.OUT, value = 0) 
        self.rst = Pin(rst_pin, Pin.OUT, value = 1)
        #...
        super().__init__( spi, self.cs, self.dc, width, height, offset_x, offset_y )

#...
from machine import SPI

# Example of pin set
spi = SPI( 1, baudrate=10_000_000, polarity = 1, phase = 1 )
tft = ST7789_SPI( spi, cs_pin = 1, dc_pin = 2, rst_pin = 4, height = 320, width = 170 )

COLOR_RED = tft.rgb( 255, 0, 0 )
tft.fill( COLOR_RED )
```
