"""
DRAW_FB_C12 v 0.0.1 (Not finished!)
Draw library for color displays

Color: 12-bit
 
Project path: https://github.com/r2d2-arduino/tft_draw
MIT License

Author: Arthur Derkach 
"""
from micropython import const

class DRAW_FB_C12:
    
    BITS_PER_PIXEL = const( 12 )
    
    def __init__( self, buffer, width, height ):

        self.width  = width
        self.height = height
        
        self.buffsize = width * height * 3 // 2
        self.buffer = bytearray( self.buffsize )
        
        self.font  = None
        self.pixel_format = 12
        self.bpp = 1.5
        
    def swap_dimensions(self):
        """ Swaps width and height for 90/270 degree rotation. """
        self.width, self.height = self.height, self.width
        
    # *** DRAW AREA ***
    
    @micropython.viper
    def fill( self, color: int ):
        """
        Быстрая заливка всего 12-битного RGB444 буфера.
        color: 0xRGB (по 4 бита на компоненту)
        """
        buffer = ptr8( self.buffer )
        buf_len = int(len(self.buffer))

        # Извлекаем 4-битные компоненты цвета
        red   = (color >> 8) & 0xF
        green = (color >> 4) & 0xF
        blue  = color & 0xF

        # Формируем 3 байта = 2 пикселя одинакового цвета
        byte0 = (red << 4) | green
        byte1 = (blue << 4) | red
        byte2 = (green << 4) | blue

        # Основной цикл по тройкам байтов (2 пикселя)
        i = 0
        end = buf_len - 2
        while i < end:
            buffer[ i     ] = byte0
            buffer[ i + 1 ] = byte1
            buffer[ i + 2 ] = byte2
            i += 3       


    @micropython.viper
    def fill_rect( self, x: int, y: int, width: int, height: int, color: int ):
        """
        Быстрая заливка прямоугольника в 12-битном RGB444 буфере.
        x, y — координаты верхнего левого угла
        width, height — размеры области
        color — 0xRGB (по 4 бита на канал)
        """
        buffer = ptr8(self.buffer)
        w_total = int(self.width)

        # Извлекаем 4-битные компоненты
        red   = (color >> 8) & 0xF
        green = (color >> 4) & 0xF
        blue  =  color & 0xF

        # Формируем три байта для пары пикселей
        byte0 = (red << 4)   | green
        byte1 = (blue << 4)  | red
        byte2 = (green << 4) | blue
        
        # Проходим по каждой строке
        for row in range(height):
            # Смещение начала строки (в байтах)
            row_start = int( ((y + row) * w_total + x) * 3 // 2 )

            i = row_start
            x_remaining = width

            # Пишем парами пикселей (2 пикселя = 3 байта)
            while x_remaining >= 2:
                buffer[ i     ] = byte0
                buffer[ i + 1 ] = byte1
                buffer[ i + 2 ] = byte2
                i += 3
                x_remaining -= 2

            # Если остался один пиксель (нечётная ширина)
            if x_remaining:
                buffer[ i     ] = byte0
                buffer[ i + 1 ] = byte1

    
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
    def draw_line(self, x0:int, y0:int, x1:int, y1:int, color:int):
        """ Draw line using Bresenham's Algorithm
        Args
        x0 (int): Start X position   s
        y0 (int): Start Y position    \
        x1 (int): End X position       \ 
        y1 (int): End Y position        e
        color (int): RGB color
        """
        buf = ptr8(self.buffer)
        w_total = int(self.width)

        # === 1. Цвет ===
        r = (color >> 8) & 0xF
        g = (color >> 4) & 0xF
        b = color & 0xF
        byte0 = (r << 4) | g
        byte1 = (b << 4) | r
        byte2 = (g << 4) | b

        # === 2. Алгоритм Брезенхема ===
        dx = int(abs(x1 - x0))
        sx = 1 if x0 < x1 else -1
        dy = -int(abs(y1 - y0))
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        # === 3. Основной цикл ===
        while True:
            # Смещение в буфере
            pixel_index = (y0 * w_total + x0)
            byte_index = int(pixel_index * 3 // 2)

            # === запись пикселя ===
            # определяем чётность пикселя (0 или 1 внутри пары)
            if (x0 & 1) == 0:
                # первый пиксель пары
                buf[byte_index] = byte0
                buf[byte_index + 1] = byte1
            else:
                # второй пиксель пары
                buf[byte_index + 1] = (buf[byte_index + 1] & 0xF0) | (r & 0x0F)
                buf[byte_index + 2] = byte2

            # === выход, если дошли до конца ===
            if x0 == x1 and y0 == y1:
                break

            e2 = err << 1
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
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
        buf = ptr8(self.buffer)
        w_total = int(self.width)
        bytes_per_pixel = 3 / 2.0  # 1.5 байта на пиксель

        # === 1. Цвет в 12-битном формате ===
        r = (color >> 8) & 0xF
        g = (color >> 4) & 0xF
        b = color & 0xF
        byte0 = (r << 4) | g
        byte1 = (b << 4) | r
        byte2 = (g << 4) | b

        # === 2. Вспомогательная функция — запись пикселя ===
        def set_px(px:int, py:int):
            if px < 0 or py < 0 or px >= w_total or py >= int(self.height):
                return
            pixel_index = py * w_total + px
            byte_index = int(pixel_index * bytes_per_pixel)

            if (px & 1) == 0:
                buf[byte_index] = byte0
                buf[byte_index + 1] = byte1
            else:
                buf[byte_index + 1] = (buf[byte_index + 1] & 0xF0) | (r & 0x0F)
                buf[byte_index + 2] = (g << 4) | b

        # === 3. Алгоритм Брезенхема для окружности ===
        f = 1 - radius
        ddF_x = 1
        ddF_y = -2 * radius
        xx = 0
        yy = radius

        # Верх, низ, лево, право
        for t in range(border):
            set_px(x, y + radius - t)
            set_px(x, y - radius + t)
            set_px(x + radius - t, y)
            set_px(x - radius + t, y)

        while xx < yy:
            if f >= 0:
                yy -= 1
                ddF_y += 2
                f += ddF_y
            xx += 1
            ddF_x += 2
            f += ddF_x

            # Толщина линии — рисуем несколько концентрических пикселей
            for t in range(border):
                r_adj = t
                set_px(x + xx, y + yy - r_adj)
                set_px(x - xx, y + yy - r_adj)
                set_px(x + xx, y - yy + r_adj)
                set_px(x - xx, y - yy + r_adj)
                set_px(x + yy - r_adj, y + xx)
                set_px(x - yy + r_adj, y + xx)
                set_px(x + yy - r_adj, y - xx)
                set_px(x - yy + r_adj, y - xx)


    
    @micropython.viper
    def fill_circle(self, x:int, y:int, radius:int, color:int):
        """ Draw filled circle
        Args
        x (int): Start X position          
        y (int): Start Y position              
        radius (int): Radius of circle
        color (int): RGB color
        """
        pass

        
    @micropython.viper
    def pixel( self, x:int, y:int, color:int ):
        """ Draw one pixel on display
        Args
        x (int): X position on dispaly, example 100
        y (int): Y position on dispaly, example 200
        color (int): RGB color
        """        
        pass
    '''

    # *** IMAGE AREA ***
        
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
        
        main_offset = int(self.buffsize) - ( (screen_height - frame_height - y) * screen_width - x ) * 3 // 2
        
        frame_bites = frame_width * 3
        
        for row in range(frame_height):
            buff_offset = main_offset - row * screen_width * 3 // 2
            # Start position of new row in image-file
            pos = offset + row * rowsize
                                    
            if int(f.tell()) != pos:
                f.seek(pos)
            
            # Reading one row from image-file
            bgr_row = f.read( frame_bites )
            image_buffer = ptr8( bgr_row )
            
            b_pos = 0
            for col in range( frame_width ):             
                #Getting color bytes
                red   = image_buffer[ col * 3     ]
                green = image_buffer[ col * 3 + 1 ]
                blue  = image_buffer[ col * 3 + 2 ]
                
                buffer[ buff_offset + col ] = (green & 0x1C) << 11 |  ((red & 0xF8) << 5 | (blue & 0xF8)) | (green & 0xE0) >> 5


    
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
        
        for char in text:
            if char == "\n": # New line
                x = screen_width
                continue
            
            if char == "\t": #replace tab to space
                char = " "                
            
            glyph = font.get_ch(char)
            glyph_height = glyph[1]
            glyph_width = glyph[2]
            
            if x + glyph_width >= screen_width: # End of row
                x = x_start
                y += glyph_height
                
            if y + glyph_height >= screen_height: # End of screen
                break
                
            self.draw_bitmap(glyph, x, y, color)
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
        
        blue  = color & BITCLIP
        green = (color >> 8) & BITCLIP
        red   = (color >> 16) & BITCLIP
 
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
                for b in range(8):
                    if ( byte >> b ) & 1:
                        pos_offset = pos - ( b * 3 )
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
    '''    
        
    @staticmethod
    @micropython.viper
    def rgb( red:int, green:int, blue:int ) -> int:
        """ Convert 8,8,8 bits RGB to 24 bits  """
        return ((red >> 4) << 8) | ((green >> 4) << 4) | (blue >> 4)       
