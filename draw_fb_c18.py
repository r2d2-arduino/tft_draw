"""
DRAW_FB_C18 v 0.1.6
Draw library for color displays

Color: 18-bit, 24-bit
 
Project path: https://github.com/r2d2-arduino/tft_draw
MIT License

Author: Arthur Derkach 
"""
from micropython import const

class DRAW_FB_C18:
    
    BITS_PER_PIXEL = const( 18 )    
    BITCLIP = const(0xFC) # 0xFC - for 18-bit, 0xFF - for 24-bit
    
    def __init__( self, width, height ):
        self.width  = width
        self.height = height
        
        self.buffsize = width * height * 3
        self.buffer = bytearray( self.buffsize )

        self.font  = None
        self.pixel_format = 18
        self.bpp = 3
        
    def swap_dimensions(self):
        """ Swaps width and height for 90/270 degree rotation. """
        self.width, self.height = self.height, self.width
        
    # *** DRAW AREA ***
    @micropython.viper
    def fill_rect(self, x:int, y:int, width:int, height:int, color:int):
        """ Draw filled rectangle
        Args
        x (int): Start X position          xy----->
        y (int): Start Y position          |   w  .
        width (int): Width of rectangle  h |      .
        height (int): Height of rectangle  v.......
        color (int): RGB color
        """
        buffer = ptr8(self.buffer)
        frame_width = int(self.width)
        
        r   = color & BITCLIP
        g = (color >> 8) & BITCLIP
        b  = (color >> 16) & BITCLIP

        frame_bytes = frame_width * 3
        width_bytes = width * 3

        start = (y * frame_width + x) * 3

        for row in range(height):            
            i = start + row * frame_bytes
            end = i + width_bytes
            while i < end:
                buffer[ i     ] = r
                buffer[ i + 1 ] = g
                buffer[ i + 2 ] = b
                i += 3
                
    @micropython.viper
    def fill( self, color:int ):
        """ Fill whole screen
        Args
        color (int): RGB color
        """
        buffer = ptr32( self.buffer )
        total_blocks = int( self.width ) * int( self.height ) * 3 // 4
        
        r = color & BITCLIP
        g = (color >> 8) & BITCLIP
        b = (color >> 16) & BITCLIP

        # Собираем 3 байта в 32-битное значение (чтобы можно было писать по 4 байта за раз)
        pattern0 = (r << 24) | (b << 16) | (g << 8) | r
        pattern1 = (g << 24) | (r << 16) | (b << 8) | g
        pattern2 = (b << 24) | (g << 16) | (r << 8) | b
        
        # Основной цикл: заполняем блоками по 4 байта
        for i in range( 0, total_blocks, 3 ):
            buffer[ i     ] = pattern0
            buffer[ i + 1 ] = pattern1
            buffer[ i + 2 ] = pattern2
    
    def draw_vline( self, x, y, height, color, thickness = 1 ):
        """ Draw vertical line
        Args
        x (int): Start X position      xy
        y (int): Start Y position     h |   
        height (int): Height of line    v   
        color (int): RGB color
        thickness (int): thickness of line
        """        
        self.fill_rect(x, y, thickness, height, color)

    def draw_hline( self, x, y, width, color, thickness = 1 ):
        """ Draw horizontal line 
        Args
        x (int): Start X position          xy----->
        y (int): Start Y position              w
        width (int): Width of line            
        color (int): RGB color
        thickness (int): thickness of line
        """         
        self.fill_rect(x, y, width, thickness, color)
    
    def draw_rect( self, x, y, width, height, color, thickness = 1 ):
        """ Draw rectangle 
        Args  
        x (int): Start X position          xy----->
        y (int): Start Y position          |   w  .
        height (int): Height of line    h  |      .
        width (int): Width of square       v.......  
        thickness (int): thickness of line   
        color (int): RGB color
        """ 
        self.fill_rect(x, y, width, thickness, color)                     
        self.fill_rect(x, y + height - thickness, width, thickness, color) 
        self.fill_rect(x, y, thickness, height, color)                     
        self.fill_rect(x + width - thickness, y, thickness, height, color) 
            
    @micropython.viper
    def draw_line( self, x0:int, y0:int, x1:int, y1:int, color:int ):
        """ Draw line using Bresenham's Algorithm
        Args
        x0 (int): Start X position   s
        y0 (int): Start Y position    \
        x1 (int): End X position       \ 
        y1 (int): End Y position        e
        color (int): RGB color
        """

        buffer = ptr8( self.buffer )
        frame_width = int( self.width )
        #h = int( self.height )

        # Преобразуем 24-битный цвет → RGB666 (6 бит на канал)
        r = color & BITCLIP
        g = (color >> 8) & BITCLIP
        b = (color >> 16) & BITCLIP

        # Разности и направления
        dx = int( abs( x1 - x0 ) )
        dy = int( abs( y1 - y0 ) )
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        # Основной цикл
        while True:
            # Индекс пикселя в буфере
            index = (y0 * frame_width + x0) * 3
            buffer[ index     ] = r
            buffer[ index + 1 ] = g
            buffer[ index + 2 ] = b

            # Проверяем конец линии
            if x0 == x1 and y0 == y1:
                break

            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    @micropython.viper
    def draw_circle( self, x:int, y:int, radius:int, color:int, border:int=1 ):
        """ Draw circle
        Args
        x (int): Start X position          
        y (int): Start Y position              
        radius (int): Radius of circle         
        border (int): border of circle   
        color (int): RGB color
        """
        buffer   = ptr8(self.buffer)
        width    = int(self.width)
        height   = int(self.height)

        r = color & BITCLIP
        g = (color >> 8) & BITCLIP
        b = (color >> 16) & BITCLIP

        # Для ускорения — локальные переменные
        x0 = int(x)
        y0 = int(y)

        # Внутренний и внешний радиус (для толщины)
        r_outer = radius
        r_inner = radius - border if border > 0 else radius - 1
        if r_inner < 0:
            r_inner = 0

        # Предвычисляем квадраты радиусов (чтобы не использовать sqrt)
        r2_outer = r_outer * r_outer
        r2_inner = r_inner * r_inner

        # Область перебора (ограничиваем прямоугольником)
        x_min = x0 - r_outer
        y_min = y0 - r_outer
        x_max = x0 + r_outer
        y_max = y0 + r_outer

        # Клэмпим границы, чтобы не выйти за экран
        if x_min < 0: x_min = 0
        if y_min < 0: y_min = 0
        if x_max >= width:  x_max = width - 1
        if y_max >= height: y_max = height - 1

        for yy in range(y_min, y_max + 1):
            dy = yy - y0
            dy2 = dy * dy
            for xx in range(x_min, x_max + 1):
                dx = xx - x0
                d2 = dx * dx + dy2
                if r2_inner <= d2 <= r2_outer:
                    idx = (yy * width + xx) * 3
                    buffer[ idx     ] = r
                    buffer[ idx + 1 ] = g
                    buffer[ idx + 2 ] = b

    
    @micropython.viper
    def fill_circle(self, x:int, y:int, radius:int, color:int):
        """ Draw filled circle
        Args
        x (int): Start X position          
        y (int): Start Y position              
        radius (int): Radius of circle
        color (int): RGB color
        """
        buffer = ptr8(self.buffer)
        width  = int(self.width)
        height = int(self.height)

        r = color & BITCLIP
        g = (color >> 8) & BITCLIP
        b = (color >> 16) & BITCLIP

        x0 = int(x)
        y0 = int(y)
        r2 = radius * radius

        # Область перебора ограничиваем квадратом
        x_min = x0 - radius
        y_min = y0 - radius
        x_max = x0 + radius
        y_max = y0 + radius

        # Ограничиваем границы по экрану
        if x_min < 0: x_min = 0
        if y_min < 0: y_min = 0
        if x_max >= width:  x_max = width - 1
        if y_max >= height: y_max = height - 1

        for yy in range(y_min, y_max + 1):
            dy = yy - y0
            dy2 = dy * dy
            for xx in range(x_min, x_max + 1):
                dx = xx - x0
                if dx * dx + dy2 <= r2:
                    idx = (yy * width + xx) * 3
                    buffer[ idx     ] = r
                    buffer[ idx + 1 ] = g
                    buffer[ idx + 2 ] = b

        
    @micropython.viper
    def pixel( self, x:int, y:int, color:int ):
        """ Draw one pixel on display
        Args
        x (int): X position on dispaly, example 100
        y (int): Y position on dispaly, example 200
        color (int): RGB color
        """        
        buffer = ptr8(self.buffer)
        width  = int(self.width)
        height = int(self.height)

        if 0 <= x < width and 0 <= y < height:
            idx = (y * width + x) * 3

            buffer[ idx     ] = color & BITCLIP
            buffer[ idx + 1 ] = (color >> 8)  & BITCLIP
            buffer[ idx + 2 ] = (color >> 16) & BITCLIP


    # *** IMAGE AREA ***
        
    @micropython.viper
    def draw_raw_image( self, filename, x:int, y:int, width:int, height:int ):
        """ Draw RAW image (RGB565 format) on display
        Args
        filename (string): filename of image, example: "rain.bmp"
        x (int) : Start X position
        y (int) : Start Y position
        width (int) : Width of raw image
        height (int) : Height of raw image
        """
        with open( filename, 'rb' ) as f:
            buffer = ptr8( self.buffer )
            screen_width = int( self.width )
            
            for row in range( height ):
                buff_offset = row * screen_width * 3
                
                image_data = f.read( width * 2 )
                image_buffer = ptr8( image_data )

                col = 0
                while col < width:
                    color = ( image_buffer[col * 2] << 8) | image_buffer[col * 2 + 1]

                    col3 = col * 3                
                    
                    buffer[ buff_offset + col3 ] = ( (color >> 11) & 0x1F ) << 3
                    buffer[ buff_offset + col3 + 1 ] = ( (color >> 5) & 0x3F ) << 2
                    buffer[ buff_offset + col3 + 2 ] = ( color & 0x1F ) << 3
                    
                    col += 1      
        
    def draw_bmp( self, filename, x = 0, y = 0 ):
        """ Draw BMP image on display
        Args
        filename (string): filename of image, example: "rain.bmp"
        x (int) : Start X position
        y (int) : Start Y position
        """
        #f = open(filename, 'rb')
        with open( filename, 'rb' ) as f:
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

                    frame_width, frame_height = width, height
                    
                    if x + frame_width > self.width:
                        frame_width = self.width - x
                        
                    if y + frame_height > self.height:
                        frame_height = self.height - y
               
                    f.seek(offset)
                    
                    self._send_bmp_to_buffer(f, x, y, frame_height, frame_width, offset, rowsize)
    
    @micropython.viper           
    def _send_bmp_to_buffer( self, f, x: int, y: int, frame_height: int, frame_width: int, offset: int, rowsize: int ):
        """ Send bmp-file to display
        Args
        f (object File) : Image file
        frame_height (int): Height of image frame
        frame_width (int): Width of image frame
        offset (int): Internal byte offset of image-file
        rowsize (int): Internal byte rowsize of image-file        
        """
        buffer = ptr8(self.buffer)
        screen_width = int(self.width)
        screen_height = int(self.height)
        
        main_offset = int(self.buffsize) - ( (screen_height - frame_height - y) * screen_width - x ) * 3
        
        frame_bites = frame_width * 3
        
        for row in range(frame_height):
            buff_offset = main_offset - row * screen_width * 3
            # Start position of new row in image-file
            pos = offset + row * rowsize
                                    
            if int(f.tell()) != pos:
                f.seek(pos)
            
            # Reading one row from image-file
            bgr_row = f.read( frame_bites )
            image_buffer = ptr8( bgr_row )
            
            col = 0
            while col < frame_width:
                buf_pos = col * 3                
                buffer[ buff_offset + buf_pos ] = image_buffer[ buf_pos + 2 ]
                buffer[ buff_offset + buf_pos + 1 ] = image_buffer[ buf_pos + 1 ]
                buffer[ buff_offset + buf_pos + 2 ] = image_buffer[ buf_pos ]
                
                col += 1 

    
    # *** TEXT AREA ***
    
    def set_font( self, font ):
        """ Set font for text
        Args
        font (module): Font module generated by font_to_py.py
        """
        self.font = font
        
    def draw_text( self, text, x, y, color ):
        """ Draw text on display (fast version)
        Args
        x (int) : Start X position
        y (int) : Start Y position
        color (int): RGB color
        bg (int) : Bacground, RGB color
        
        Return (int, int): Last position of the carriage: X, Y        
        """       
        x_start = x
        glyph_height = 0
        screen_height = self.height
        screen_width = self.width
        
        font = self.font        
        if font == None:
            print("Font not set")
            return False
        
        draw_bitmap = self.draw_bitmap
        getch = font.get_ch
        
        for char in text:
            if char == "\n": # New line
                x = screen_width
                continue
            
            if char == "\t": #replace tab to space
                char = " "                
            
            glyph = getch(char)
            glyph_height = glyph[1]
            glyph_width = glyph[2]
            
            if x + glyph_width >= screen_width: # End of row
                x = x_start
                y += glyph_height
                
            if y + glyph_height >= screen_height: # End of screen
                break
                
            draw_bitmap(glyph, x, y, color)
            x += glyph_width
            
            if char == " " and (x + glyph_width) <= screen_width: # double size for space
                x += glyph_width
                
        return ( x, y )
        
    @micropython.viper
    def draw_bitmap( self, bitmap, x:int, y:int, color:int ):
        """ Draw one bitmap (glyph) on display (Fast version)
        Args
        bitmap (tuple) : Bitmap data [data, height, width]
        x (int) : Start X position
        y (int) : Start Y position
        color (int): RGB color
        """
        data  = ptr8(bitmap[0]) #memoryview of bitmap
        height = int(bitmap[1]) 
        width  = int(bitmap[2])
        screen_width  = int(self.width)
        
        red  = color & BITCLIP
        green = (color >> 8) & BITCLIP
        blue   = (color >> 16) & BITCLIP
 
        buffer = ptr8(self.buffer)

        i = 0
        for h in range(height):
            ypos = (h + y) * screen_width * 3

            bit_index = 0
            while bit_index < width:
                byte = data[i]

                if byte == 0:
                    bit_index += 8
                    i += 1
                    continue
                
                pos = ypos + (bit_index + x) * 3 + 21
                #Drawing pixels when bit = 1
                for bit in range(8):
                    if ( byte >> bit ) & 1:
                        pos_offset = pos - ( bit * 3 )
                        buffer[ pos_offset     ] = red
                        buffer[ pos_offset + 1 ] = green
                        buffer[ pos_offset + 2 ] = blue
                
                bit_index += 8
                i += 1
      
    def rect( self, x, y, width, height, color, filled = False):
        """ Compatibility for FrameBuffer rect """
        if filled:
            self.fill_rect( x, y, width, height, color)
        else:
            self.draw_rect( x, y, width, height, color, 1 )
    
    def line ( self, x1, y1, x2, y2, color ):
        self.draw_line( x1, y1, x2, y2, color )
        
        
    @staticmethod
    @micropython.viper
    def rgb( red:int, green:int, blue:int ) -> int:
        """ Convert 8,8,8 bits RGB to 24 bits  """
        return red | ( green << 8) | (blue << 16)
    
    
    def rect( self, x, y, width, height, color, filled = False):
        """ 100% MicroPython FrameBuffer compatibility for rect """
        if filled:
            self.fill_rect( x, y, width, height, color)
        else:
            self.draw_rect( x, y, width, height, color, 1 )
    
    def line ( self, x1, y1, x2, y2, color ):
        """ 100% MicroPython FrameBuffer compatibility for line """
        self.draw_line( x1, y1, x2, y2, color )
         
    @micropython.viper
    def draw_ellipse(self, x:int, y:int, xr:int, yr:int, color:int, border:int, mask:int):
        """ Ultra-fast integer-only hollow ellipse routine with quadrant mask filtering """
        buffer = ptr8(self.buffer)
        width = int(self.width)
        height = int(self.height)

        r = color & BITCLIP
        g = (color >> 8) & BITCLIP
        b = (color >> 16) & BITCLIP

        x0 = int(x)
        y0 = int(y)

        xr2 = xr * xr
        yr2 = yr * yr
        outer_val = xr2 * yr2

        xr_in = xr - border
        yr_in = yr - border
        if xr_in < 0: xr_in = 0
        if yr_in < 0: yr_in = 0
        inner_val = xr_in * xr_in * yr_in * yr_in
        xr_in2 = xr_in * xr_in
        yr_in2 = yr_in * yr_in

        x_min = x0 - xr
        y_min = y0 - yr
        x_max = x0 + xr
        y_max = y0 + yr

        if x_min < 0: x_min = 0
        if y_min < 0: y_min = 0
        if x_max >= width:  x_max = width - 1
        if y_max >= height: y_max = height - 1

        for yy in range(y_min, y_max + 1):
            dy = yy - y0
            dy2 = dy * dy
            term_outer_y = dy2 * xr2
            term_inner_y = dy2 * xr_in2
            
            for xx in range(x_min, x_max + 1):
                dx = xx - x0
                dx2 = dx * dx
                
                v_outer = dx2 * yr2 + term_outer_y
                
                if v_outer <= outer_val:
                    v_inner = dx2 * yr_in2 + term_inner_y
                    if v_inner > inner_val:
                        # Разрешение битовой маски квадрантов стандарта MIPI/MicroPython
                        q_bit = 0
                        if dx >= 0:
                            if dy < 0: q_bit = 1     # Квадрант 1: Верх-Право (bit 0)
                            else: q_bit = 8          # Квадрант 4: Низ-Право (bit 3)
                        else:
                            if dy < 0: q_bit = 2     # Квадрант 2: Верх-Лево (bit 1)
                            else: q_bit = 4          # Квадрант 3: Низ-Лево (bit 2)
                        
                        if (mask & q_bit) != 0:
                            idx = (yy * width + xx) * 3
                            buffer[idx] = r
                            buffer[idx + 1] = g
                            buffer[idx + 2] = b
                            
    @micropython.viper
    def fill_ellipse(self, x:int, y:int, xr:int, yr:int, color:int, mask:int):
        """ Ultra-fast integer-only filled ellipse routine """
        buffer = ptr8(self.buffer)
        width = int(self.width)
        height = int(self.height)

        r = color & BITCLIP
        g = (color >> 8) & BITCLIP
        b = (color >> 16) & BITCLIP

        x0 = int(x)
        y0 = int(y)

        xr2 = xr * xr
        yr2 = yr * yr
        outer_val = xr2 * yr2

        x_min = x0 - xr
        y_min = y0 - yr
        x_max = x0 + xr
        y_max = y0 + yr

        if x_min < 0: x_min = 0
        if y_min < 0: y_min = 0
        if x_max >= width:  x_max = width - 1
        if y_max >= height: y_max = height - 1

        for yy in range(y_min, y_max + 1):
            dy = yy - y0
            dy2 = dy * dy
            term_outer_y = dy2 * xr2
            
            for xx in range(x_min, x_max + 1):
                dx = xx - x0
                
                v_outer = (dx * dx) * yr2 + term_outer_y
                
                if v_outer <= outer_val:
                    q_bit = 0
                    if dx >= 0:
                        if dy < 0: q_bit = 1
                        else: q_bit = 8
                    else:
                        if dy < 0: q_bit = 2
                        else: q_bit = 4
                    
                    if (mask & q_bit) != 0:
                        idx = (yy * width + xx) * 3
                        buffer[idx] = r
                        buffer[idx + 1] = g
                        buffer[idx + 2] = b

    def ellipse(self, x, y, xr, yr, color, filled=False, mask=15):
        """ 100% MicroPython FrameBuffer compatibility for ellipse """
        if filled:
            self.fill_ellipse(x, y, xr, yr, color, mask)
        else:
            self.draw_ellipse(x, y, xr, yr, color, 1, mask)    