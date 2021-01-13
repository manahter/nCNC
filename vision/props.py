import bpy
import blf
import bgl
import gpu
import time
from bpy.props import EnumProperty, BoolProperty, PointerProperty, IntProperty, FloatProperty, FloatVectorProperty
from bpy.types import PropertyGroup, Scene
from gpu_extras.batch import batch_for_shader

gcode_batchs = {}
gcode_shaders = {}


def handles() -> dict:
    keycode = "ncnc_pr_vision.handles"
    ns = bpy.app.driver_namespace

    if ns.get(keycode):
        return ns.get(keycode)

    ns[keycode] = {}
    return ns[keycode]


def handle_remove(keycode) -> handles:
    handle_list = handles()
    if handle_list.get(keycode):
        bpy.types.SpaceView3D.draw_handler_remove(handle_list.pop(keycode), 'WINDOW')

    return handle_list


def register_check(context) -> bool:
    return hasattr(context.scene, "ncnc_pr_machine") and hasattr(context.scene, "ncnc_pr_vision")


def gcode_callback(self, context):
    if not register_check(context):
        return

    pr_txt = context.scene.ncnc_pr_texts.active_text
    if not pr_txt:
        return

    # for transparent
    bgl.glEnable(bgl.GL_BLEND)

    if not self.infront:
        bgl.glEnable(bgl.GL_DEPTH_TEST)

    pr_txt = pr_txt.ncnc_pr_text
    if pr_txt.event:
        gcode_batchs["p"] = batch_for_shader(gcode_shaders["p"],
                                             'POINTS',
                                             {"pos": pr_txt.get_points()})
        for i in range(4):
            gcode_batchs[i] = batch_for_shader(gcode_shaders[i],
                                               'LINES',
                                               {"pos": pr_txt.get_lines(i)})
        if context.area:
            context.area.tag_redraw()

    if pr_txt.event_selected:
        gcode_batchs["c"] = batch_for_shader(gcode_shaders["c"],
                                             'LINES',
                                             {"pos": pr_txt.get_selected()})

    for i, color, thick, show in [(0, self.color_g0, self.thick_g0, self.g0),
                                  (1, self.color_g1, self.thick_g1, self.g1),
                                  (2, self.color_g2, self.thick_g2, self.g2),
                                  (3, self.color_g3, self.thick_g3, self.g3),
                                  ("p", self.color_gp, self.thick_gp, self.gp),
                                  ("c", self.color_gc, self.thick_gc, self.gc)
                                  ]:
        if not show:
            continue
        if i == "p":
            bgl.glPointSize(thick)
        else:
            bgl.glLineWidth(thick)
        gcode_shaders[i].bind()
        gcode_shaders[i].uniform_float("color", color)
        gcode_batchs[i].draw(gcode_shaders[i])

    # for transparent
    bgl.glDisable(bgl.GL_BLEND)

    if not self.infront:
        bgl.glDepthMask(bgl.GL_TRUE)


def dash_callback(self, context):
    if not register_check(context):
        return
    # Draw text to indicate that draw mode is active
    pr_mac = context.scene.ncnc_pr_machine
    pos = pr_mac.mpos if pr_mac.pos_type == "mpos" else pr_mac.wpos

    blf_pos_y = 10

    pos_type = 'WPos' if pr_mac.pos_type == 'wpos' else 'MPos'
    for prop, text, val in [
        ("pos", pos_type, f"X {round(pos[0], 2)}   Y {round(pos[1], 2)}   Z {round(pos[2], 2)}"),
        ("buffer", "Buffer", f"{pr_mac.buffer},{pr_mac.bufwer}"),
        ("spindle", "Spindle", pr_mac.spindle),
        ("feed", "Feed", pr_mac.feed),
        ("status", "Status", pr_mac.status),
    ]:

        if not eval(f"self.{prop}"):
            continue

        size = eval(f"self.thick_{prop}")
        blf.color(0, *eval(f"self.color_{prop}"))
        blf.size(0, size, 64)
        blf.position(0, 10, blf_pos_y, 0)
        blf.draw(0, text)

        blf.position(0, size * 5, blf_pos_y, 0)
        blf.draw(0, f"{val}")
        blf_pos_y += size * 1.5


mill_delay = .5
mill_last_time = 0
mill_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
mill_batch = None


