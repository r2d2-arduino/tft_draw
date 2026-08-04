"""
DRAW_FB_C16 v 0.1.2
Draw library for color displays

Color: 16-bit
 
Project path: https://github.com/r2d2-arduino/tft_draw
MIT License

Author: Arthur Derkach 
"""
from framebuf import FrameBuffer, RGB565
from micropython import const

class DRAW_FB_C16 (FrameBuffer):
    
    BITS_PER_PIXEL = const( 16 )
    
    def __init__( self, width, height ):
        
        self.width  = width
        self.height = height
        
        self.buffsize = width * height * 2
        self.buffer = bytearray( self.buffsize )
        self.pixel_format = 16
        self.bpp = 2
        
        self.font = None
        
        super().__init__( self.buffer, self.width, self.height, RGB565 )
        
    def swap_dimensions(self):
        """ Swaps width and height for 90/270 degree rotation. """
        self.width, self.height = self.height, self.width
        
        super().__init__(self.buffer, self.width, self.height, RGB565)
        
    """ IMAGE AREA """
    
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
            buffer = memoryview( self.buffer )
            screen_width = int( self.width )

            for row in range( height ):
                offset = ( x + ( row + y ) * screen_width ) * 2
                f.readinto( buffer[ offset:offset + width * 2 ] )
        
    def draw_bmp( self, filename, x = 0, y = 0 ):
        """ Draw BMP image on display
        Args
        filename (string): filename of image, example: "rain.bmp"
        x (int) : Start X position
        y (int) : Start Y position
        """
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
                    
                    self._send_bmp_to_framebuff(f, x, y, frameHeight, frameWidth, offset, rowsize)

            
    @micropython.viper           
    def _send_bmp_to_framebuff( self, f, x: int, y: int, frameHeight: int, frameWidth: int, offset: int, rowsize: int ):
        """ Send bmp-file to display
        Args
        f (object File) : Image file
        frameHeight (int): Height of image frame
        frameWidth (int): Width of image frame
        offset (int): Internal byte offset of image-file
        rowsize (int): Internal byte rowsize of image-file        
        """
        buffer = ptr16(self.buffer)
        screen_width = int(self.width)
        buffsize = int(self.buffsize) // 2
        main_offset = buffsize - y * screen_width - frameWidth - x
        
        for row in range(frameHeight):
            buff_offset = main_offset - row * screen_width
            # Start position of new row in image-file
            pos = offset + row * rowsize
                                    
            if int(f.tell()) != pos:
                f.seek(pos)
            
            # Reading one row from image-file
            bgr_row = f.read( frameWidth * 3 )
            image_buffer = ptr8( bgr_row )
            
            for col in range( frameWidth ):
                #Getting color bytes
                red   = image_buffer[ col * 3     ]
                green = image_buffer[ col * 3 + 1 ]
                blue  = image_buffer[ col * 3 + 2 ]
                
                buffer[ buff_offset + col ] = (green & 0x1C) << 11 |  ((red & 0xF8) << 5 | (blue & 0xF8)) | (green & 0xE0) >> 5
        
    """ TEXT AREA """
        
    def set_font( self, font ):
        """ Set font for text
        Args
        font (module): Font module generated by font_to_py.py
        """
        self.font = font
        
    def draw_text( self, text, x, y, color ):
        """ Draw text on display
        Args
        x (int) : Start X position
        y (int) : Start Y position
        color (int): RGB565 2-byte color, example 0xF81F
        
        Return (int, int): Last position of the carriage: X, Y        
        """
        x_start = x
        screen_height = self.height
        screen_width = self.width
        
        draw_bitmap = self.draw_bitmap
        
        font = self.font        
        if font == None:
            print("Font not set")
            return False
        
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
            
            if char == " ": # double size for space
                x += glyph_width
                
            if x + glyph_width > screen_width:
                x = x_start
                y += glyph_height
                
            if y + glyph_height > screen_height: # End of screen
                break                
  
            draw_bitmap(glyph, x, y, color)
            x += glyph_width
        return ( x, y )
                
    @micropython.viper
    def draw_bitmap( self, bitmap, x:int, y:int, color:int ):
        """ Draw one bitmap (glyph) on display
        Args
        bitmap (tuple) : Bitmap data [data, height, width]
        x (int) : Start X position
        y (int) : Start Y position
        color (int): RGB565 2-byte color, example 0xF81F
        """
        data   = ptr8(bitmap[0]) #memoryview of bitmap
        height = int(bitmap[1])
        width  = int(bitmap[2])
        
        buffer = ptr16(self.buffer)
        screen_width  = int(self.width)      
        
        i = 0
        for h in range(height):
            ypos = (h + y) * screen_width 

            bit_index = 0
            while bit_index < width:
                byte = data[i]
                
                if byte == 0:
                    bit_index += 8
                    i += 1
                    continue
                
                pos = ypos + bit_index + x 
                #Drawing pixels when bit = 1
                if (byte >> 7) & 1:                    
                    buffer[ pos     ] = color       
                if (byte >> 6) & 1:                   
                    buffer[ pos + 1 ] = color                  
                if (byte >> 5) & 1:                    
                    buffer[ pos + 2 ] = color
                if (byte >> 4) & 1:                    
                    buffer[ pos + 3 ] = color
                if (byte >> 3) & 1:                    
                    buffer[ pos + 4 ] = color
                if (byte >> 2) & 1:                    
                    buffer[ pos + 5 ] = color
                if (byte >> 1) & 1:                    
                    buffer[ pos + 6 ] = color
                if byte & 1:                    
                    buffer[ pos + 7 ] = color
                
                bit_index += 8
                i += 1 
    
    @staticmethod
    @micropython.viper
    def color565( red:int, green:int, blue:int ) -> int:
        """ Convert 8,8,8 bits RGB to 16 bits  """
        return ( (green & 0x1c) << 11 | (blue & 0xf8) << 5 | (red & 0xf8) | (green & 0xe0) >> 5 )


    @staticmethod
    @micropython.viper
    def rgb( red:int, green:int, blue:int ) -> int:
        """ Convert 8,8,8 bits RGB to 16 bits  """
        return ( (green & 0x1c) << 11 | (blue & 0xf8) << 5 | (red & 0xf8) | (green & 0xe0) >> 5 )
