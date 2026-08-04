"""
DRAW_8B_C16 v 0.2.1

Draw library for color displays

Color: 16-bit
Interface: 8-bit

Project path: https://github.com/r2d2-arduino/tft_draw
MIT License

Author: Arthur Derkach 
"""
from micropython import const

class DRAW_8B_C16 ( ):
    
    BITS_PER_PIXEL = const( 16 )
    
    def __init__( self, width, height ):
        self.width  = width
        self.height = height
        
        self.buffer_multiply = 1
        self.font = None
       
    def swap_dimensions( self ):
        """ Swaps width and height for 90/270 degree rotation. """
        self.width, self.height = self.height, self.width       
        
    def set_buffer_multiply( self, multiply = 1 ):
        self.buffer_multiply = int(multiply)
    
    """
    *** Draw area ***
    """

    @micropython.viper
    def raw_pixel(self, x:int, y:int, color: int):
        """ Draw one pixel on display
        Args
        x (int): X position on dispaly, example 100
        y (int): Y position on dispaly, example 200
        color (int): RGB color
        """
        # Gpio preparation
        byte2gpio = ptr32(self.BYTE2GPIO)

        #coordinats
        x_hi  = byte2gpio[(x >> 8) & 0xFF]
        x_low = byte2gpio[x & 0xFF]
        y_hi  = byte2gpio[(y >> 8) & 0xFF]
        y_low = byte2gpio[y & 0xFF]

        #cs_bit = int(self.cs_bit)
        dc_bit = int(self.dc_bit)
        wr_bit = int(self.wr_bit)

        #Getting pointers to registers
        GPIO_OUT   = ptr32(self.GPIO_OUT_REG)  # 0 - 31  pins
        GPIO_OUT_S = ptr32(self.GPIO_OUT_SET) # + bit

        # Column address sending
        GPIO_OUT[0] = byte2gpio[0x2A] - dc_bit
        GPIO_OUT_S[0] = wr_bit

        # Sending Start and End X coordinates
        GPIO_OUT[0] = x_hi
        GPIO_OUT_S[0] = wr_bit
        GPIO_OUT[0] = x_low
        GPIO_OUT_S[0] = wr_bit

        GPIO_OUT[0] = x_hi
        GPIO_OUT_S[0] = wr_bit
        GPIO_OUT[0] = x_low
        GPIO_OUT_S[0] = wr_bit

        # Page address sending
        GPIO_OUT[0] = byte2gpio[0x2B] - dc_bit
        GPIO_OUT_S[0] = wr_bit

        # Sending Start and End Y coordinates
        GPIO_OUT[0] = y_hi
        GPIO_OUT_S[0] = wr_bit
        GPIO_OUT[0] = y_low
        GPIO_OUT_S[0] = wr_bit

        GPIO_OUT[0] = y_hi
        GPIO_OUT_S[0] = wr_bit
        GPIO_OUT[0] = y_low
        GPIO_OUT_S[0] = wr_bit

        # Memory write for addresses
        GPIO_OUT[0] = byte2gpio[0x2C] - dc_bit
        GPIO_OUT_S[0] = wr_bit

        # Sending Color data
        GPIO_OUT[0] = byte2gpio[(color >> 8) & 0xFF] # color hi
        GPIO_OUT_S[0] = wr_bit
        GPIO_OUT[0] = byte2gpio[color & 0xFF] # color low
        GPIO_OUT_S[0] = wr_bit

        #GPIO_OUT_S[0] = int(self.cs_bit) # CS = 1 - Device Off

    def draw_line(self, x0, y0, x1, y1, color):
        """ Draw line using Bresenham's Algorithm
        Args
        x0 (int): Start X position   s
        y0 (int): Start Y position    \
        x1 (int): End X position       \
        y1 (int): End Y position        e
        color (int): RGB color
        """
        self.update_byte2gpio()
        self.raw_line(x0, y0, x1, y1, color)
        self.cs.value(1)

    @micropython.viper
    def raw_line(self, x0:int, y0:int, x1:int, y1:int, color:int):
        """ Draw line using Bresenham's Algorithm
        Args
        x0 (int): Start X position   s
        y0 (int): Start Y position    \
        x1 (int): End X position       \
        y1 (int): End Y position        e
        color (int): RGB color
        """
        # Fastest way for vertical and horizontal lines
        if y0 == y1:
            w = x1 - x0 if x1 > x0 else x0 - x1
            sx = x0 if x0 < x1 else x1
            self.raw_fill_rect(sx, y0, w + 1, 1, color)
            return

        if x0 == x1:
            h = y1 - y0 if y1 > y0 else y0 - y1
            sy = y0 if y0 < y1 else y1
            self.raw_fill_rect(x0, sy, 1, h + 1, color)
            return

        # Calculating Bresenham's vars
        dx = x1 - x0 if x1 > x0 else x0 - x1
        dy = y1 - y0 if y1 > y0 else y0 - y1
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        # Preparing registers set
        byte2gpio = ptr32(self.BYTE2GPIO)
        dc_bit = int(self.dc_bit)
        wr_bit = int(self.wr_bit)
        #cs_bit = int(self.cs_bit)

        GPIO_OUT   = ptr32(self.GPIO_OUT_REG)
        GPIO_OUT_S = ptr32(self.GPIO_OUT_SET)

        # Preparing sending to display commands
        caset = byte2gpio[0x2A] - dc_bit
        paset = byte2gpio[0x2B] - dc_bit
        ramwr = byte2gpio[0x2C] - dc_bit

        # Converting colors to gpio sets
        color_hi = 0; color_low = 0
        gpio1 = 0; gpio2 = 0; gpio3 = 0
        color_r = 0; color_g = 0; color_b = 0

        color_hi  = byte2gpio[(color >> 8) & 0xFF]
        color_low = byte2gpio[color & 0xFF]

        # Main draw phase of line
        while True:
            # Pixel draw
            # Sending column (X)
            GPIO_OUT[0] = caset; GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = byte2gpio[(x0 >> 8) & 0xFF]; GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = byte2gpio[x0 & 0xFF];        GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = byte2gpio[(x0 >> 8) & 0xFF]; GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = byte2gpio[x0 & 0xFF];        GPIO_OUT_S[0] = wr_bit

            # Sending page (Y)
            GPIO_OUT[0] = paset; GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = byte2gpio[(y0 >> 8) & 0xFF]; GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = byte2gpio[y0 & 0xFF];        GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = byte2gpio[(y0 >> 8) & 0xFF]; GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = byte2gpio[y0 & 0xFF];        GPIO_OUT_S[0] = wr_bit

            # Write to memory command
            GPIO_OUT[0] = ramwr; GPIO_OUT_S[0] = wr_bit

            # Sending pixel data
            GPIO_OUT[0] = color_hi;  GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = color_low; GPIO_OUT_S[0] = wr_bit

            #GPIO_OUT_S[0] = cs_bit
            #self.cs.value(1)

            if x0 == x1 and y0 == y1:
                break

            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_vline(self, x, y, height, color, thickness = 1):
        """ Draw vertical line
        Args
        x (int): Start X position      xy
        y (int): Start Y position     h |
        height (int): Height of line    v
        color (int): RGB color
        thickness (int): thickness of line
        """
        self.fill_rect(x, y, thickness, height, color)

    def draw_hline(self, x, y, width, color, thickness = 1):
        """ Draw horizontal line
        Args
        x (int): Start X position          xy----->
        y (int): Start Y position              w
        width (int): Width of line
        color (int): RGB color
        thickness (int): thickness of line
        """
        self.fill_rect(x, y, width, thickness, color)

    def draw_rect(self, x, y, width, height, color, thickness = 1):
        """ Draw rectangle
        Args
        x (int): Start X position          xy----->
        y (int): Start Y position          |   w  .
        height (int): Height of line    h  |      .
        width (int): Width of square       v.......
        thickness (int): thickness of line
        color (int): RGB color
        """
        self.update_byte2gpio()
        self.raw_rect(x, y, width, height, color, thickness)
        self.cs.value(1)

    def raw_rect(self, x, y, width, height, color, thickness = 1):
        """ Draw rectangle
        Args
        x (int): Start X position          xy----->
        y (int): Start Y position          |   w  .
        height (int): Height of line    h  |      .
        width (int): Width of square       v.......
        thickness (int): thickness of line
        color (int): RGB color
        """
        self.raw_fill_rect(x, y, width, thickness, color)
        self.raw_fill_rect(x, y + height - thickness, width, thickness, color)
        self.raw_fill_rect(x, y, thickness, height, color)
        self.raw_fill_rect(x + width - thickness, y, thickness, height, color)


    def fill_rect(self, x, y, width, height, color):
        """ Draw filled rectangle
        Args
        x (int): Start X position          xy----->
        y (int): Start Y position          |   w  .
        width (int): Width of rectangle  h |      .
        height (int): Height of rectangle  v.
        color (int): RGB color
        """
        self.update_byte2gpio()
        self.raw_fill_rect(x, y, width, height, color)
        self.cs.value(1)

    @micropython.viper
    def raw_fill_rect(self, x:int, y:int, width:int, height:int, color:int):
        """ Draw filled rectangle
        Args
        x (int): Start X position          xy----->
        y (int): Start Y position          |   w  .
        width (int): Width of rectangle  h |      .
        height (int): Height of rectangle  v.
        color (int): RGB color
        """
        wr_bit = int(self.wr_bit)

        byte2gpio = ptr32(self.BYTE2GPIO)
        #Getting pointers to registers
        GPIO_OUT   = ptr32(self.GPIO_OUT_REG)  # 0 - 31  pins
        GPIO_OUT_S = ptr32(self.GPIO_OUT_SET) # + bit
        #self.cs.value(0) #?
        self.set_window(x, y, x + width - 1, y + height - 1) # Setting draw area

        amount = width * height # amount of pixels

        color_hi  = byte2gpio[(color >> 8) & 0xFF]
        color_low = byte2gpio[color & 0xFF]

        while amount:
            GPIO_OUT[0] = color_hi
            GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = color_low
            GPIO_OUT_S[0] = wr_bit

            amount -= 1
        

    def fill(self, color):
        """ Fill whole screen
        Args
        color (int): RGB color
        """
        self.fill_rect(0, 0, self.width, self.height, color)

    def fill_screen(self, color):
        """ Fill whole screen ( Old def support ) """
        self.fill( color )

    def draw_ellipse(self, x, y, radius_x, radius_y, color, border = 1):
        """ Draw ellipse or circle with mathematically perfect thick borders
        Args
        x, y (int): Center position
        radius_x, radius_y (int): Horizontal and vertical radius
        color (int): RGB color
        border (int): Thickness of the line
        """
        self.update_byte2gpio()
        self.raw_ellipse(x, y, radius_x, radius_y, color, border)
        self.cs.value(1)

    @micropython.viper
    def raw_ellipse(self, x:int, y:int, radius_x:int, radius_y:int, color:int, border:int = 1):
        """ Draw ellipse or circle with mathematically perfect thick borders
        Args
        x, y (int): Center position
        radius_x, radius_y (int): Horizontal and vertical radius
        color (int): RGB color
        border (int): Thickness of the line
        """
        if radius_x < 0 or radius_y < 0 or border < 1:
            return

        rx_in = radius_x - border
        ry_in = radius_y - border

        # If the thickness is greater than the radius, draw a solid shape.
        is_filled = (border >= radius_x) or (border >= radius_y)

        if rx_in < 0: rx_in = 0
        if ry_in < 0: ry_in = 0

        ry2 = radius_y * radius_y
        ry_in2 = ry_in * ry_in

        fillrect = self.raw_fill_rect
        # Scan the shape along the Y axis from the center (0) to the edge (radius_y)
        for y_pos in range(radius_y + 1):
            y2 = y_pos * y_pos

            # Calculating the boundary of an outer ellipse
            diff_out = ry2 - y2
            sq_out = diff_out
            if sq_out > 0:
                y_guess = (sq_out + 1) >> 1
                while y_guess < sq_out:
                    sq_out = y_guess
                    y_guess = (sq_out + diff_out // sq_out) >> 1
            # Formula X = a * sqrt(b^2 - y^2) / b
            x_out = (radius_x * sq_out + (radius_y >> 1)) // radius_y if radius_y > 0 else 0

            # Calculating the boundary of the inner ellipse (hole)
            x_in = 0
            if not is_filled and y_pos <= ry_in:
                diff_in = ry_in2 - y2
                sq_in = diff_in
                if sq_in > 0:
                    y_guess = (sq_in + 1) >> 1
                    while y_guess < sq_in:
                        sq_in = y_guess
                        y_guess = (sq_in + diff_in // sq_in) >> 1
                x_in = (rx_in * sq_in + (ry_in >> 1)) // ry_in

            # Drawing horizontal lines
            if is_filled or y_pos > ry_in:
                # Solid line
                w = x_out * 2 + 1
                if w > 0:
                    fillrect(x - x_out, y + y_pos, w, 1, color)
                    if y_pos > 0:
                        fillrect(x - x_out, y - y_pos, w, 1, color)
            else:
                # Double line
                w = x_out - x_in
                if w > 0:
                    # Right side
                    fillrect(x + x_in + 1, y + y_pos, w, 1, color)
                    # Left side
                    fillrect(x - x_out, y + y_pos, w, 1, color)
                    # Mirror reflection for the lower half of the ellipse
                    if y_pos > 0:
                        fillrect(x + x_in + 1, y - y_pos, w, 1, color)
                        fillrect(x - x_out, y - y_pos, w, 1, color)

    def draw_circle(self, x, y, radius, color, border = 1):
        """ Backwards compatible draw_circle """
        self.draw_ellipse(x, y, radius, radius, color, border)

    def raw_circle(self, x, y, radius, color, border = 1):
        """ Backwards compatible draw_circle """
        self.raw_ellipse(x, y, radius, radius, color, border)


    def fill_ellipse(self, x, y, radius_x, radius_y, color):
        """ Draw filled ellipse
        Args
        x (int): Center X position
        y (int): Center Y position
        radius_x (int): Horizontal radius
        radius_y (int): Vertical radius
        color (int): RGB color
        """
        self.update_byte2gpio()
        self.raw_fill_ellipse(x, y, radius_x, radius_y, color)
        self.cs.value(1)


    def raw_fill_ellipse(self, x, y, radius_x, radius_y, color):
        """ Draw filled ellipse
        Args
        x (int): Center X position
        y (int): Center Y position
        radius_x (int): Horizontal radius
        radius_y (int): Vertical radius
        color (int): RGB color
        """
        if radius_x <= 0 or radius_y <= 0:
            return

        radius_y_s2 = radius_y**2
        ratio = radius_x / radius_y # X-axis stretch factor

        fillrect = self.raw_fill_rect
        # Scanning along the Y axis from top to bottom
        for p in range(-radius_y, radius_y + 1):
            # Calculate the half-width of the horizontal line of an ellipse
            dx = int( ratio * (radius_y_s2 - p**2)**0.5 )
            if dx > 0:
                fillrect(x - dx, y + p, dx * 2, 1, color)

    def fill_circle(self, x, y, radius, color):
        """ Draw filled circle (Backwards compatible) """
        self.fill_ellipse(x, y, radius, radius, color)

    def raw_fill_circle(self, x, y, radius, color):
        """ Draw filled circle (Backwards compatible) """
        self.raw_fill_ellipse(x, y, radius, radius, color)


    """
    *** Image area ***
    """

    @micropython.viper
    def draw_raw_image(self, filename, x: int, y: int, width: int, height: int):
        """ Draw RAW image (RGB565 format) on display
        Args
        filename (string): filename of image, example: "rain.raw"
        x (int) : Start X position
        y (int) : Start Y position
        width (int) : Width of raw image
        height (int) : Height of raw image
        """
        with open( filename, 'rb' ) as f:
            
            wr_bit = int(self.wr_bit)
            self.update_byte2gpio()

            #Getting pointers to registers
            GPIO_OUT   = ptr32(self.GPIO_OUT_REG) # 0 - 31  pins
            GPIO_OUT_S = ptr32(self.GPIO_OUT_SET)
            byte2gpio  = ptr32(self.BYTE2GPIO) #pointer to byte2gpio converter

            self.set_window(x, y, x + width - 1, y + height - 1) # Set start position

            #byte_width = width * 2
            current_row = 0
            
            # Calculating bites in block
            rows_to_read = int(self.buffer_multiply)
            pixels_to_read = rows_to_read * width
            image_data = bytearray(rows_to_read * width * 2)
            image_buffer = ptr8(image_data) # get pointer to image row
            
            rows_rest = height % rows_to_read
            
            while current_row < height - rows_rest:
                # Reading image block
                f.readinto(image_data)

                for pos in range(pixels_to_read):
                    GPIO_OUT[0] = byte2gpio[ image_buffer[ pos * 2 ] ]
                    GPIO_OUT_S[0] = wr_bit
                    
                    GPIO_OUT[0] = byte2gpio[ image_buffer[ pos * 2 + 1 ] ]
                    GPIO_OUT_S[0] = wr_bit
                
                current_row += rows_to_read
            
            #calculating rest
            if rows_rest:
                rest_data = bytearray(rows_rest * width * 2)
                rest_buffer = ptr8(rest_data)
                f.readinto(rest_data)
                
                for rpos in range( rows_rest * width ):
                    GPIO_OUT[0] = byte2gpio[ rest_buffer[ rpos * 2 ] ]
                    GPIO_OUT_S[0] = wr_bit
                    
                    GPIO_OUT[0] = byte2gpio[ rest_buffer[ rpos * 2 + 1 ] ]
                    GPIO_OUT_S[0] = wr_bit
        
            self.cs.value(1) # Chip disabled

    def draw_bmp( self, filename, x = 0, y = 0 ):
        """ Draw BMP image on display
        Args
        filename (string): filename of image, example: "rain.bmp"
        x (int) : Start X position
        y (int) : Start Y position
        """
        f = open(filename, 'rb')

        if f.read(2) == b'BM':  #header
            dummy    = f.read(8) #file size(4), creator bytes(4)
            offset   = int.from_bytes(f.read(4), 'little')
            dummy    = f.read(4) #hdrsize
            width    = int.from_bytes(f.read(4), 'little')
            height   = int.from_bytes(f.read(4), 'little')
            planes   = int.from_bytes(f.read(2), 'little')
            depth    = int.from_bytes(f.read(2), 'little')
            compress = int.from_bytes(f.read(4), 'little')

            if planes == 1 and depth == 24 and compress == 0: #compress method == uncompressed
                rowsize = (width * 3 + 3) & ~3

                if height < 0:
                    height = -height

                frameWidth, frameHeight = width, height

                if x + frameWidth > self.width:
                    frameWidth = self.width - x

                if y + frameHeight > self.height:
                    frameHeight = self.height - y

                f.seek(offset)

                self.update_byte2gpio()
                self.set_window(x, y, x + frameWidth - 1, y + frameHeight - 1)
                self._send_bmp_to_display( f, frameHeight, frameWidth, offset, rowsize )

                self.cs.value(1)
        f.close()

    @micropython.viper
    def _send_bmp_to_display( self, f, frameHeight: int, frameWidth: int, offset: int, rowsize: int ):
        """ Send bmp-file to display by blocks
        Args
        f (object File) : Image file
        frameHeight (int): Height of image frame
        frameWidth (int): Width of image frame
        offset (int): Internal byte offset of image-file
        rowsize (int): Internal byte rowsize of image-file
        bufmulty (int): Number of rows to read in one block
        """
        wr_bit = int(self.wr_bit)

        GPIO_OUT   = ptr32(self.GPIO_OUT_REG)
        GPIO_OUT_S = ptr32(self.GPIO_OUT_SET)
        byte2gpio  = ptr32(self.BYTE2GPIO)

        # Calculating row size of block
        image_data = bytearray(rowsize)
        image_buffer = ptr8(image_data)
            
        for row in range( frameHeight ):
            # Start position of new row in image-file
            pos = offset + row * rowsize  
            if int(f.tell()) != pos:
                f.seek(pos)

            # Reading row block
            f.readinto(image_data)
            
            col = 0
            while col < frameWidth:
                # Pixel index in the image
                blue  = image_buffer[ col * 3 ]
                green = image_buffer[ col * 3 + 1 ]
                red   = image_buffer[ col * 3 + 2 ]

                # Sending new bit-masks directly to registers
                GPIO_OUT[0] = byte2gpio[ ( red & 0xF8 ) | ( green & 0xFC ) >> 5 ]
                GPIO_OUT_S[0] = wr_bit
                GPIO_OUT[0] = byte2gpio[ ( green & 0x1C ) << 3 | blue >> 3 ]
                GPIO_OUT_S[0] = wr_bit

                col += 1

    """
    *** Text area ***
    """

    def set_font(self, font):
        """ Set font for text
        Args
        font (module): Font module generated by font_to_py.py
        """
        self.font = font

    def draw_text(self, text, x, y, color):
        """ Draw text on display
        Args
        x (int) : Start X position
        y (int) : Start Y position
        color (int): RGB color

        Return (int, int): Last position of the carriage: X, Y
        """
        x_start = x
        screen_height = self.height
        screen_width = self.width

        font = self.font
        if font == None:
            print("Font not set")
            return False

        glyph_height = font.height()

        draw = self.raw_bitmap
        getch = font.get_ch
        
        i = 0
        self.update_byte2gpio()
        for char in text:
            if char == "\n": # New line
                x = x_start
                y += glyph_height
                i = i + 1
                continue

            if char == "\t": #replace tab to space
                char = " "

            glyph = getch(char)
            if not glyph:
                continue

            glyph_height = glyph[1]
            glyph_width = glyph[2]

            if char == " ": # double size for space
                x += glyph_width

            if x + glyph_width > screen_width:
                x = x_start
                y += glyph_height

            if y + glyph_height > screen_height: # End of screen
                break

            draw(glyph, x, y, color)
            x += glyph_width
            i = i + 1
        self.cs.value(1)
        return ( x, y, i )

    def draw_bitmap(self, bitmap, x:int, y:int, color:int):
        """ Draw transparent bitmap (char) on display """
        self.update_byte2gpio()
        self.raw_bitmap( bitmap, x, y, color )
        self.cs.value(1)

    @micropython.viper
    def raw_bitmap(self, bitmap, x:int, y:int, color:int):
        """ Draw transparent bitmap (char) on display (Optimized) """
        data   = ptr8(bitmap[0])
        height = int(bitmap[1])
        width  = int(bitmap[2])

        byte2gpio = ptr32(self.BYTE2GPIO)
        dc_bit = int(self.dc_bit)
        wr_bit = int(self.wr_bit)

        GPIO_OUT   = ptr32(self.GPIO_OUT_REG)
        GPIO_OUT_S = ptr32(self.GPIO_OUT_SET)

        # Preparind sending to dispaly commands
        caset = byte2gpio[0x2A] - dc_bit
        paset = byte2gpio[0x2B] - dc_bit
        ramwr = byte2gpio[0x2C] - dc_bit

        # Converting color to gpio data
        color_hi  = byte2gpio[(color >> 8) & 0xFF]
        color_low = byte2gpio[color & 0xFF]

        i = 0
        for h in range(height):
            ypos = h + y

            # Sending Y-coords (PASET). One time for one row
            GPIO_OUT[0] = paset
            GPIO_OUT_S[0] = wr_bit

            y_hi = byte2gpio[(ypos >> 8) & 0xFF]
            y_low = byte2gpio[ypos & 0xFF]

            GPIO_OUT[0] = y_hi
            GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = y_low
            GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = y_hi
            GPIO_OUT_S[0] = wr_bit
            GPIO_OUT[0] = y_low
            GPIO_OUT_S[0] = wr_bit

            bit_len = 0
            while bit_len < width:
                byte = data[i]
                i += 1

                if byte: # If byte is empty - skiping
                    dot = 0
                    while dot < 8 and bit_len + dot < width:
                        if byte & (0x80 >> dot): # (byte >> (7-dot)) & 1
                            px = x + bit_len + dot

                            # Sending X coords only (CASET)
                            GPIO_OUT[0] = caset
                            GPIO_OUT_S[0] = wr_bit

                            x_hi = byte2gpio[(px >> 8) & 0xFF]
                            x_low = byte2gpio[px & 0xFF]

                            GPIO_OUT[0] = x_hi
                            GPIO_OUT_S[0] = wr_bit
                            GPIO_OUT[0] = x_low
                            GPIO_OUT_S[0] = wr_bit
                            GPIO_OUT[0] = x_hi
                            GPIO_OUT_S[0] = wr_bit
                            GPIO_OUT[0] = x_low
                            GPIO_OUT_S[0] = wr_bit

                            # Command RAMWR (Write to memory)
                            GPIO_OUT[0] = ramwr
                            GPIO_OUT_S[0] = wr_bit

                            # Sending color
                            GPIO_OUT[0] = color_hi
                            GPIO_OUT_S[0] = wr_bit
                            GPIO_OUT[0] = color_low
                            GPIO_OUT_S[0] = wr_bit

                        dot += 1
                bit_len += 8

    def scroll_text(self, text, x, y, color, bg = 0x0000, delay = 10):
        """ Scroll text on display
        Args
        x (int) : Start X position
        y (int) : Start Y position
        color (int): RGB color
        bg (int) : Bacground, RGB color
        delay (int): Delay between new lines (ms)
        """
        if not text:
            return

        font = self.font
        if font == None:
            print("Font not set")
            return False

        screen_width = self.width
        screen_height = self.height

        self.vert_scroll(0, screen_height, 0)
        run_scrolling = False

        x_start = x

        #sample = font.get_ch("A")
        #glyph_height = sample[1] if sample else 8
        glyph_height = font.height()

        draw = self.raw_bitmap
        scrollrow = self._scroll_row
        self.update_byte2gpio()
        for char in text:
            if char == "\n": # New line
                x = screen_width
                continue

            if char == "\t": #replace tab to space
                char = " "

            glyph = font.get_ch(char)
            glyph_height = glyph[1]
            glyph_width = glyph[2]

            if char == " ": # double size for space
                x += glyph_width

            if x + glyph_width >= screen_width: # End of row
                x = x_start
                y += glyph_height

                if y + glyph_height > screen_height: # End of screen
                    run_scrolling = True
                    y = 0

                if run_scrolling:
                    scrollrow(y, glyph_height, screen_width, bg, delay)

            draw(glyph, x, y, color)
            x += glyph_width

        self.cs.value(1)

    def _scroll_row(self, y, glyph_height, screen_width, bg, delay):
        """ Scroll one row of text """
        for ys in range(glyph_height):
            self.vert_scroll_start_address(y + ys + 1) #scrolling up on glyph_height
            self.raw_fill_rect(0, y + ys, screen_width, 1, bg)
            sleep_ms(delay)
        
    @micropython.viper
    def rgb(self, red :int, green :int, blue :int)->int:
        """ Convert 8,8,8 bits RGB to 16/18/24 bits  """
        return ( ((red >> 3) << 11) & 0xF800 | ((green >> 2) << 5) & 0x07E0 | (blue >> 3) & 0x001F )


    def h2rgb( self, hexcolor ):
        """ Convert hex color to RGB #00FFAA -> 0x00, 0xFF, 0xAA """
        hex_str = hexcolor.lstrip('#')
        r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        self.rgb(r, g, b)