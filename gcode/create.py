import time
import bpy
from bpy.types import Operator, PropertyGroup, Scene
from bpy.props import BoolProperty, IntProperty, FloatVectorProperty, PointerProperty

from nCNC.utils.catch import catch_start


class NCNC_PR_GCodeCreate(PropertyGroup):
    isrun = []

    loading: IntProperty(
        name="Loading...",
        subtype="PERCENTAGE",
        default=0,
        min=0,
        max=100
    )

    def update_overwrite(self, context):
        if not self.overwrite:
            self.auto_convert = False

    overwrite: BoolProperty(
        name="Overwrite",
        default=True,
        description="Overwrite the last text",
        update=update_overwrite
    )
    auto_convert: BoolProperty(
        name="Auto Convert",
        default=False,
        description="On / Off"
    )

    def template_convert(self, layout, context=None):

        row = layout.row(align=True)
        row.prop(self, "overwrite",
                 icon_only=True,
                 icon=("RADIOBUT_ON" if self.overwrite else "RADIOBUT_OFF"),
                 invert_checkbox=self.overwrite)
        row.separator()
        row.operator("ncnc.gcode_create",
                     text="Convert to G-Code" if not self.loading else "",
                     icon="COLOR_GREEN",
                     )
        if self.loading:
            row.prop(self, "loading", slider=True)
        if self.overwrite:
            row.prop(self, "auto_convert",
                     icon_only=True,
                     icon=("ONIONSKIN_ON" if self.auto_convert else "ONIONSKIN_OFF"),
                     # invert_checkbox=self.auto_convert
                     )
        return row

    @classmethod
    def register(cls):
        Scene.ncnc_pr_gcode_create = PointerProperty(
            name="NCNC_PR_GCodeCreate Name",
            description="NCNC_PR_GCodeCreate Description",
            type=cls
        )

    @classmethod
    def unregister(cls):
        del Scene.ncnc_pr_gcode_create


class NCNC_OT_GCodeCreate(Operator):
    bl_idname = "ncnc.gcode_create"
    bl_label = "Convert"
    bl_description = "Convert included objects to Gcode"
    bl_options = {'REGISTER', 'UNDO'}
    # bl_options = {'REGISTER'}

    # if auto converting, auto_call must True
    auto_call: BoolProperty(default=False)

    codes = {}

    delay = .1
    _last_time = 0
    run_index = 0
    last_index = 0

    min_point: FloatVectorProperty(name="Minimum Point", default=[0, 0, 0], subtype="XYZ")
    max_point: FloatVectorProperty(name="Maximum Point", default=[0, 0, 0], subtype="XYZ")

    # !!! Maximum değerleri hesapla. Daha doğrusu objelerin gcodunu alırken al.

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        pr_cvr = context.scene.ncnc_pr_gcode_create

        if self.auto_call and not pr_cvr.auto_convert:
            return {'CANCELLED'}

        len_isrun = len(pr_cvr.isrun)
        if len_isrun:
            pr_cvr.isrun[-1] = False

        self.run_index = len_isrun
        pr_cvr.isrun.append(True)

        self.pr_objs = context.scene.ncnc_pr_objects.items

        ##################
        # Convert to GCodes
        self.codes.clear()
        # TODO: min_point, max_point    -> Bunları kullanılabilir yap
        self.min_point = [0, 0, 0]
        self.max_point = [0, 0, 0]

        context.window_manager.modal_handler_add(self)

        return self.timer_add(context)

    def timer_add(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(self.delay, window=context.window)
        catch_start()
        return {"RUNNING_MODAL"}

    def timer_remove(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {'CANCELLED'}

    def modal(self, context, event):
        if time.time() - self._last_time < self.delay:
            return {'PASS_THROUGH'}

        self._last_time = time.time()

        pr_cvr = context.scene.ncnc_pr_gcode_create

        if not pr_cvr.isrun[self.run_index] or len(self.pr_objs) is 0:
            return self.finished(context)

        if len(self.pr_objs) <= self.last_index:
            self.last_index = 0

        pr_cvr.loading = (len(self.codes) / len(self.pr_objs)) * 100

        #############################################
        #############################################
        obj = self.pr_objs[self.last_index].obj
        conf = obj.ncnc_pr_objectconfigs
        self.last_index += 1

        if not obj:
            return {'PASS_THROUGH'}
        elif conf.is_updated:
            bpy.ops.ncnc.gcode_convert(obj_name=obj.name)
        elif not conf.is_updated and conf.loading == 0:
            self.codes[self.last_index - 1] = conf.gcode

            for j, i in enumerate(conf.min_point):
                self.min_point[j] = min(i, self.min_point[j])

            for j, i in enumerate(conf.max_point):
                self.max_point[j] = max(i, self.max_point[j])

        for i in range(len(self.pr_objs)):
            if not self.codes.get(i):
                return {'PASS_THROUGH'}

        return self.finished(context)

    def finished(self, context):
        pr_cvr = context.scene.ncnc_pr_gcode_create
        pr_cvr.isrun[self.run_index] = False
        pr_cvr.loading = 0
        self.add_footer()

        ###########################
        # Create Internal Text File
        file_name = "nCNC"

        if pr_cvr.overwrite and file_name in bpy.data.texts.keys():
            bpy.data.texts.remove(bpy.data.texts[file_name])

        # Join codes
        codes = [self.add_header()]
        for i in sorted(self.codes):
            codes.append(self.codes[i])
        codes.append(self.add_footer())

        mytext = bpy.data.texts.new(file_name)
        mytext.write("\n".join(codes))

        context.scene.ncnc_pr_texts.texts = mytext.name
        self.report({"INFO"}, "Converted")
        self.timer_remove(context)
        return {"CANCELLED"}

    def add_header(self):
        return f"""(Block-name: Header)
(Block-expand: 1)
(Block-enable: 1)
(Made in Blender by nCNC Add-on)
M3 S1200
G4 P1 (Pause 1 second)
G21 (All units in mm)
"""

    def add_footer(self, total=0):
        # !!! Buradaki 5 değerini, max noktasına göre güncelle
        return f"""
(Block-name: Footer)
(Block-expand: 1)
(Block-enable: 1)
G0 Z{round(self.max_point[2], 3)}
M5
G0 X0 Y0
M2
"""
        # (Total Number of Lines : {total})
