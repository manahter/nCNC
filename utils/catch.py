import bpy
from mathutils import Vector


def catch_update(scene, desgraph):
    for item in scene.ncnc_pr_objects.items:
        if not item.obj:
            continue
        self = item.obj.ncnc_pr_objectconfigs
        obj = self.id_data

        if obj.update_from_editmode() or obj.update_tag() or \
                self.last_loc != obj.location or self.last_rot != Vector(obj.rotation_euler) or \
                self.last_sca != obj.scale:
            self.is_updated = True
            self.last_loc = obj.location.copy()
            self.last_rot = Vector(obj.rotation_euler)
            self.last_sca = obj.scale.copy()


def catch_start():
    posts = bpy.app.handlers.depsgraph_update_post
    if catch_update not in posts:
        bpy.app.handlers.depsgraph_update_post.append(catch_update)


def catch_stop():
    posts = bpy.app.handlers.depsgraph_update_post
    if catch_update in posts:
        posts.remove(catch_update)