def mill_callback(self, context):
    if not register_check(context):
        return

    global mill_delay, mill_last_time, mill_shader, mill_batch
    if time.time() - mill_last_time > mill_delay:
        pr_mac = context.scene.ncnc_pr_machine
        pos = pr_mac.mpos if pr_mac.pos_type == "mpos" else pr_mac.wpos

        mill_last_time = time.time()
        mill_delay = .1 if pr_mac.status in ("JOG", "RUN") else .5
        mill_batch = batch_for_shader(mill_shader,
                                      'LINES',
                                      {"pos": mill_lines(*pos)})

    # for transparent
    bgl.glEnable(bgl.GL_BLEND)

    if not self.infront:
        bgl.glEnable(bgl.GL_DEPTH_TEST)

    bgl.glLineWidth(self.thick_mill)
    mill_shader.bind()
    mill_shader.uniform_float("color", self.color_mill)
    mill_batch.draw(mill_shader)

    # for transparent
    bgl.glDisable(bgl.GL_BLEND)

    if not self.infront:
        bgl.glDepthMask(bgl.GL_TRUE)


def mill_lines(x, y, z):
    s = 1.5
    s2 = s * 5
    return [
        (x, y, z), (x + s, y + s, z + s2),
        (x, y, z), (x - s, y - s, z + s2),
        (x, y, z), (x + s, y - s, z + s2),
        (x, y, z), (x - s, y + s, z + s2),
        (x - s, y - s, z + s2), (x - s, y + s, z + s2),
        (x - s, y + s, z + s2), (x + s, y + s, z + s2),
        (x + s, y - s, z + s2), (x + s, y + s, z + s2),
        (x - s, y - s, z + s2), (x + s, y - s, z + s2),
        (x, y, z + s2), (x, y, z + s2 * 2)
    ]


