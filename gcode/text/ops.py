import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty


class NCNC_OT_Text(Operator):
    bl_idname = "ncnc.gcode"
    bl_label = "Gcode Read"
    bl_description = ""
    bl_options = {'REGISTER'}

    text_name: StringProperty()
    run_index: IntProperty()
    code_lines = []
    last_index = 0
    pr_txt = None
    delay = .1

    # Added radius R value reading feature in G code.
    # Reference
    # https://www.bilkey.com.tr/online-kurs-kurtkoy/cnc/fanuc-cnc-programlama-kodlari.pdf
    # https://www.cnccookbook.com/cnc-g-code-arc-circle-g02-g03/
    # http://www.helmancnc.com/circular-interpolation-concepts-programming-part-2/

    # R açıklama
    # x0'dan x10'a gideceğiz diyelim.
    # R -5 ile 5 aralığında olamaz. Çünkü X'in başlangıç ve bitiş noktası arası mesafe zaten 10.
    # 10/2 = 5 yapar. R değeri en küçük 5 olur.
    # R - değer alırsa, çemberin büyük tarafını takip eder. + değer alırsa küçük tarafını.
    #

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        self.pr_txt = bpy.data.texts[self.text_name].ncnc_pr_text
        context.window_manager.modal_handler_add(self)

        line_0 = self.pr_txt.lines.add()
        line_0.load("G0 G90 G17 G21 X0 Y0 Z0 F500")

        self.code_lines = self.pr_txt.id_data.as_string().splitlines()

        return self.timer_add(context)

    def timer_add(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(self.delay, window=context.window)
        return {"RUNNING_MODAL"}

    def timer_remove(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {'CANCELLED'}

    def modal(self, context, event):
        if not self.pr_txt.isrun[self.run_index]:
            return self.timer_remove(context)

        pr = self.pr_txt

        context.scene.ncnc_pr_texts.loading = (self.last_index / len(self.code_lines)) * 100

        loop_count = 100 if event.type == "TIMER" else 20
        for no, code in enumerate(self.code_lines[self.last_index:], start=self.last_index + 1):
            pr.event = True
            pr.event_selected = True
            self.last_index += 1

            pr.count = no

            l = pr.lines.add()
            l.index = no
            l.load(code)

            # Calc -> Total Length, Time
            if l.length:
                pr.distance_to_travel += l.length
                pr.estimated_time += l.estimated_time

            # Calc -> Total Pause Time
            if l.pause:
                pr.estimated_time += l.pause

            # Calc -> Min/Max X,Y,Z
            for j, v in enumerate(l.xyz):
                if pr.minimum[j] > v:
                    pr.minimum[j] = v
                if pr.maximum[j] < v:
                    pr.maximum[j] = v

            if self.last_index % loop_count == 0:
                return {'PASS_THROUGH'}

        pr.event = True

        if context.area:
            context.area.tag_redraw()

        self.report({'INFO'}, "G-Code Loaded")
        self.pr_txt.isrun[self.run_index] = False
        context.scene.ncnc_pr_texts.loading = 0
        return self.timer_remove(context)