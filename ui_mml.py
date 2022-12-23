import bpy
import json
import pathlib

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
        self.mml_client = mml_client.MMLClient(img)

    def draw(self, context):
        layout = self.layout

        img = bpy.context.area.spaces.active.image

        row = layout.row()
        row.label(text="Status: {}".format(self.mml_client.instance.get_status_string()))
        row = layout.row()
        layout.prop(img.mml_properties, 'ptex_filepath')
        row = layout.row()
        layout.prop(img.mml_properties, 'use_remote_parameters')
        
        row = layout.row()
        connect_button = layout.operator(mml_client.OBJECT_OT_connect.bl_idname, text="Connect to MM")
        row = layout.row()
        ptex_button = layout.operator(mml_sender.OBJECT_OT_send.bl_idname, text="Submit PTex to MM")
        ptex_button.data_to_send = bpy.path.abspath(img.mml_properties.ptex_filepath)
        ptex_button.expected_packets = 2
        ptex_button.image_name = img.name
        #send_ptex_button = layout.operator(mml_sender.OBJECT_OT_send.bl_idname, text="Send PTex")
        #send_ptex_button.image_name = img.name
        #connect_button = layout.operator(mml_sender.OBJECT_OT_send.bl_idname, text="Set resolution")
        #connect_button.data_to_send = img.size
        
        row = layout.row()
        if (img.mml_properties.use_remote_parameters):
            row.template_list("UI_UL_ParamsList", "The_List", img,
                          "mml_remote_parameters", img, "params_list_index")
        else:
            row.template_list("UI_UL_ParamsList", "The_List", img,
                          "mml_local_parameters", img, "params_list_index")
                          
            
#    def get_status_text(self):
#        if self.connection_status == ConnectionStatus.Disconnected:
#            return "Disconnected."
#        if self.connection_status == ConnectionStatus.Connected:
#            return "Connected."
            
            
#class OBJECT_OT_create_ptex_props(bpy.types.Operator):
#    bl_idname = "image.create_ptex_props"
#    bl_label = "Create PTex Properties"
#    bl_options = {'REGISTER', 'UNDO'}

#    def get_ptex_parameters(self):
#        img = bpy.context.area.spaces.active.image
#        if not 'ptex_filepath' in img:
#            print("Error: no correct ptex filepath in image {}".format(img))
#            return []
#        try:
#            directory = str(pathlib.Path(__file__).parent) + img["ptex_filepath"]
#            file = open(directory, 'r')
#            json_file = json.load(file)
#            file.close()
#        except FileNotFoundError as error:
#            print("FileNotFoundError: ", error.strerror)
#            print(error.strerror)
#            return []

#        output = []
#        for node in json_file["nodes"]:
#            if "type" in node and node["type"] == "remote":
#                for param_key in node["parameters"]:
#                    print("Found parameter {} with value {}".format(str(param_key), str(node["parameters"][param_key])))
#                    output.append("{} :: {}".format(param_key, node["parameters"][param_key]))        
#        print("Returning ", output)
#        return output
#       
#    def execute(self, context):
#        img = bpy.context.area.spaces.active.image
#        img.mml_local_parameters.clear()
#        img.mml_remote_parameters.clear()
#        ptex_parameters = self.get_ptex_parameters()
#        properties = []
#        i=0
#        for param in ptex_parameters:
#            print("Adding param {} as a new mml_parameter property to the material".format(param))
#            i += 1
#            new_parameter = img.mml_remote_parameters.add()
#            new_parameter.parameter = "dfdf " + str(i)
#        print("Created ptex properties")
#        return {'FINISHED'}

def update_test(self, context):
    print("Update_test: ", self)
    

class UI_UL_ParamsList(bpy.types.UIList):
    """Demo UIList."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        custom_icon = 'OBJECT_DATAMODE'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon = custom_icon)
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
    mml_sender.OBJECT_OT_send.mml_properties = bpy.props.PointerProperty(type=mml.MMLProperties, name="MML Properties", description="MML properties")
    #bpy.utils.register_class(OBJECT_OT_create_ptex_props)
    bpy.utils.register_class(mml_sender.OBJECT_OT_send)
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
    bpy.utils.unregister_class(mml_sender.OBJECT_OT_send)
    bpy.utils.unregister_class(mml_client.OBJECT_OT_connect)
    bpy.utils.unregister_class(UI_UL_ParamsList)

if __name__ == "__main__":
    print("### Running MML ###")
    register()