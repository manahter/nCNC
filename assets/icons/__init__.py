import os
import bpy.utils.previews

icons = None


def icons_register():
    global icons

    icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__))

    for icon_full_name in os.listdir(icons_dir):
        if not icon_full_name.endswith(".png"):
            continue
        icon_name = icon_full_name[:-4]
        icons.load(icon_name, os.path.join(icons_dir, icon_full_name), 'IMAGE')


def icons_unregister():
    global icons
    bpy.utils.previews.remove(icons)

