#!/usr/bin/env python3
"""
Image Processing Workflow for Web Upload
- Converts images to JPG format
- Resizes images to web-friendly dimensions
- Adds copyright metadata
- Applies visible watermarks
- Organizes processed images in output directory
"""

import os
import sys
import shutil
import argparse
import subprocess
import datetime
from PIL import Image, ImageDraw, ImageFont

# Try importing pillow_heif for HEIC support
try:
    import pillow_heif
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False
    print("Warning: pillow-heif module not found. HEIC/HEIF file support will be limited.")
    print("To enable HEIC support, install pillow-heif: pip install pillow-heif")

# Constants
DEFAULT_COPYRIGHT_HOLDER = "YOURNAME"
DEFAULT_MAX_DIMENSION = 1024
DEFAULT_WATERMARK_OPACITY = 0.45
DEFAULT_WATERMARK_FONT_SIZE = 36
DEFAULT_WATERMARK_COLOR = (255, 255, 255)  # White

def create_directories(input_dir, working_dir, output_dir):
    """Create necessary directories if they don't exist."""
    for directory in [input_dir, working_dir, output_dir]:
        os.makedirs(directory, exist_ok=True)
        print(f"Directory ensured: {directory}")

def convert_to_jpg(input_path, output_path):
    """Convert image to JPG format."""
    try:
        # Handle HEIC files
        if input_path.lower().endswith(('.heic', '.heif')):
            if HEIC_SUPPORT:
                heif_file = pillow_heif.read_heif(input_path)
                image = Image.frombytes(
                    heif_file.mode, 
                    heif_file.size, 
                    heif_file.data,
                    "raw",
                    heif_file.mode,
                    heif_file.stride,
                )
            else:
                print(f"✗ Unable to process HEIC/HEIF file {input_path} - pillow-heif not installed")
                return False
        else:
            image = Image.open(input_path)
        
        # Convert to RGB (in case of RGBA or other modes)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save as JPG
        image.save(output_path, "JPEG", quality=95)
        print(f"✓ Converted to JPG: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error converting {input_path} to JPG: {str(e)}")
        return False

def resize_image(input_path, output_path, max_dimension):
    """Resize image to have maximum dimension specified."""
    try:
        image = Image.open(input_path)
        original_width, original_height = image.size
        
        # Calculate new dimensions
        if original_width > original_height:
            if original_width > max_dimension:
                new_width = max_dimension
                new_height = int(original_height * (max_dimension / original_width))
            else:
                new_width, new_height = original_width, original_height  # No resize needed
        else:
            if original_height > max_dimension:
                new_height = max_dimension
                new_width = int(original_width * (max_dimension / original_height))
            else:
                new_width, new_height = original_width, original_height  # No resize needed
        
        # Only resize if dimensions changed
        if (new_width, new_height) != (original_width, original_height):
            # Resize and save
            resized_image = image.resize((new_width, new_height), Image.LANCZOS)
            resized_image.save(output_path, "JPEG", quality=95)
            print(f"✓ Resized to {new_width}x{new_height}: {output_path}")
        else:
            # Just copy the file
            shutil.copy2(input_path, output_path)
            print(f"✓ No resize needed (already {original_width}x{original_height}): {output_path}")
        
        return True
    except Exception as e:
        print(f"✗ Error resizing {input_path}: {str(e)}")
        return False

