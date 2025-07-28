# Icon Creation Instructions

## Current Status
An SVG icon has been created (`icon.svg`) that shows a microphone with sound waves, representing the audio generation capabilities of Higgs Audio V2.

## Converting to PNG
To create the required `icon.png` file (512x512px), you can:

### Option 1: Online Conversion
1. Open `icon.svg` in any web browser
2. Take a screenshot or use browser developer tools to save as PNG
3. Resize to 512x512px using any image editor
4. Save as `icon.png`

### Option 2: Command Line (if you have ImageMagick)
```bash
magick icon.svg -resize 512x512 icon.png
```

### Option 3: Use Online SVG to PNG Converter
1. Upload `icon.svg` to any online SVG to PNG converter
2. Set output size to 512x512px
3. Download and save as `icon.png`

### Option 4: Create Custom Icon
If you prefer a different design:
1. Create a 512x512px PNG image
2. Use audio/microphone/sound wave themes
3. Use blue (#2563eb) as the primary color to match the design
4. Save as `icon.png`

## Design Elements
The current SVG icon includes:
- Blue circular background
- White microphone with grille lines
- Sound waves on both sides
- Audio waveform at the bottom
- Microphone stand

This represents the text-to-speech and voice generation capabilities of Higgs Audio V2.