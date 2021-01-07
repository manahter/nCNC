# -*- coding:utf-8 -*-
import os
import bpy

from bpy.types import AddonPreferences
from bpy.props import StringProperty
from bpy.types import Operator

bl_info = {
    "name": "nCNC",
    "description": "CNC Controls, G code operations",
    "author": "Manahter",
    "version": (1, 0, 1),
    "blender": (2, 91, 0),
    "location": "View3D",
    "category": "Generic",
    "warning": "Under development. Nothing is guaranteed",
    "doc_url": "https://github.com/manahter/nCNC/wiki",
    "tracker_url": "https://github.com/manahter/nCNC/issues"
}


# TODO:
"""
Eklenecek Özellikler;
    * Kod çizgileri görününce, included objeler görünmesin. (Vision'dan bu özellik aktifleştirilebilir olur)
    * Sadece belli bir objenin yollarını (kodunu) göster/gizle özelliği ekle
    * Koddaki hatalı kısımların çizgisi kırmızı olacak şekilde düzenle. Vision'a da eklenebilir
    * Kod Çizgilerinin ucuna yönünü belirten bir ok koy:
        https://github.com/blender/blender/blob/6c9178b183f5267e07a6c55497b6d496e468a709/release/scripts/templates_py/gizmo_custom_geometry.py
        https://blender.stackexchange.com/a/148300

Yapılamayanlar;
    * Kod satırları için TextEditör benzeri ayrı bir alan oluşturulabilir mi araştır.
        - Özelleştirilmiş Yeni Edtör alanı oluşturulamıyor. Node Editor gib alanlar ancak oluşturulabiliyor.
"""


class NCNC_Prefs(AddonPreferences):
    # This must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    last_preset: StringProperty()

# my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
# icons = bpy.utils.previews.new()
# icons.load("my_icon", os.path.join(my_icons_dir, "auto.png"), 'IMAGE')
# row.prop( ... icon_value=icons["my_icon"].icon_id ...)


"""
    Header -> _HT_
    Menu -> _MT_
    Operator -> _OT_
    Panel -> _PT_
    UIList -> _UL_
"""


from .assets.icons import icons_register, icons_unregister

icons_register()

from .import registerer
from .import head
from .import gcode
from .import machine
from .import scene
from .import vision
from .import objects
from .utils.catch import catch_stop


class NCNC_OT_Empty(Operator):
    bl_idname = "ncnc.empty"
    bl_label = ""
    bl_description = ""
    bl_options = {'REGISTER'}

    def invoke(self, context, event=None):
        return {"CANCELLED"}


registerer.classes.insert(0, NCNC_Prefs)
registerer.classes.insert(1, NCNC_OT_Empty)


def register():
    for i in registerer.classes:
        bpy.utils.register_class(i)


def unregister():
    icons_unregister()
    for i in registerer.classes[::-1]:
        bpy.utils.unregister_class(i)
    catch_stop()


if __name__ == "__main__":
    register()
