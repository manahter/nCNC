import bpy
from bpy.props import IntProperty, BoolProperty, PointerProperty, CollectionProperty
from bpy.types import PropertyGroup, Scene

from .configs.props import NCNC_PR_ObjectConfigs


class NCNC_PR_Objects(PropertyGroup):
    def add_item(self, obj):
        for j, i in enumerate(self.items):
            if obj == i.obj:
                return

        item = self.items.add()
        item.obj = obj
        self.active_item_index = len(self.items) - 1

    def remove_item(self, obj):
        for j, i in enumerate(self.items):
            if obj == i.obj:
                self.items.remove(j)
                break

    def update_active_item_index(self, context):
        if not bpy.ops.object.select_all.poll():
            return
        bpy.ops.object.select_all(action='DESELECT')
        obj = self.items[self.active_item_index].obj

        if obj.name not in context.scene.objects.keys():
            self.items.remove(self.active_item_index)
            return

        obj.select_set(True)
        context.view_layer.objects.active = obj

    items: CollectionProperty(
        type=NCNC_PR_ObjectConfigs,
        name="Objects",
        description="All Object Items Collection",
    )
    active_item_index: IntProperty(
        name="Active Item",
        default=-1,
        description="Selected object index in Collection",
        update=update_active_item_index,
    )

    def hide_in_viewport(self, context):
        for i in self.items:
            if i.obj:
                i.obj.id_data.hide_viewport = self.hide_in_viewport

    hide_in_viewport: BoolProperty(
        name="Hide in Viewport",
        default=False,
        update=hide_in_viewport
    )

    @classmethod
    def register(cls):
        Scene.ncnc_pr_objects = PointerProperty(
            name="NCNC_PR_Objects Name",
            description="NCNC_PR_Objects Description",
            type=cls)

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_objects
