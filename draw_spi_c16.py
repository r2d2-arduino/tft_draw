"""
DRAW_SPI_C16 v 0.1.4
Draw library for color displays

Color: 16-bit
 
Project path: https://github.com/r2d2-arduino/tft_draw
MIT License

Author: Arthur Derkach 
"""
from struct import pack
from micropython import const

class DRAW_SPI_C16:
    
    BITS_PER_PIXEL = const( 16 )
    BUFFER_INTERNAL = const(4097)
    BUFFER_ROWS = const(9)
    
    def __init__( self, spi, cs, dc, width, height, offset_x = 0, offset_y = 0 ):
        self.spi = spi
        self.cs  = cs
        self.dc  = dc
        
        self.width  = width
        self.height = height
        
        self.offset_x = offset_x
        self.offset_y = offset_y
        
        self.font  = None
        self.pixel_format = 16
        
    def swap_dimensions(self):
        """ Swaps width and height for 90/270 degree rotation. """
        self.width, self.height = self.height, self.width
        
        self.offset_x, self.offset_y = self.offset_y, self.offset_x

    @micropython.viper
    def set_window( self, x0:int, y0:int, x1:int, y1:int ):
        """ Sets the starting position and the area of drawing on the display
        Args
        x0 (int): Start X position  ________
        y0 (int): Start Y position  |s---> |
        x1 (int): End X position    ||     |    
        y1 (int): End Y position    |v____e|  
        """
        offx = int( self.offset_x )
        offy = int( self.offset_y )
        
        dc_on = self.dc.on
        dc_off = self.dc.off
        
        spi_write = self.spi.write
        
        dc_off() # command mode
        spi_write( b'\x2a' )
        dc_on() # data mode
        spi_write( pack( ">HH", x0 + offx, x1 + offx ) )
        
        dc_off() # command mode
        spi_write( b'\x2b' )
        dc_on() # data mode
        spi_write( pack( ">HH", y0 + offy, y1 + offy ) )
        
        dc_off() # command mode
        spi_write( b'\x2c' )
        dc_on()
    
    # *** DRAW AREA ***
    
    def fill_rect( self, x, y, width, height, color ):
        """ Draw filled rectangle
        Args
        x (int): Start X position          xy----->
        y (int): Start Y position          |   w  .
        width (int): Width of rectangle  h |      .
        height (int): Height of rectangle  v.......
        color (int): RGB color
        """        
        self.cs.value(0)        
        self.set_window(x, y, x + width - 1, y + height - 1)
        
        if ( width * height < self.BUFFER_INTERNAL ):
            self.spi.write( pack( '<H', color ) * width * height )
        else:
            buffer = pack( '<H', color ) * width
            spwrite = self.spi.write
            
            blockbuff = BUFFER_ROWS * buffer
            blocknum = height // BUFFER_ROWS
            blockrest = height % BUFFER_ROWS

            for _ in range( blocknum ):
                spwrite( blockbuff )
                
            if blockrest:
                spwrite( buffer * blockrest )
                
        self.cs.value(1)
        
    def fill( self, color ):
        """ Fill whole screen
        Args
        color (int): RGB color
        """        
        self.fill_rect( 0, 0, self.width, self.height, color )        
        
    def fill_screen( self, color ):
        """ Fill whole screen
        Args
        color (int): RGB color
        """        
        self.fill_rect( 0, 0, self.width, self.height, color )
        
    
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
        
        dx = int( abs(x1 - x0) )
        dy = int( abs(y1 - y0) )
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        dc_on = self.dc.on
        dc_off = self.dc.off
        
        spi_write = self.spi.write
        
        offx = int(self.offset_x)
        offy = int(self.offset_y)
        
        x0 += offx
        x1 += offx
        y0 += offy
        y1 += offy        
        
        color_bytes = pack( '<H', color )
        
        x0_bytes = pack( ">HH", x0, x0 )
        y0_bytes = pack( ">HH", y0, y0 ) 
        
        self.cs.value(0)
                
        while True:
            dc_off() # command mode
            spi_write( b'\x2a' )
            dc_on() # data mode
            spi_write( x0_bytes )
            
            dc_off() # command mode
            spi_write( b'\x2b' )
            dc_on() # data mode
            spi_write( y0_bytes )
            
            dc_off() # command mode
            spi_write( b'\x2c' )
            dc_on() # data mode
            spi_write( color_bytes )
        
            if x0 == x1 and y0 == y1:
                break            
            
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
                x0_bytes = pack( ">HH", x0, x0 )
                
            if e2 < dx:
                err += dx
                y0 += sy
                y0_bytes = pack( ">HH", y0, y0 )

        self.cs.value(1)

    def draw_circle( self, x, y, radius, color, border = 1 ):
        """ Draw circle
        Args
        x (int): Start X position          
        y (int): Start Y position              
        radius (int): Radius of circle         
        border (int): border of circle   
        color (int): RGB color
        """
        if (x < 0 or y < 0 or x >= self.width or y >= self.height):
            print("Invalid params in draw_circle")
            return
        
        spi_write = self.spi.write
        set_window = self.set_window
        color_bytes = pack( '<H', color )
        
        self.cs.value(0)
        
        for r in range(radius - border, radius):
            # Bresenham algorithm
            x_pos = 0 - r
            y_pos = 0
            err = 2 - 2 * r
            while 1:
                set_window( x - x_pos, y + y_pos, x - x_pos, y + y_pos )
                spi_write( color_bytes )
                set_window( x + x_pos, y + y_pos, x + x_pos, y + y_pos )
                spi_write( color_bytes )
                set_window( x + x_pos, y - y_pos, x + x_pos, y - y_pos )
                spi_write( color_bytes )
                set_window( x - x_pos, y - y_pos, x - x_pos, y - y_pos )
                spi_write( color_bytes )
                
                e2 = err
                if (e2 <= y_pos):
                    y_pos += 1
                    err += y_pos * 2 + 1
                    if(0-x_pos == y_pos and e2 <= x_pos):
                        e2 = 0
                if (e2 > x_pos):
                    x_pos += 1
                    err += x_pos * 2 + 1
                if x_pos > 0:
                    break
                
        self.cs.value(1)
    
    def fill_circle( self, x, y, radius, color ):
        """ Draw filled circle
        Args
        x (int): Center X position          
        y (int): Center Y position              
        radius (int): Radius of circle
        color (int): RGB color
        """
        set_window = self.set_window
        spi_write = self.spi.write
        #color_bytes = [color & 0xff, (color >> 8) & 0xff]
        color_bytes_2 = pack( '<H', color ) * 2
        radius_s2 = radius**2
        self.cs.value(0) 
        for p in range( -radius, radius + 1 ):
            # Calculating the horizontal line
            dx = round( ( radius_s2 - p**2 )**0.5 )
            if dx > 0:                       
                set_window( x - dx, y + p, x + dx - 1, y + p )
                spi_write( color_bytes_2 * dx )
                    
        self.cs.value(1)      
      
    def draw_arc( self, x, y, radius, start_angle, end_angle, color ):
        ''' Draw arc
        Args
        x (int): Center X position
        y (int): Center Y position
        radius (int): Radius of arc
        start_angle (int): Start angle
        end_angle   (int): End angle
        color (int): RGB color
        '''
        set_window = self.set_window
        spi_write = self.spi.write        
        
        #color_bytes = bytearray( [color & 0xff, (color >> 8) & 0xff] )
        color_bytes = pack( '<H', color )
        
        self.cs.value(0)
        
        for angle in range( start_angle, end_angle + 1 ):
            theta = math.radians( angle )
            x0 = round( x + radius * math.cos( theta ) ) 
            y0 = round( y + radius * math.sin( theta ) )

            set_window( x0, y0, x0, y0 )
            spi_write( color_bytes )
        
        self.cs.value(1)
        
    def fill_arc( self, x, y, radius, start_angle, end_angle, thickness, color ):
        ''' Fill arc
        Args
        x (int): Center X position
        y (int): Center Y position
        radius (int): Radius of arc
        start_angle (int): Start angle
        end_angle   (int): End angle
        color (int): RGB color
        border (int): Border of circle
        '''
        fill_circle = self.fill_circle
        
        angle_step = 4
        in_radius = thickness//2
        
        angle = start_angle
        while angle < end_angle + 1:
            theta = math.radians( angle )
            x0 = int( x + radius * math.cos( theta ) ) 
            y0 = int( y + radius * math.sin( theta ) )
            
            fill_circle( x0, y0, in_radius, color)
            angle += angle_step      
      
    @micropython.viper
    def draw_pixel( self, x:int, y:int, color:int ):
        """ Draw one pixel on display
        Args
        x (int): X position on dispaly, example 100
        y (int): Y position on dispaly, example 200
        color (int): RGB color
        """
        self.cs.value(0)
        
        offx = int( self.offset_x )
        offy = int( self.offset_y )
        
        dc_on = self.dc.on
        dc_off = self.dc.off
        
        spi_write = self.spi.write
        
        dc_off() # command mode
        spi_write( b'\x2a' )
        dc_on() # data mode
        spi_write( pack( ">HH", x + offx, x + offx ) )
        
        dc_off() # command mode
        spi_write( b'\x2b' )
        dc_on() # data mode
        spi_write( pack( ">HH", y + offy, y + offy ) )
        
        dc_off() # command mode
        spi_write( b'\x2c' )
        dc_on()
            
        #spi.write(bytearray([(color >> 8) & 0xff, color & 0xff]))
        spi_write( pack( '<H', color ) )
        
        self.cs.value(1)

    # *** IMAGE AREA ***
    def draw_raw_image( self, filename, x, y, width, height ):
        """ Draw RAW image (RGB565 format) on display
        Args
        filename (string): filename of image, example: "rain.bmp"
        x (int) : Start X position
        y (int) : Start Y position
        width (int) : Width of raw image
        height (int) : Height of raw image
        """
        with open( filename, 'rb' ) as f:
            self.cs.value( 0 )      
            self.set_window( x, y, x + width - 1, y + height - 1 ) # Set start position
            
            byte_width = width * 2
            total_bytes = height * byte_width
            
            if ( total_bytes < self.BUFFER_INTERNAL ):
                image_buffer = f.read( total_bytes )
                self.spi.write( image_buffer )
            else:
                spi_write = self.spi.write
                
                blocknum = height // BUFFER_ROWS
                blockrest = height % BUFFER_ROWS
                
                image_buffer = bytearray( byte_width * BUFFER_ROWS )
                
                for _ in range( blocknum ):
                    #image_buffer = f.read( byte_width * BUFFER_ROWS )
                    #spi_write( image_buffer )
                    f.readinto( image_buffer )
                    spi_write( image_buffer )
                    
                if blockrest:
                    image_rest = f.read( byte_width * blockrest )
                    spi_write( image_rest )
                         
            self.cs.value( 1 )  # Chip disabled
        
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

                    frameWidth, frameHeight = width, height
                    
                    if x + frameWidth > self.width:
                        frameWidth = self.width - x
                        
                    if y + frameHeight > self.height:
                        frameHeight = self.height - y
               
                    f.seek(offset)
                    
                    self.cs.value(0)
                    self.set_window(x, y, x + frameWidth - 1, y + frameHeight - 1)
                    
                    self._send_bmp_to_display(f, frameHeight, frameWidth, offset, rowsize)
             
                    self.cs.value(1)
                    
    @micropython.viper           
    def _send_bmp_to_display( self, f, frameHeight: int, frameWidth: int, offset: int, rowsize: int ):
        """ Send bmp-file to display
        Args
        f (object File) : Image file
        frameHeight (int): Height of image frame
        frameWidth (int): Width of image frame
        offset (int): Internal byte offset of image-file
        rowsize (int): Internal byte rowsize of image-file        
        """
        spi_buffer = bytearray( frameWidth * 2 )
        row_buffer = ptr16( spi_buffer )
        spi_write = self.spi.write

        for row in range( frameHeight ):
            # Start position of new row in image-file
            pos = offset + ( frameHeight - row - 1 ) * rowsize
            #pos = offset + row * rowsize
                                    
            if int( f.tell() ) != pos:
                f.seek( pos )

            # Reading one row from image-file
            bgr_row = f.read( frameWidth * 3 )
            image_buffer = ptr8( bgr_row )

            for col in range( frameWidth ):             
                #Getting color bytes
                red   = image_buffer[ col * 3     ]
                green = image_buffer[ col * 3 + 1 ]
                blue  = image_buffer[ col * 3 + 2 ]
                
                row_buffer[ col ] = (green & 0x1C) << 11 |  ((red & 0xF8) << 5 | (blue & 0xF8)) | (green & 0xE0) >> 5
            
            spi_write( spi_buffer )
    
    # *** TEXT AREA ***
    
    def set_font( self, font ):
        """ Set font for text
        Args
        font (module): Font module generated by font_to_py.py
        """
        self.font = font
        
    def draw_text( self, text, x, y, color, bg = 0x0000 ):
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
        
        getchar = font.get_ch
        
        for char in text:
            if char == "\n": # New line
                x = x_start
                y += glyph_height
                continue
            
            if char == "\t": #replace tab to space
                char = " "                
            
            glyph = getchar(char)
            glyph_height = glyph[1]
            glyph_width = glyph[2]
            
            if x + glyph_width > screen_width: # End of row
                x = x_start
                y += glyph_height
                
            if y + glyph_height > screen_height: # End of screen
                break
                
            self.draw_bitmap(glyph, x, y, color, bg)
            x += glyph_width
            
            if char == " " and (x + glyph_width) <= screen_width: # double size for space
                self.draw_bitmap(glyph, x, y, color, bg)
                x += glyph_width
                
        return ( x, y )
        
  
    @micropython.viper
    def draw_bitmap( self, bitmap, x:int, y:int, color:int, bg:int ):
        """ Draw one bitmap (glyph) on display (Fast version)
        Args
        bitmap (tuple) : Bitmap data [data, height, width]
        x (int) : Start X position
        y (int) : Start Y position
        color (int): RGB color
        bg (int) : Bacground, RGB color
        """
        data  = ptr8(bitmap[0]) #memoryview of bitmap
        height = int(bitmap[1]) 
        width  = int(bitmap[2])
        
        self.cs.value(0)
        self.set_window(x, y, x + width - 1, y + height - 1)
        
        spi_buffer = bytearray( height * width * 2 )
        bitmap_buffer = ptr16( spi_buffer )
        
        # Sending Color data        
        i = 0
        for row in range(height):
            dots_sum = 0                    
            while dots_sum < width:
                byte = data[i]
                i += 1
                dot = 0
                offset = (row * width + dots_sum)
                
                while dot < 8 and dot + dots_sum < width:
                    if (byte >> (7 - dot)) & 1: # main color
                        bitmap_buffer[ dot + offset ] = color
                    else: # background
                        bitmap_buffer[ dot + offset ] = bg
                    dot += 1                         
                dots_sum += 8
                
        self.spi.write(spi_buffer)     
        self.cs.value(1)
        
    @staticmethod
    @micropython.viper
    def color565( red:int, green:int, blue:int ) -> int:
        """ Convert 8,8,8 bits RGB to 16 bits  """
        return ( (green & 0x1c) << 11 | (blue & 0xf8) << 5 | (red & 0xf8) | (green & 0xe0) >> 5 )


    @staticmethod
    @micropython.viper
    def rgb( red:int, green:int, blue:int ) -> int:
        """ Convert 8,8,8 bits RGB to 16 bits
        Compatibility for old code """
        return ( (green & 0x1c) << 11 | (blue & 0xf8) << 5 | (red & 0xf8) | (green & 0xe0) >> 5 )
