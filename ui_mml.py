import json
import pathlib
import textwrap

import sys
import os
    
if "bpy" in locals():
    import importlib
    importlib.reload(mml_main)
    importlib.reload(mml_sender)
    importlib.reload(mml_client)
else:
    import bpy
    from . import mml_main
    from . import mml_sender
    from . import mml_client



class MMLPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "MML Panel"
    bl_idname = "OBJECT_PT_mml"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "MML"


    def draw(self, context):
        layout = self.layout

        img = bpy.context.area.spaces.active.image
        if not  mml_client.MMLClient.instance:
            mml_client.MMLClient()
        self.mml_client = mml_client.MMLClient.instance

        row = layout.row()
        row.label(text="Status: {}".format(self.mml_client.instance.get_status_string()))

        if not img:
            return

        row = layout.row()
        layout.prop(img.mml_properties, "port")
        mml_client.MMLClient.instance.port = img.mml_properties.port
        row.label(text=mml_main.MML.info_message)

        row = layout.row()
        layout.prop(img.mml_properties, 'ptex_filepath')
        
        row = layout.row()
        layout.prop(img.mml_properties, 'island_only')
        layout.operator(mml_client.OBJECT_OT_update_islands.bl_idname)

        row = layout.row()
        connect_button = layout.operator(mml_client.OBJECT_OT_connect.bl_idname, text="Connect to MM")
        row1 = self.layout.row()   
        ptex_button = row1.operator(mml_sender.MMLSubmit.bl_idname, text="Submit PTex to MM")   
        row2 = self.layout.row()
        ptex_with_params_button = row2.operator(mml_sender.MMLSubmit.bl_idname, text="Submit and reset Parameters")   
        ptex_with_params_button.reset_parameters = True
        row3 = self.layout.row()
        render_request_button = row3.operator(mml_sender.MMLRequestRender.bl_idname, text="Request Render")
        render_request_button.image_name = img.name
        for button in [ptex_button, ptex_with_params_button]:
            button.data_to_send = bpy.path.abspath(img.mml_properties.ptex_filepath)
            button.image_name = img.name
        
        for r in [row1, row2]:
            r.enabled = self.mml_client.instance.status == mml_client.Status.connected
        row3.enabled = mml_main.MML.is_ready()
        
        
        self.layout.separator(factor=2)
        toggle = -1
        row = layout.row(align = True)
        row.prop(img.mml_properties, 'request_albedo', text="Albedo", toggle=toggle)
        row.prop(img.mml_properties, 'request_metallicity', text="Metallicity", toggle=toggle)
        row.prop(img.mml_properties, 'request_roughness', text="Roughness", toggle=toggle)
        
        row = layout.row(align = True)
        row.prop(img.mml_properties, 'request_emission', text="Emission", toggle=toggle)
        row.prop(img.mml_properties, 'request_normal', text="Normal", toggle=toggle)
        row.prop(img.mml_properties, 'request_occlusion', text="AO", toggle=toggle)
        
        row = layout.row(align = True)
        row.prop(img.mml_properties, 'request_depth', text="Depth", toggle=toggle)
#        row.prop(img.mml_properties, 'request_opacity', text="Opacity", toggle=toggle)
        row.prop(img.mml_properties, 'request_sss', text="SSS", toggle=toggle)

        self.layout.separator(factor=2)
        row = layout.row()
        row.prop(img.mml_properties, 'use_remote_parameters', toggle=toggle)
        row.prop(img.mml_properties, 'auto_update', toggle=toggle)
                
        row = self.layout.row()
        if (img.mml_properties.use_remote_parameters):
            row.template_list("UI_UL_ParamsList", "The_List", img,
                          "mml_remote_parameters", img, "params_list_index")
        else:
            row.template_list("UI_UL_ParamsList", "The_List", img,
                          "mml_local_parameters", img, "params_list_index")
        row.enabled = mml_main.MML.is_ready()
            

def update_test(self, context):
    print("Update_test: ", self)
    

class UI_UL_ParamsList(bpy.types.UIList):
    """Demo UIList."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.get_id(), icon = custom_icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)
        if data.params_list_index >= 0:
            row = layout.row()
            row.prop(item, "value", text="")
