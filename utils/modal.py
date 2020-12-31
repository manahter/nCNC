running_modals = {}


def register_modal(self):
    # if exists previous modal (self), stop it
    unregister_modal(self)

    # Register to self
    running_modals[self.bl_idname] = self

    # self.report({'INFO'}, "NCNC Communication: Started")


def unregister_modal(self):
    # Get previous running modal
    self_prev = running_modals.get(self.bl_idname)

    try:
        # if exists previous modal (self), stop it
        if self_prev:
            self_prev.inloop = False
            running_modals.pop(self.bl_idname)

            # self.report({'INFO'}, "NCNC Communication: Stopped (Previous Modal)")
    except:
        running_modals.pop(self.bl_idname)