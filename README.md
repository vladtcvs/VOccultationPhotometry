# Contents

* [Description](#description)
    * [Purpose](#purpose)
    * [UI description](#ui-description)
        * [Detect tracks panel](#detect-tracks-panel)
        * [Reference track panel](#reference-track-panel)
        * [Occultation track panel](#occultation-track-panel)
* [Usage](#usage)
* [Installation](#installation)
    * [Installation via pip](#install-via-pip)
    * [Using pre-built binary](#using-pre-built-binary)
* [Build](#build)
* [License](#license)

# Description

## Purpose

Tool purpose is analyzing asteroids star occultations captured by star drift method.

## UI description

App hase 3 panels:
* Detect tracks panel
* Reference track panel
* Occultation track panel

### Detect tracks panel

This panel is intended for specifying reference and occultation tracks. It has elements:

1. Image area - the whole original image
2. "Auto detect references" button - automatically detect reference tracks
3. Buttons left, right, top, bottom - for moving active track (occultation or reference)
4. "Occultation track" button - select occultation track as active
5. List of buttons for selecting corresponding reference track as active
6. List of buttons with "X" for removing corresponding reference track
7. "New reference" button - for initializing new reference track
8. "W" and "H" input - for specification dimensions of reference and occultation track frames

### Reference track panel

1. Left top image - mean reference track image. Mean of all reference tracks
2. Left bottom image - linearized mean reference track. Contains green markers for choosing active area for building profile plot
3. Profile plot
4. "Track orientation" selector - used for longest track axis selection. "Automatic" by default
5. "Reference track smooth" - reference track curve smoothed after detection for noise reduction
6. "Reference track half width" - half width of extracted image along track curve
7. "Reference track half width (used for profile)" - how much of extracted image use for profile building
8. "Build mean reference track" button - recalculate mean reference track
9. "Save reference profile" - save profile as csv file
10. "Save reference slices" - save linealized mean reference track as image

### Occultation track panel

1. Left top image - occultation track image
2. Left bottom image - linearized occultation track. Contains green markers for choosing active area for building profile plot
3. Profile plot
4. "Occultation track half width" - half width of extracted image along track curve
5. "Occultation track half width (used for profile)" - how much of extracted image use for profile building
6. "Build occultation track" button - recalculate occultation track
7. "Save occultation profile" - save profile as csv file
8. "Save occultation slices" - save linealized occultation track as image

# Usage

1. Load image with occultation track
2. Press "Auto detect references"
3. If reference tracks detection is not perfect:
    1. adjust reference tracks positions by selecting them and moving horizontally and vertically
    2. adjust reference tracks size by adjusting width and height
    3. Add or remove reference tracks. But there should be at least 1 reference track
    4. For tracks which goes close to 45 degrees, may be useful to manually select orientation vertical or horizontal by switch on "Reference track" panel
4. Move occultation track position to match occultation track and line displayed in occultation track frame (fully green one)
5. Switch to occultation track panel
6. Adjust "Track half width (used for profile)" as minimum as possible to select only actual track pixels. Use green markers on left bottom image
7. If needed, move occultation track frame to ensure that linearized track in left bottom is centered between green markers
8. Press "Save occultation profile" to store displayed track profile as csv file
9. Press "Save occultation slices" to save linearized occultation track as image for further processing

# Installation

## Install via pip

This way is applicable if you have python installed to your system.

### Linux & Mac

1. Make sure you have python installed on your system, version 3.11 or newer
2. Run in terminal:
```sh
python -m pip install voccultation
```
3. Run in terminal to launch application:
```sh
voccultation
```

**Note:** in some Linux distro there is no `python` command, try specify `python3`


### Windows

1. Open Microsoft store and install python 3.14
2. Open command line (cmd.exe) and enter
```
python3.14 -m pip install voccultation
```
3. App is insalled to location `C:\Users\%USERNAME%\AppData\Local\Python\pythoncore-3.14-64\Scripts\voccultation.exe`
4. Create desktop shortcut (right click -> Send to -> Desktop)

## Using pre-built binary

This way is applicable for windows if you don't have python installed to your system.

1. Open releases page: https://github.com/vladtcvs/VOccultation/releases
2. Choose latest release
3. Expand "Assets"
4. Download `voccultation-windows.zip`
5. Extract archive
6. Run voccultation.bat

# Build

1. Create venv for package:
    ```sh
    python3 -m venv ~/voccultation-venv
    source ~/voccultation-venv/bin/activate
    ```

2. Run build:
    ```sh
    python3 -m pip install .
    ```

# License

[GNU GPL v3](LICENSE.txt)
