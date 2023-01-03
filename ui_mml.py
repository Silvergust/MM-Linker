import bpy
import json
import pathlib
import textwrap

import sys
import os

blend_dir = os.path.dirname(bpy.data.filepath)
if blend_dir not in sys.path:
    sys.path.append(blend_dir)
    
import mml_main as mml
import mml_sender
import importlib
import mml_client

importlib.reload(mml)
importlib.reload(mml_sender)
importlib.reload(mml_client)


class MMLPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "MML Panel"
    bl_idname = "OBJECT_PT_mml"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "MML"

    def __init__(self):
        img = bpy.context.area.spaces.active.image
        self.mml_client = mml_client.MMLClient()

    def draw(self, context):
        layout = self.layout

        img = bpy.context.area.spaces.active.image

        row = layout.row()
        row.label(text="Status: {}".format(self.mml_client.instance.get_status_string()))
        row = layout.row()
        #layout.prop(mml_client.MMLClient, "Port")
        #layout.prop(mml_client.MMLClient, "port")
        row.label(text=mml.MML.info_message)
        row = layout.row()
        #layout.prop(img.mml_properties, 'ptex_filepath')
        
        row = layout.row()
        connect_button = layout.operator(mml_client.OBJECT_OT_connect.bl_idname, text="Connect to MM")
        #row.enabled = True
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
        row3.enabled = mml.MML.is_ready()
        
        
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
        row.prop(img.mml_properties, 'request_opacity', text="Opacity", toggle=toggle)
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
        row.enabled = mml.MML.is_ready()
            

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
            
        if data.params_list_index >= 0 and data.mml_remote_parameters:
            row = layout.row()
            row.prop(item, "value", text="")

def register():
    bpy.utils.register_class(mml.MMLProperties)
    bpy.utils.register_class(mml.MMLParameters)
    bpy.utils.register_class(MMLPanel)
    bpy.types.Image.mml_remote_parameters = bpy.props.CollectionProperty(type=mml.MMLParameters)
    bpy.types.Image.mml_local_parameters = bpy.props.CollectionProperty(type=mml.MMLParameters) # A local parameter is one from a non-remote node
    bpy.types.Image.mml_properties = bpy.props.PointerProperty(type=mml.MMLProperties, name="MML Properties", description="MML properties", update=update_test)
    #mml_sender.OBJECT_OT_send.mml_properties = bpy.props.PointerProperty(type=mml.MMLProperties, name="MML Properties", description="MML properties")
    #bpy.utils.register_class(OBJECT_OT_create_ptex_props)
    bpy.utils.register_class(mml_sender.MMLSubmit)
    bpy.utils.register_class(mml_sender.MMLRequestRender)
    bpy.utils.register_class(mml_client.OBJECT_OT_connect)
    bpy.utils.register_class(UI_UL_ParamsList)
    bpy.types.Image.params_list_index = bpy.props.IntProperty(name = "Index for ParamList",
                                             default = 0)

def unregister():
    bpy.utils.unregister_class(mml.MMLParameters)
    bpy.utils.unregister_class(mml.MMLProperties)
    bpy.utils.unregister_class(MMLPanel)
    #del bpy.types.Image.mml_parameters
    del bpy.types.Image.mml_remote_parameters
    del bpy.types.Image.mml_local_parameters
    del bpy.types.Image.mml_properties
    del mml_sender.OJBECT_OT_send.mml_properties
    #bpy.utils.unregister_class(OBJECT_OT_create_ptex_props)
    #bpy.utils.unregister_class(mml_sender.OBJECT_OT_send)
    bpy.utils.unregister_class(mml_sender.MMLSubmit)
    bpy.utils.unregister_class(mml_sender.MMLRequestRender)
    bpy.utils.unregister_class(mml_client.OBJECT_OT_connect)
    bpy.utils.unregister_class(UI_UL_ParamsList)

if __name__ == "__main__":
    print("### Running MML ###")
    #register()