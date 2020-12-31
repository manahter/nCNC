from bpy.types import Panel, UIList


class NCNC_UL_Messages(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row()
        if item.message.startswith("error:"):
            icon = "FUND"  # "FUND" or "COLORSET_01_VEC"
        elif item.ingoing:
            icon = "BLANK1"
        else:
            icon = "RIGHTARROW_THIN"
        row.prop(item, "message",
                 text="",  # time.strftime(item.time),
                 icon=icon,  # "BLANK1"  "NONE"
                 emboss=False)


class NCNC_PT_Communication(Panel):
    bl_idname = "NCNC_PT_communication"
    bl_label = "Communication"
    bl_region_type = "UI"
    bl_space_type = "VIEW_3D"
    bl_category = "nCNC"

    # bl_options = {"DEFAULT_CLOSED", "HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        return context.scene.ncnc_pr_head.tool_machine

    def draw(self, context):
        layout = self.layout
        pr_com = context.scene.ncnc_pr_communication

        col = layout.column(align=True)
        col.template_list(
            "NCNC_UL_Messages",  # TYPE
            "ncnc_ul_messages",  # ID
            pr_com,  # Data Pointer
            "items",  # Propname
            pr_com,  # active_dataptr
            "active_item_index",  # active_propname
            rows=3,
            type='DEFAULT'
        )

        row = col.row(align=True)

        # if not context.scene.ncnc_pr_connection.isconnected:
        #    row.enabled = False
        #    row.alert = True

        row.prop(pr_com, "messaging", text="", full_event=False)
        row.operator("ncnc.messages", text="", icon="TRASH", ).action = "clear"

        # row = layout.row(align=True)
        # row.label(text=f"Messages -> {len(pr_com.items)}")
        # row.operator("ncnc.messages", text="", icon="TRASH").action = "clear"

        row = layout.row(align=True)
        row.label(text=f"Queue -> Public {len(pr_com.queue_list)}, Hidden {len(pr_com.queue_list_hidden)}")
        row.operator("ncnc.messages", text="", icon="TRASH").action = "clearqueu"