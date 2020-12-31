from bpy.types import Operator, SpaceView3D
from bpy.props import EnumProperty

from bpy_extras.view3d_utils import (
    region_2d_to_vector_3d,
    region_2d_to_origin_3d
)
import blf


class NCNC_OT_JogController(Operator):
    bl_idname = "ncnc.jogcontroller"
    bl_label = "Jog Control Operators"
    bl_description = "Jog Control Operators,\nMove X / Y / Z"
    bl_options = {'REGISTER'}

    action: EnumProperty(name="Jog Controller",
                         items=[("x+", "X+", "TRIA_RIGHT"),  # EVENT_X
                                ("x-", "X-", "TRIA_LEFT"),  # EVENT_Y
                                ("y+", "Y+", "TRIA_UP"),
                                ("y-", "Y-", "TRIA_DOWN"),
                                ("z+", "Z+", "TRIA_UP"),
                                ("z-", "Z-", "TRIA_DOWN"),

                                ("x+y+", "X+ Y+", "DOT"),
                                ("x+y-", "X+ Y-", "DOT"),
                                ("x-y+", "X- Y+", "DOT"),
                                ("x-y-", "X- Y-", "DOT"),

                                ("x0y0", "X0 Y0", "DOT"),
                                ("z0", "Z0", "DOT"),

                                ("0xy", "XY:0", "XY:0"),
                                ("0x", "X:0", "X:0"),
                                ("0y", "Y:0", "Y:0"),
                                ("0z", "Z:0", "Z:0"),
                                ("home", "Home", "Home: XYZ"),
                                ("safez", "Safe Z", "Safe Z: 5mm"),
                                ("cancel", "Jog Cancel", "Jog Cancel and Clear"),
                                ("mousepos", "Mouse Pos", "Set mouse pos")
                                ])

    def invoke(self, context, event=None):

        pr_dev = context.scene.ncnc_pr_machine
        pr_jog = context.scene.ncnc_pr_jogcontroller
        pr_com = context.scene.ncnc_pr_communication

        if self.action == "x+":
            pr_com.send_in_order(f"$J=G21 G91 X{pr_jog.step_size_xy} F{pr_jog.feed_rate}")
        elif self.action == "x-":
            pr_com.send_in_order(f"$J=G21 G91 X-{pr_jog.step_size_xy} F{pr_jog.feed_rate}")
        elif self.action == "y+":
            pr_com.send_in_order(f"$J=G21 G91 Y{pr_jog.step_size_xy} F{pr_jog.feed_rate}")
        elif self.action == "y-":
            pr_com.send_in_order(f"$J=G21 G91 Y-{pr_jog.step_size_xy} F{pr_jog.feed_rate}")
        elif self.action == "z+":
            pr_com.send_in_order(f"$J=G21 G91 Z{pr_jog.step_size_z} F{pr_jog.feed_rate}")
        elif self.action == "z-":
            pr_com.send_in_order(f"$J=G21 G91 Z-{pr_jog.step_size_z} F{pr_jog.feed_rate}")
        elif self.action == "x+y+":
            pr_com.send_in_order(f"$J=G21 G91 X{pr_jog.step_size_xy} Y{pr_jog.step_size_xy} F{pr_jog.feed_rate}")
        elif self.action == "x+y-":
            pr_com.send_in_order(f"$J=G21 G91 X{pr_jog.step_size_xy} Y-{pr_jog.step_size_xy} F{pr_jog.feed_rate}")
        elif self.action == "x-y+":
            pr_com.send_in_order(f"$J=G21 G91 X-{pr_jog.step_size_xy} Y{pr_jog.step_size_xy} F{pr_jog.feed_rate}")
        elif self.action == "x-y-":
            pr_com.send_in_order(f"$J=G21 G91 X-{pr_jog.step_size_xy} Y-{pr_jog.step_size_xy} F{pr_jog.feed_rate}")
        elif self.action == "x0y0":
            pos = pr_dev.mpos if pr_dev.pos_type == "mpos" else pr_dev.wpos
            if pos[2] < 3:
                pr_com.send_in_order(f"$J=G21 G90 Z3 F{pr_jog.feed_rate}")
            # pr_com.send_in_order(f"$J=G21 G91 X{round(pos[0], 3) * -1}Y{round(pos[1], 3) * -1}F{pr_jog.feed_rate}")
            pr_com.send_in_order(f"$J=G21 G90 X0 Y0 F{pr_jog.feed_rate}")
        elif self.action == "z0":
            pos = pr_dev.mpos if pr_dev.pos_type == "mpos" else pr_dev.wpos
            pr_com.send_in_order(f"$J=G21G91Z{round(pos[2], 3) * -1}F{pr_jog.feed_rate}")

        # #### Reset Zero XYZ
        elif self.action == "0xy":
            pr_com.send_in_order("G10 L20 X0 Y0")
        elif self.action == "0x":
            pr_com.send_in_order("G10 L20 X0")
        elif self.action == "0y":
            pr_com.send_in_order("G10 L20 Y0")
        elif self.action == "0z":
            pr_com.send_in_order("G10 L20 Z0")

        elif self.action == "home":
            pos = pr_dev.mpos if pr_dev.pos_type == "mpos" else pr_dev.wpos
            if pos[2] < 3:
                pr_com.send_in_order(f"$J=G21 G90 Z3 F{pr_jog.feed_rate}")
            pr_com.send_in_order(f"$J=G21 G90 X0 Y0 F{pr_jog.feed_rate}")
            pr_com.send_in_order(f"$J=G21 G90 Z0 F{pr_jog.feed_rate}")
        elif self.action == "safez":
            pos = pr_dev.mpos if pr_dev.pos_type == "mpos" else pr_dev.wpos
            pr_com.send_in_order(f"$J=G21 G90 Z5 F{pr_jog.feed_rate}")
        elif self.action == "cancel":
            pr_com.set_hardly("0x85")

        elif self.action == "mousepos":
            # context.region
            # bpy.ops.view3d.view_axis(type="TOP")
            context.window_manager.modal_handler_add(self)
            self.draw_handle_2d = SpaceView3D.draw_handler_add(
                self.draw_callback_2d,
                (self, context),
                "WINDOW",
                "POST_PIXEL"
            )
            return {"RUNNING_MODAL"}
        return {"FINISHED"}

    def modal(self, context, event):
        if event.type == "LEFTMOUSE":
            # print("Mouse     ; ", event.mouse_x, event.mouse_y)
            # print("Mouse Prev; ", event.mouse_prev_x, event.mouse_prev_y)
            # print("Mouse Regn; ", event.mouse_region_x, event.mouse_region_y)

            for area in context.window.screen.areas:

                if area.type != 'VIEW_3D':
                    continue

                if area.x < event.mouse_x < area.x + area.width and area.y < event.mouse_y < area.y + area.height:

                    active_region = None
                    active_region_3d = None

                    ##############
                    # on Quad View
                    if len(area.spaces.active.region_quadviews):
                        #  +-----------------+
                        #  | quad 1 | quad 3 |
                        #  |--------+--------|
                        #  | quad 0 | quad 2 |
                        #  +-----------------+
                        quad_index = -1
                        for region in area.regions:

                            if region.type == "WINDOW":

                                quad_index += 1
                                if (region.x <= event.mouse_x < region.width + region.x) and \
                                        (region.y <= event.mouse_y < region.height + region.y):
                                    active_region = region
                                    active_region_3d = area.spaces.active.region_quadviews[quad_index]

                                    break

                    #####################
                    # on Normal View (3D)
                    else:
                        for region in area.regions:
                            if region.type == "WINDOW":
                                active_region = region
                                break
                        active_region_3d = area.spaces[0].region_3d

                    if not (active_region and active_region_3d):
                        self.report({'WARNING'}, "View should be [TOP, LEFT, RIGHT ...]")
                        return {'CANCELLED'}

                    m_pos = (event.mouse_x - region.x, event.mouse_y - region.y)
                    origin = region_2d_to_origin_3d(active_region, active_region_3d, m_pos)
                    direction = region_2d_to_vector_3d(active_region, active_region_3d, m_pos)

                    # print(origin, direction)
                    # print("Area     ;", area)
                    # print("Region   ;", active_region)
                    # print("Region3D ;", active_region_3d)
                    # print("Origin   ;", origin)
                    # print("Direction;", direction)

                    pr_jog = context.scene.ncnc_pr_jogcontroller
                    pr_com = context.scene.ncnc_pr_communication

                    at = ""

                    # ##################
                    # Move XY - TOP VIEW
                    if direction[2] == -1:
                        at = f"X{round(origin[0], 2)} Y{round(origin[1], 2)}"

                    # #####################
                    # Move XY - BOTTOM VIEW
                    if direction[2] == 1:
                        at = f"X{round(origin[0], 2)} Y{round(origin[1], 2)}"

                    # ####################
                    # Move XZ - FRONT VIEW
                    elif direction[1] == 1:
                        at = f"X{round(origin[0], 2)} Z{round(origin[2], 2)}"

                    # ###################
                    # Move XZ - BACK VIEW
                    elif direction[1] == -1:
                        at = f"X{round(origin[0], 2)} Z{round(origin[2], 2)}"

                    # ####################
                    # Move YZ - RIGHT VIEW
                    elif direction[0] == -1:
                        at = f"Y{round(origin[1], 2)} Z{round(origin[2], 2)}"

                    # ###################
                    # Move YZ - LEFT VIEW
                    elif direction[0] == 1:
                        at = f"Y{round(origin[1], 2)} Z{round(origin[2], 2)}"

                    if at:
                        pr_com.send_in_order(f"$J=G21 G90 {at} F{pr_jog.feed_rate}")
                    else:
                        self.report({'WARNING'}, "View should be [TOP, LEFT, RIGHT ...]")

                    break

        if event.value == "PRESS" or event.type == "ESC":
            SpaceView3D.draw_handler_remove(self.draw_handle_2d, "WINDOW")
            if context.area:
                context.area.tag_redraw()
            return {'CANCELLED'}

        return {"PASS_THROUGH"}

    def draw_callback_2d(self, op, context):
        # Draw text to indicate that draw mode is active
        region = context.region
        text = "- Move: Mouse Left Click (inView: TOP, LEFT, RIGHT ...)-"
        subtext = "Close: Press Anything"

        xt = int(region.width / 2.0)

        blf.size(0, 24, 72)
        blf.position(0, xt - blf.dimensions(0, text)[0] / 2, 60, 0)
        blf.draw(0, text)

        blf.size(1, 20, 72)
        blf.position(1, xt - blf.dimensions(0, subtext)[0] / 2, 30, 1)
        blf.draw(1, subtext)

        # Draw handler to paint onto the screen


