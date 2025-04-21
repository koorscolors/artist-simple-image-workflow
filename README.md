# Image Workflow Tool

A tool for processing images for web upload: converts formats, resizes, adds copyright metadata, and applies watermarks.

## Installation Requirements

1. **Install Python dependencies:**
   ```
   pip install pillow
   pip install pillow-heif  # For HEIC file support
   ```

2. **Install ExifTool:**
   If you don't already have it, install ExifTool using Homebrew:
   ```
   brew install exiftool
   ```

## Basic Usage

1. Create an `input` directory and place your original images there
2. Run the script with default settings:
   ```
   python image_workflow.py
   ```

The script will:
- Create `working` and `output` directories if they don't exist
- Convert all images to JPG format
- Resize to max 1024px on longest dimension
- Add copyright metadata for "YOURNAME"
- Add a simple watermark with your name
- Place final images in the `output` directory

## Customization Options

### Directories
```
--input-dir DIRECTORY   Directory containing input images (default: input)
--working-dir DIRECTORY Directory for temporary working files (default: working)
--output-dir DIRECTORY  Directory for final processed images (default: output)
```

### Image Size
```
--max-dimension PIXELS  Maximum dimension in pixels (default: 1024)
```

### Copyright
```
--copyright-holder NAME Name of the copyright holder (default: YOURNAME)
--year YEAR             Copyright year (defaults to current year)
```

### Watermark Appearance
```
--watermark-text TEXT   Custom watermark text (defaults to copyright holder name)
--watermark-opacity DECIMAL  Watermark transparency (0-1, default: 0.5)
--watermark-font-size PIXELS Font size for watermark (default: 40)
--watermark-scale PERCENT    Size as percentage of image dimension (1-50)
--watermark-font-color R,G,B Font color in RGB format (default: 255,255,255 for white)
```

### Watermark Placement
```
--watermark-position X Y  Place at specific coordinates
--watermark-repeat        Tile watermark across entire image
--watermark-spacing PIXELS  Spacing between repeated watermarks (default: 100)
--watermark-angle DEGREES   Rotate watermark (default: 0)
```

### Filename Modification
```
--prepend-text TEXT     Text to add at the beginning of filenames
--append-text TEXT      Text to add at the end of filenames (before extension)
--enumerate             Append sequential numbers to filenames
--enum-start NUMBER     Starting number for enumeration (default: 1)
--enum-padding NUMBER   Zero padding for enumeration (e.g., 3 for 001, 002, etc.)
```

## Example Commands

### Basic with larger size
```
python image_workflow.py --max-dimension 1500
```

### Subtle watermark
```
python image_workflow.py --watermark-opacity 0.2 --watermark-scale 3
```

### Pattern watermark
```
python image_workflow.py --watermark-repeat --watermark-angle 30 --watermark-text "© YOURNAME"
```

### Custom workflow
```
python image_workflow.py --input-dir raw-photos --output-dir web-ready --max-dimension 2000 --watermark-text "© YOURNAME" --watermark-scale 5 --watermark-font-color 255,255,0 --watermark-repeat
```

### Filename modification examples

#### Add prefix to filenames
```
python image_workflow.py --prepend-text "vacation_"
```
Result: image.jpg → vacation_image.jpg

#### Add suffix to filenames
```
python image_workflow.py --append-text "_edited"
```
Result: image.jpg → image_edited.jpg

#### Add sequential numbering
```
python image_workflow.py --enumerate
```
Result: beach.jpg → beach_1.jpg, sunset.jpg → sunset_2.jpg

#### Numbered series with zero padding
```
python image_workflow.py --enumerate --enum-start 1 --enum-padding 3
```
Result: beach.jpg → beach_001.jpg, sunset.jpg → sunset_002.jpg

#### Combining naming options
```
python image_workflow.py --prepend-text "hawaii_" --append-text "_trip" --enumerate --enum-padding 2
```
Result: beach.jpg → hawaii_beach_01_trip.jpg

## Supported File Types

The script supports various image formats including:
- JPG/JPEG
- PNG
- HEIC/HEIF (requires pillow-heif module)
- TIFF/TIF
- GIF
- BMP
