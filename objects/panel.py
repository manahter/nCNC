from bpy.types import Panel, UIList


class NCNC_UL_Objects(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        obj = item.obj

        sor = obj.name not in context.scene.objects.keys()
        row = layout.row()

        if obj.ncnc_pr_objectconfigs.loading:
            row.prop(obj.ncnc_pr_objectconfigs, "loading", slider=True)
        else:
            row.prop(obj, "name",
                     text="",
                     emboss=False,
                     icon_only=sor,
                     icon=f"OUTLINER_OB_{obj.type}" if not sor else "TRASH",
                     # icon_value=layout.icon(obj.data)
                     )


class NCNC_PT_Objects(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "Included Objects"
    bl_idname = "NCNC_PT_objects"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_gcode

    def draw(self, context):
        layout = self.layout

        props = context.scene.ncnc_pr_objects

        row = layout.row()

        col2 = row.column(align=True)
        col2.operator("ncnc.objects", icon="ADD", text="").action = "add"
        col2.operator("ncnc.objects", icon="REMOVE", text="").action = "remove"
        col2.operator("ncnc.objects", icon="TRASH", text="").action = "delete"
        col2.separator()
        col2.operator("ncnc.objects", icon="TRIA_UP", text="").action = "up"
        col2.operator("ncnc.objects", icon="TRIA_DOWN", text="").action = "down"

        col1 = row.column()  # .box()
        col1.template_list(
            "NCNC_UL_Objects",  # TYPE
            "ncnc_ul_objects",  # ID
            props,  # Data Pointer
            "items",  # Propname
            props,  # active_dataptr
            "active_item_index",  # active_propname
            rows=5,
            type='DEFAULT'
        )

        context.scene.ncnc_pr_gcode_create.template_convert(layout, context=context)

    def draw_header_preset(self, context):
        pr_obs = context.scene.ncnc_pr_objects
        self.layout.prop(pr_obs, "hide_in_viewport",
                         text="",
                         icon="HIDE_ON" if pr_obs.hide_in_viewport else "HIDE_OFF",
                         emboss=False
                         )


class NCNC_PT_Stock(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "nCNC"
    bl_label = "Stock"
    bl_idname = "NCNC_PT_objectstock"

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_gcode

    def draw(self, context):
        layout = self.layout

        pr = context.scene.ncnc_pr_objects

        row = layout.row(align=True)
        row.prop(pr, "stock")
        row.prop(pr, "stock_wire",
                 text="",
                 icon="MOD_WIREFRAME" if pr.stock_wire else "SNAP_VOLUME")
