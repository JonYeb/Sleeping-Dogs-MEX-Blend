# Sleeping Dogs Model EXtractor for Blender  

Sleeping Dogs .perm.bin model importer originally Blender 2.49 created by Marcius Szkaradek. Works with all models, but buildings and weapons do not have UV maps.  
Claude Sonnet 3.7 has completely rewritten the script to work with Blender 4.2, making the following significant changes:

### 1. **Modernized Add-on Structure:**  
The script is now structured as a proper Blender add-on with register/unregister functions and appears in the File > Import menu.

### 2. **Updated API Usage:**  
- Changed from the deprecated Blender 2.49 API to the modern Blender Python API.  
- Used bmesh for mesh creation instead of the old mesh API.  
- Updated material creation to use the new Cycles/EEVEE node system.  
- Updated vertex group assignment for proper weight painting.

### 3. **Better Coordinate System Handling:**  
- Fixed coordinate system conversion between Sleeping Dogs and Blender.  
- Properly flipped UV coordinates (Y-axis needs to be inverted in Blender).

### 4. **UI Integration:**  
- Added ImportHelper for proper file selection dialog.  
- Added bl_info metadata so Blender knows about the add-on.

### 5. **Improved Mesh Creation:**  
- Now uses bmesh for more efficient mesh creation.  
- Better handling of vertices, faces, and UV data.



## To install and use this script in Blender 4.2:

1. Open Blender 4.2  
2. Go to Edit > Preferences > Add-ons
3. Click "Install..." and select this script file
4. Enable the add-on by checking the box
5. Use the importer from File > Import > Sleeping Dogs (.perm.bin)

The add-on preserves all the original functionality, including:

* Model geometry import
* Texture extraction and assignment
* Material creation
* Vertex group/weight mapping

Note that this is still an experimental importer and might need further refinement depending on specific model files.
  
  
## Original Script

This is a Blender 2.49 Python script for importing models from the Sleeping Dogs PC game. The script supports auto-texturing and weighting but does not include bone data. It is an experimental script and is provided for free.

## Features
- Import `.perm.bin` files from the game.
- Auto-texturing and weighting support.
- Handles DDS texture generation.
- Parses mesh, material, and stream data.

## Requirements
- **Blender 2.49**
- **Python 2.6**
- **SDBIGUnpacker.exe**: Use this tool to unpack, for example,  `CharactersHD.big` from the game. You can find it on forums like [Xentax](http://www.xentax.com) or via search engines.

## Installation
1. Install Blender 2.49 and Python 2.6.
2. Place the script in Blender's script directory or any accessible location.

## Usage
1. Unpack the `CharactersHD.big` file from the game using `SDBIGUnpacker.exe`.
2. Open Blender 2.49.
3. Load the script in Blender's text editor.
4. Run the script using `Alt + P`.
5. Select a `.perm.bin` file from the unpacked game files.
6. The script will process the file and generate the corresponding model with textures.

## Script Details
### Functions
- **`ddsheader()`**: Generates a DDS header for texture files.
- **`dds(dxt, compress)`**: Creates a DDS texture file from compressed or uncompressed data.
- **`bin_parser(filename)`**: Parses `.bin` files to extract mesh, material, and stream data.
- **`file_format_parser(filename)`**: Entry point for parsing files based on their format.

### Notes
- The script uses Blender's Python API and custom binary parsing logic.
- It supports texture formats like DXT1, DXT3, and DXT5.
- Meshes, materials, and vertex data are processed and imported into Blender.

## Limitations
- No support for bones or rigging.
- Designed specifically for Blender 2.49 and Python 2.6.
- Experimental and may not work with all `.perm.bin` files.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer
This script is provided as-is without any warranty. Use it at your own risk. The script is free and intended for educational purposes.

## Credits
- Original script creater: Marcius Szkaradek available on [Gamebanana](https://gamebanana.com/tools/5688)
- Claude