def add_copyright(image_path, copyright_holder, year=None):
    """Add copyright metadata to image using exiftool."""
    # Use current year if not specified
    if year is None:
        try:
            year = datetime.datetime.now().year
        except:
            year = 2025
    
    # Copyright string
    copyright_string = f"Copyright © {year} {copyright_holder}. All rights reserved."
    
    try:
        # Call exiftool to add copyright metadata
        cmd = [
            'exiftool',
            '-overwrite_original',
            f'-Copyright={copyright_string}',
            f'-CopyrightNotice={copyright_string}',
            f'-XMP:Rights={copyright_string}',
            f'-IPTC:CopyrightNotice={copyright_string}',
            f'-EXIF:Copyright={copyright_string}',
            f'-IPTC:Credit={copyright_holder}',
            f'-IPTC:By-line={copyright_holder}',
            f'-XMP:Creator={copyright_holder}',
            image_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Added copyright to: {image_path}")
            return True
        else:
            print(f"✗ Error adding copyright to {image_path}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error adding copyright to {image_path}: {str(e)}")
        return False

def add_watermark(input_path, output_path, watermark_text, position=None, opacity=0.5, 
                 font_size=40, repeat=False, spacing=100, angle=0, font_color=(255, 255, 255),
                 scale_factor=None):
    """Add a text watermark to an image."""
    try:
        # Open the input image
        img = Image.open(input_path).convert("RGBA")
        
        # Create a transparent overlay for the watermark
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Calculate font size based on scale_factor if provided
        if scale_factor is not None:
            # Use the smaller dimension (width or height) to calculate font size
            base_dimension = min(img.width, img.height)
            font_size = int(base_dimension * scale_factor / 100)
        
        # Try to load font
        font = None
        scale_ratio = 1
        try:
            # Try multiple font options for better compatibility
            font_options = [
                "arial.ttf",
                "Arial.ttf",
                "DejaVuSans.ttf",
                "Verdana.ttf",
                "times.ttf",
                "Times New Roman.ttf"
            ]
            
            for font_name in font_options:
                try:
                    font = ImageFont.truetype(font_name, font_size)
                    break
                except IOError:
                    continue
                    
            if font is None:
                # If none of the fonts are found, use the default font
                font = ImageFont.load_default()
                # For default font, manually scale by creating a larger canvas and resizing
                if font_size > 40:  # Only do this for larger requested sizes
                    scale_ratio = font_size / 40
                    font_size = 40  # Use maximum size for default font
        except Exception:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Get text size
        if hasattr(draw, 'textbbox'):
            # For newer Pillow versions
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            # For older Pillow versions
            text_width, text_height = draw.textsize(watermark_text, font=font)
        
        # Create color with opacity
        text_color = (*font_color, int(255 * opacity))
        
        # Handle manual scaling for default font if needed
        if font is ImageFont.load_default() and scale_ratio > 1:
            # Create a larger canvas for the text
            temp_img = Image.new('RGBA', 
                               (int(text_width * scale_ratio), int(text_height * scale_ratio)),
                               (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            temp_draw.text((0, 0), watermark_text, font=font, fill=text_color)
            
            # Use this for the watermark
            text_width = temp_img.width
            text_height = temp_img.height
        
        # Adjust spacing for repeating patterns
        if repeat and scale_factor is not None:
            spacing = int(spacing * (font_size / 40))
        
        if repeat:
            # Create a pattern of watermarks
            if angle != 0:
                # Create a temporary image for the rotated text
                padding = int(max(text_width, text_height) * 0.1)  # 10% padding
                txt_img = Image.new('RGBA', 
                                  (text_width + padding*2, text_height + padding*2), 
                                  (255, 255, 255, 0))
                txt_draw = ImageDraw.Draw(txt_img)
                
                # Draw text at the center of the temp image
                txt_draw.text((padding, padding), watermark_text, font=font, fill=text_color)
                
                # Handle manual scaling for default font if needed
                if font is ImageFont.load_default() and scale_ratio > 1:
                    txt_img.paste(temp_img, (padding, padding), temp_img)
                
                txt_img = txt_img.rotate(angle, expand=1)
                
                # Calculate the pattern size based on spacing and rotated dimensions
                pattern_width = txt_img.width + spacing
                pattern_height = txt_img.height + spacing
                
                # Create a pattern by tiling the rotated text
                for y in range(-pattern_height, img.height + pattern_height, pattern_height):
                    for x in range(-pattern_width, img.width + pattern_width, pattern_width):
                        # Paste with offset to create staggered effect
                        offset_x = x - (y // pattern_height % 2) * (pattern_width // 2)
                        overlay.paste(txt_img, (offset_x, y), txt_img)
            else:
                # Create a grid of watermarks
                for y in range(-text_height, img.height, spacing + text_height):
                    for x in range(-text_width, img.width, spacing + text_width):
                        # Add offset to every other row for a more pleasing pattern
                        offset_x = x + ((y // (spacing + text_height)) % 2) * ((spacing + text_width) // 2)
                        
                        if font is ImageFont.load_default() and scale_ratio > 1:
                            # Use the resized text image
                            overlay.paste(temp_img, (offset_x, y), temp_img)
                        else:
                            # Draw text directly
                            draw.text((offset_x, y), watermark_text, font=font, fill=text_color)
        else:
            # Set position (default to bottom right)
            if position is None:
                position = (img.width - text_width - 20, img.height - text_height - 20)
            
            # Draw the text
            if font is ImageFont.load_default() and scale_ratio > 1:
                # Use the resized text image
                overlay.paste(temp_img, position, temp_img)
            else:
                # Draw text directly
                draw.text(position, watermark_text, font=font, fill=text_color)
        
        # Combine the input image with the overlay
        watermarked = Image.alpha_composite(img, overlay)
        
        # Convert back to RGB for JPEG
        watermarked = watermarked.convert("RGB")
        
        # Save the watermarked image
        watermarked.save(output_path, "JPEG", quality=95)
        print(f"✓ Added watermark to: {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error adding watermark to {input_path}: {str(e)}")
        return False

def generate_output_filename(original_filename, prepend_text=None, append_text=None, 
                     enumerate_files=False, enum_counter=None, enum_padding=0):
    """Generate a new filename with optional prefixes, suffixes, and enumeration."""
    base_name, extension = os.path.splitext(original_filename)
    
    # Start with base name
    new_name = base_name
    
    # Add prefix if specified
    if prepend_text:
        new_name = f"{prepend_text}{new_name}"
    
    # Add enumeration if specified
    if enumerate_files and enum_counter is not None:
        # Format with zero padding if specified
        enum_str = str(enum_counter).zfill(enum_padding)
        new_name = f"{new_name}_{enum_str}"
    
    # Add suffix if specified
    if append_text:
        new_name = f"{new_name}{append_text}"
    
    # Add jpg extension (since all output files are jpg)
    return f"{new_name}.jpg"

def process_image(filename, input_dir, working_dir, output_dir, 
                 max_dimension, copyright_holder, year,
                 watermark_text, watermark_position, watermark_opacity,
                 watermark_font_size, watermark_repeat, watermark_spacing,
                 watermark_angle, watermark_font_color, watermark_scale_factor,
                 prepend_text=None, append_text=None, enumerate_files=False, 
                 enum_counter=None, enum_padding=0):
    """Process a single image through the entire workflow."""
    input_path = os.path.join(input_dir, filename)
    
    # Generate original file paths for working files
    base_name = os.path.splitext(filename)[0]
    working_jpg_path = os.path.join(working_dir, f"{base_name}.jpg")
    resized_jpg_path = os.path.join(working_dir, f"{base_name}_resized.jpg")
    
    # Generate new filename for output
    output_filename = generate_output_filename(
        filename, 
        prepend_text, 
        append_text, 
        enumerate_files, 
        enum_counter, 
        enum_padding
    )
    final_path = os.path.join(output_dir, output_filename)
    
    print(f"\nProcessing: {filename}")
    print(f"Output filename: {output_filename}")
    
    # 1. Convert to JPG
    if not convert_to_jpg(input_path, working_jpg_path):
        return False
    
    # 2. Resize
    if not resize_image(working_jpg_path, resized_jpg_path, max_dimension):
        return False
    
    # 3. Add copyright
    if not add_copyright(resized_jpg_path, copyright_holder, year):
        return False
    
    # 4. Add watermark
    if not add_watermark(resized_jpg_path, final_path, watermark_text, watermark_position,
                       watermark_opacity, watermark_font_size, watermark_repeat,
                       watermark_spacing, watermark_angle, watermark_font_color, watermark_scale_factor):
        return False
    
    # Clean up working files
    if os.path.exists(working_jpg_path):
        os.remove(working_jpg_path)
    if os.path.exists(resized_jpg_path):
        os.remove(resized_jpg_path)
    
    print(f"✓ Completed processing: {filename}")
    return True

def process_batch(input_dir, working_dir, output_dir, 
                 max_dimension, copyright_holder, year,
                 watermark_text, watermark_position, watermark_opacity,
                 watermark_font_size, watermark_repeat, watermark_spacing,
                 watermark_angle, watermark_font_color, watermark_scale_factor,
                 prepend_text=None, append_text=None, enumerate_files=False,
                 enum_start=1, enum_padding=0,
                 file_types=None):
    """Process a batch of images."""
    if file_types is None:
        file_types = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp', '.heic', '.heif']
    
    # Create necessary directories
    create_directories(input_dir, working_dir, output_dir)
    
    # Get all image files in the input directory
    files = [f for f in os.listdir(input_dir) 
            if os.path.isfile(os.path.join(input_dir, f)) and 
            any(f.lower().endswith(ext) for ext in file_types)]
    
    if not files:
        print(f"No image files found in {input_dir}")
        return
    
    print(f"Found {len(files)} images to process")
    
    # Process each file
    success_count = 0
    enum_counter = enum_start
    
    for filename in files:
        # Use enumeration counter if enabled
        current_enum = enum_counter if enumerate_files else None
        
        if process_image(filename, input_dir, working_dir, output_dir,
                       max_dimension, copyright_holder, year,
                       watermark_text, watermark_position, watermark_opacity,
                       watermark_font_size, watermark_repeat, watermark_spacing,
                       watermark_angle, watermark_font_color, watermark_scale_factor,
                       prepend_text, append_text, enumerate_files, current_enum, enum_padding):
            success_count += 1
            # Increment the counter if enumeration is enabled
            if enumerate_files:
                enum_counter += 1
    
    print(f"\nDone! Successfully processed {success_count} out of {len(files)} images.")
    print(f"Output images saved to: {output_dir}")

def parse_color(color_str):
    """Parse a color string in the format 'R,G,B' into a tuple of integers."""
    try:
        r, g, b = map(int, color_str.split(','))
        # Ensure values are within valid range (0-255)
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return (r, g, b)
    except (ValueError, AttributeError):
        raise argparse.ArgumentTypeError("Color must be in the format 'R,G,B' (e.g. '255,0,0' for red)")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Process images for web upload: convert, resize, copyright, and watermark',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Directory options
    parser.add_argument('--input-dir', default='input', help='Directory containing input images')
    parser.add_argument('--working-dir', default='working', help='Directory for temporary working files')
    parser.add_argument('--output-dir', default='output', help='Directory for final processed images')
    
    # Resize options
    parser.add_argument('--max-dimension', type=int, default=DEFAULT_MAX_DIMENSION, 
                      help='Maximum dimension in pixels')
    
    # Copyright options
    parser.add_argument('--copyright-holder', default=DEFAULT_COPYRIGHT_HOLDER, 
                      help='Name of the copyright holder')
    parser.add_argument('--year', type=int, help='Copyright year (defaults to current year)')
    
    # Watermark options
    parser.add_argument('--watermark-text', help='Text to use for watermark (defaults to copyright holder name)')
    parser.add_argument('--watermark-position', nargs=2, type=int, 
                      help='Position of watermark (x y). Defaults to bottom right')
    parser.add_argument('--watermark-opacity', type=float, default=DEFAULT_WATERMARK_OPACITY, 
                      help='Opacity of watermark (0-1)')
    
    # Watermark font options
    size_group = parser.add_argument_group('Watermark Size Options (choose one)')
    size_ex_group = size_group.add_mutually_exclusive_group()
    size_ex_group.add_argument('--watermark-font-size', type=int, default=DEFAULT_WATERMARK_FONT_SIZE, 
                             help='Absolute font size for watermark')
    size_ex_group.add_argument('--watermark-scale', type=float, 
                             help='Scale factor as percentage of image size (1-50)')
    
    # Watermark pattern options
    parser.add_argument('--watermark-repeat', action='store_true', 
                      help='Repeat watermark across the entire image')
    parser.add_argument('--watermark-spacing', type=int, default=100, 
                      help='Spacing between repeated watermarks in pixels')
    parser.add_argument('--watermark-angle', type=int, default=0, 
                      help='Angle of rotation for watermarks (degrees)')
    parser.add_argument('--watermark-font-color', type=parse_color, default='255,255,255', 
                      help='Font color for watermark in R,G,B format (e.g. "255,0,0" for red)')
    
    # Filename modification options
    filename_group = parser.add_argument_group('Filename Modification Options')
    filename_group.add_argument('--prepend-text', help='Text to add at the beginning of filenames')
    filename_group.add_argument('--append-text', help='Text to add at the end of filenames (before extension)')
    filename_group.add_argument('--enumerate', action='store_true', help='Append sequential numbers to filenames')
    filename_group.add_argument('--enum-start', type=int, default=1, 
                              help='Starting number for enumeration (default: 1)')
    filename_group.add_argument('--enum-padding', type=int, default=0, 
                              help='Zero padding for enumeration (e.g., 3 for 001, 002, etc.)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # If watermark text is not specified, use copyright holder
    watermark_text = args.watermark_text if args.watermark_text else args.copyright_holder
    
    # Process the batch
    process_batch(
        args.input_dir,
        args.working_dir,
        args.output_dir,
        args.max_dimension,
        args.copyright_holder,
        args.year,
        watermark_text,
        tuple(args.watermark_position) if args.watermark_position else None,
        args.watermark_opacity,
        args.watermark_font_size,
        args.watermark_repeat,
        args.watermark_spacing,
        args.watermark_angle,
        args.watermark_font_color,
        args.watermark_scale,
        args.prepend_text,
        args.append_text,
        args.enumerate,
        args.enum_start,
        args.enum_padding
    )

if __name__ == "__main__":
    main()