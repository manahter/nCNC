![Cover](https://user-images.githubusercontent.com/73780835/98469456-cff8f880-21f0-11eb-9431-a0b6cd2e5d80.png)
# Blender Add on - nCNC - CAM / CAD
[![Blender Addon](https://img.shields.io/badge/Blender-2.9-orange?&style=flat&logo=blender&logoColor=white)](https://www.blender.org/download/releases/2-90/)
[![Blender Addon](https://img.shields.io/badge/Addon-nCNC-orange)](https://github.com/manahter/nCNC)
[![Blender Addon](https://img.shields.io/github/v/release/manahter/nCNC)](https://github.com/manahter/nCNC)
[![Blender Addon](https://img.shields.io/github/release-date-pre/manahter/nCNC)](https://github.com/manahter/nCNC)
[![Blender Addon](https://img.shields.io/github/license/manahter/nCNC)](https://github.com/manahter/nCNC/blob/main/LICENSE)
![GitHub last commit](https://img.shields.io/github/last-commit/manahter/nCNC)

This add-on; Allows you to control the CNC machine and generate G-code to milling.

* _Currently only curves can be converted (will be developed for 3D objects as well)_
* _This add-on has been tested with GRBL v1.1 - CNC 3018._
* _This add-on under development._

## Table of contents
* [General Features](#General-Features)
* [Installation](#Installation)
* [Usage](#Usage)
* [Feature Done](#Feature-Done)
* [License](#License)
* [Support](#Support)


## Installation
1. Before [download](https://github.com/manahter/nCNC/releases/latest/download/nCNC.zip).
2. Blender: Edit -> Preferences -> Add-ons -> Install.
3. Select the downloaded file and you're good to go.
* Or see in detail on [wiki](https://github.com/manahter/nCNC/wiki/Installation)

## General Features
* G Code Viewer
* G Code Converter
* G Code Sender
* CNC Controller
* CNC Configurator

## Usage
- For detailed information about the use of the add-on;
  * [Wiki](https://github.com/manahter/nCNC/wiki)
  * [Youtube](https://www.youtube.com/watch?v=mPNej4vpJvc&list=PLEhXwZnmfmZUFy7qmVqo_J2PuXGDBswYh)

[![Jog](https://user-images.githubusercontent.com/73780835/98465377-bef0bd00-21d9-11eb-8c31-b40152f22837.gif)](https://youtu.be/6yTcJT8kL2c?t=286 "go Youtube Video")

## Feature Done
### v0.6.6
* Added, pocket engrave on the surface
* Pocket carving range can be changed.
* Pockets can also be created on inclined objects.
* Code can be generated without converting the text object to a curve.

### v0.6.5
* Improvements have been made to the code.
* Added progress bar to converting process for included objects.

### v0.6.4
* Bug fixed when closing the main 3D viewport
* Bug fixed object duplication when modifying Toolpath Configs.
* Added, G-Code conversion progress bar
* Changed, G-Code reader progress bar position
* Added 'auto convert' button. Not fully stable. Continuing to improve.

### v0.6.3
* The feature of creating a circle in a single line has been improved.
* G2-G3 code cancellation feature has been added in toolpath configs. (Curve/Line, reverse button)
as Line: Let it consist of lines only. Don't use G2-G3 code.
as Curve: Use curves and lines. Use all, including G2-G3.
* Added radius R value reading feature in G code.
* [Click for details](https://github.com/manahter/nCNC/releases/tag/v0.6.3)

### v0.6.2
* Fixed Modal bug
* Fixed the bug that occurred while deactivating and activating the add-on while the connection was open.

### v0.6.1
* Add Scene nCNC Settings Panel
* Add Import / Export GCode
* Add Gcode Analyse Panel
* Add CNC Machine Tools
  * Add Connection
  * Add Communication
  * Add Machine ( Status, Modes, Configs )
  * Add Jog Controller
* Add Vision Tools
  * Add Display GCode
  * Add Mill in 3D Viewport
  * Add Dashboard in Viewport
  * Add Change vision draws; show/hide, color, line size, 
  * Add Draw to Selected Gcode line

## License
nCNC uses the MIT license. See [LICENSE](https://github.com/manahter/nCNC/blob/main/LICENSE) for more details.

## Support
| [![iyzipay Method](https://www.iyzico.com/assets/images/content/logo.svg)](https://iyzi.link/AFuRiw)  | [![Amazon Gift](https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Amazon.com-Logo.svg/300px-Amazon.com-Logo.svg.png)](https://www.amazon.com/hz/wishlist/ls/1FK123QWD8L6T?ref_=wl_share)   |
|:------------:|:---------------:|
| You can support my work with a donation through iyzico. Doing so means I'll be able to spend more time working on open source and creating content. | Send a gift. If donations don't feel like the best way to support my work, consider sending me a gift from my wish list. I regularly update it with things I'd appreciate (please include a note so I know who sent it). |
| [![iyzipay Method](https://img.shields.io/badge/-donate-1e64ff?style=for-the-badge)](https://iyzi.link/AFvxng)| [![Amazon Gift](https://img.shields.io/badge/-Send_Gift-fe9a2f?style=for-the-badge)](https://www.amazon.com/hz/wishlist/ls/1FK123QWD8L6T?ref_=wl_share) |