class NCNC_PR_Vision(PropertyGroup):

    # ##########################
    # ########### Layout Methods
    def prop_bool(self, layout, prop: str):
        return layout.prop(self, prop,
                           emboss=False,
                           text="",
                           icon=("RESTRICT_VIEW_OFF" if eval(f"self.{prop}") else "RESTRICT_VIEW_ON"), )

    def prop_theme(self, layout, prop: str, text=""):
        row = layout.row(align=True)
        self.prop_bool(row, prop)
        row.label(text=text)
        col = row.column(align=True)
        col.prop(self, f"color_{prop}", text="")
        col.prop(self, f"thick_{prop}", text="")
        return row

    # ##########################
    # ################## Presets
    def update_presets(self, context):
        prs = {"def": (("g0", (.073, .07, .07, 0.4), 1),
                       ("g1", (.8, .5, .3, 0.5), 2),
                       ("g2", (1, .45, .3, 0.5), 2),
                       ("g3", (1, .45, .3, 0.5), 2),
                       ("gp", (1, .6, .2, 1), 1.5),
                       ("dash", (1, 1, 1, .9), 14),
                       ("status", (1, .66, .45, .9), 14),
                       ("pos", (1, .66, .45, .9), 14),
                       ("mill", (.9, .6, .45, .9), 3),
                       ),
               "blu": (("gcode", (0, .44, .77, 0.5), 1),
                       ("g0", (.2, .3, .5, .5), 1),
                       ("gp", (0, .1, .2, 1), 2),
                       ("dash", (.5, .7, 1, .9), 14),
                       ("mill", (0, .5, .8, .9), 3),
                       ),
               "bla": (("gcode", (0, 0, 0, 1), 1),
                       ("g0", (0, 0, 0, 1), 1),
                       ("gp", (.3, .3, .3, 1), 2),
                       ("dash", (0, 0, 0, 1), 14),
                       ("mill", (0, 0, .1, 1), 3),
                       ),
               "whi": (("gcode", (1, 1, 1, 1), 2),
                       ("g0", (1, 1, 1, 1), 1),
                       ("gp", (.4, .4, .4, 1), 2),
                       ("dash", (1, 1, 1, .9), 14),
                       ("mill", (.7, .8, 1, 1), 3),
                       ),
               "bej": (("g0", (.073, .07, .07, 0.5), 1),
                       ("g1", (.8, .5, .3, 0.5), 2),
                       ("g2", (1, .45, .3, 0.5), 2),
                       ("g3", (1, .45, .3, 0.5), 2),
                       ("gp", (1, .6, .2, 1), 1.5),
                       ("dash", (1, 1, 1, .9), 14),
                       ("status", (1, .66, .45, .9), 14),
                       ("pos", (1, .66, .45, .9), 14),
                       ("mill", (.9, .6, .45, .9), 3),
                       ),
               "cfl": (("g0", (.5, .5, .5, 0.5), 1),
                       ("g1", (0, .44, .77, 0.5), 2),
                       ("g2", (.77, .2, .3, 0.5), 2),
                       ("g3", (.3, .77, .2, 0.5), 2),
                       ("gp", (.1, .1, .1, 1), 2),
                       ("dash", (1, 1, 1, .9), 14),
                       ("status", (1, .8, .2, .9), 14),
                       ("pos", (1, .8, .2, .9), 14),
                       ("mill", (.9, .25, .1, .9), 3),
                       ),
               }

        for key, color, thick in prs[self.presets]:
            exec(f"self.color_{key} = {color}")
            exec(f"self.thick_{key} = {thick}")

        # Save to last preset
        addon = bpy.context.preferences.addons.get(__name__)
        if addon:
            addon.preferences.last_preset = self.presets
            bpy.context.preferences.use_preferences_save = True

    presets: EnumProperty(
        items=[("def", "Default", ""),
               ("bla", "Black", ""),
               ("whi", "White", ""),
               ("blu", "Blue", ""),
               ("bej", "Beige", ""),
               ("cfl", "Colorful", ""),
               ],
        name="Presets",
        update=update_presets
    )

    infront: BoolProperty(
        name="In front",
        description="Make the G code lines draw in front of others",
        default=False
    )

    # ##########################
    # #################### DASH
    def update_dash(self, context):
        keycode = "DASH"
        _handls = handle_remove(keycode)
        if self.dash:
            _handls[keycode] = bpy.types.SpaceView3D.draw_handler_add(dash_callback,
                                                                      (self, context),
                                                                      "WINDOW",
                                                                      "POST_PIXEL")

    dash: BoolProperty(
        name="Machine Dashboard",
        description="Show/Hide in Viewport",
        default=False,
        update=update_dash
    )
    feed: BoolProperty(
        name="Feed on Dashboard",
        description="Show/Hide in Viewport",
        default=True
    )
    spindle: BoolProperty(
        name="Spindle on Dashboard",
        description="Show/Hide in Viewport",
        default=True
    )
    buffer: BoolProperty(
        name="Buffer on Dashboard",
        description="Show/Hide in Viewport",
        default=True
    )
    status: BoolProperty(
        name="Status on Dashboard",
        description="Show/Hide in Viewport",
        default=True
    )
    pos: BoolProperty(
        name="Position on Dashboard",
        description="Show/Hide in Viewport",
        default=True
    )

    def update_color_dash(self, context):
        for key in ("feed", "spindle", "buffer", "status", "pos"):
            self[f"color_{key}"] = self.color_dash

    color_dash: FloatVectorProperty(
        name='Dashboard',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, 1, 1, 0.9),
        update=update_color_dash
    )
    color_feed: FloatVectorProperty(
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, 1, 1, 0.9)
    )
    color_spindle: FloatVectorProperty(
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, 1, 1, 0.9)
    )
    color_buffer: FloatVectorProperty(
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, 1, 1, 0.9)
    )
    color_status: FloatVectorProperty(
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, .66, .45, .9)
    )
    color_pos: FloatVectorProperty(
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, .66, .45, .9)
    )

    def update_thick_dash(self, context):
        for key in ("feed", "spindle", "buffer", "status", "pos"):
            self[f"thick_{key}"] = self.thick_dash

    thick_dash: IntProperty(default=14, min=8, max=20, description="Font Size", update=update_thick_dash)
    thick_feed: IntProperty(default=14, min=8, max=20, description="Font Size")
    thick_spindle: IntProperty(default=14, min=8, max=20, description="Font Size")
    thick_buffer: IntProperty(default=14, min=8, max=20, description="Font Size")
    thick_status: IntProperty(default=14, min=8, max=20, description="Font Size")
    thick_pos: IntProperty(default=14, min=8, max=20, description="Font Size")

    # ##########################
    # #################### GCODE
    def update_gcode(self, context):
        keycode = "GCODE"
        handles = handle_remove(keycode)

        pr_act = context.scene.ncnc_pr_texts.active_text
        if not pr_act:
            return
        pr_txt = pr_act.ncnc_pr_text

        if self.gcode:
            # For different shader / color
            # https://docs.blender.org/api/current/gpu.html#mesh-with-random-vertex-colors

            # Dotted Line For G0
            # https://docs.blender.org/api/current/gpu.html#custom-shader-for-dotted-3d-line

            for i in range(4):
                gcode_shaders[i] = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
                gcode_batchs[i] = batch_for_shader(gcode_shaders[i],
                                                   'LINES',
                                                   {"pos": pr_txt.get_lines(i)}
                                                   # {"pos": []}
                                                   )

            gcode_shaders["p"] = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            gcode_batchs["p"] = batch_for_shader(gcode_shaders["p"],
                                                 'POINTS',
                                                 {"pos": pr_txt.get_points()}
                                                 # {"pos": []}
                                                 )

            gcode_shaders["c"] = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            gcode_batchs["c"] = batch_for_shader(gcode_shaders["c"],
                                                 'LINES',
                                                 {"pos": []}
                                                 )

            handles[keycode] = bpy.types.SpaceView3D.draw_handler_add(gcode_callback,
                                                                      (self, context),
                                                                      "WINDOW",
                                                                      "POST_VIEW")

    gcode: BoolProperty(default=True, update=update_gcode)
    gp: BoolProperty(default=True)
    gc: BoolProperty(default=True)
    g0: BoolProperty(default=True)
    g1: BoolProperty(default=True)
    g2: BoolProperty(default=True)
    g3: BoolProperty(default=True)

    def update_thick_gcode(self, context):
        for key in (0, 1, 2, 3, "p"):
            self[f"thick_g{key}"] = self.thick_gcode

    thick_gcode: FloatProperty(name="General", default=2.0, min=0, max=10, description="Line Thickness",
                               update=update_thick_gcode)
    thick_gp: FloatProperty(name="Point", default=1.5, min=0, max=10, description="Point Thickness")
    thick_gc: FloatProperty(name="Current", default=3.0, min=0, max=10, description="Line Thickness")
    thick_g0: FloatProperty(name="Rapid", default=1.0, min=0, max=10, description="Line Thickness")
    thick_g1: FloatProperty(name="Linear", default=2.0, min=0, max=10, description="Line Thickness")
    thick_g2: FloatProperty(name="Arc CW", default=2.0, min=0, max=10, description="Line Thickness")
    thick_g3: FloatProperty(name="Arc CCW", default=2.0, min=0, max=10, description="Line Thickness")

    def update_color_gcode(self, context):
        for key in (0, 1, 2, 3, "p"):
            self[f"color_g{key}"] = self.color_gcode

    color_gcode: FloatVectorProperty(
        name='General',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(.5, .5, .5, .5),
        update=update_color_gcode
    )
    color_gp: FloatVectorProperty(
        name='Point Color',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, .6, .2, 1)
    )
    color_gc: FloatVectorProperty(
        name='Current Code Line Color',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, 0, 1, .5)
    )
    color_g0: FloatVectorProperty(
        name='Rapid Color',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(.073, .07, .07, 0.4)
    )
    color_g1: FloatVectorProperty(
        name='Linear Color',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        # default=(0.7, 0.5, 0.2, 0.5)
        default=(.8, .5, .3, 0.5)
    )
    color_g2: FloatVectorProperty(
        name='Arc Color CW',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, .45, .3, 0.5)
    )
    color_g3: FloatVectorProperty(
        name='Arc Color CCW',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(1, .45, .3, 0.5)
    )

    # ##########################
    # #################### MILL
    def update_mill(self, context):
        keycode = "MILL"
        handles = handle_remove(keycode)
        if self.mill:
            pr_mac = context.scene.ncnc_pr_machine
            pos = pr_mac.mpos if pr_mac.pos_type == "mpos" else pr_mac.wpos

            global mill_shader, mill_batch
            mill_batch = batch_for_shader(mill_shader,
                                          'LINES',
                                          {"pos": mill_lines(*pos)})

            handles[keycode] = bpy.types.SpaceView3D.draw_handler_add(mill_callback,
                                                                      (self, context),
                                                                      "WINDOW",
                                                                      "POST_VIEW")

    mill: BoolProperty(
        name="Machine Mill",
        description="Show/Hide in Viewport",
        default=False,
        update=update_mill
    )
    color_mill: FloatVectorProperty(
        name='Arc Color CCW',
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(.9, .6, .45, .9)
    )

    thick_mill: FloatProperty(name="Arc CCW", default=3.0, min=0, max=10, description="Line Thickness")

    @classmethod
    def register(cls):
        Scene.ncnc_pr_vision = PointerProperty(
            name="NCNC_PR_Vision Name",
            description="NCNC_PR_Vision Description",
            type=cls)

        # bpy.context.scene.ncnc_pr_vision.presets = pf.last_preset

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_vision
        for keycode in ("DASH", "MILL", "GCODE"):
            handle_remove(keycode)

