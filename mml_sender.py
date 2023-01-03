import bpy
import websockets
import asyncio
import os
import mml_main as mml
import time
import mml_client
import json

class MMLSubmit(bpy.types.Operator):
    """Send PTex file path to the MML server."""
    bl_idname = "image.mml_send"
    bl_label = "MML Send"
    data_to_send: bpy.props.StringProperty(name="data")
    image_name: bpy.props.StringProperty(name='image_name')
    expected_packets: bpy.props.IntProperty(name='expected_packets')
    reset_parameters: bpy.props.BoolProperty(name='reset_parameters')
        
    @classmethod
    def poll(cls, context):
        return True
        #return context.active_object is not None

    def execute(self, context):
        print("Sending data: ")
        #mml_client.MMLClient.instance.send_command(mml.MML.commands_dict['connect'], self.image_name, self.data_to_send)
        data_dict = { "command" : "load_ptex", "reset_parameters":self.reset_parameters, "image_name":self.image_name, "filepath" : self.data_to_send }
        data = json.dumps(data_dict)
        mml_client.MMLClient.instance.send_json(data)
        return {'FINISHED'}
    
class MMLRequestRender(bpy.types.Operator):
    """Send a render request to the MML server."""
    bl_idname = "image.mml_request_render"
    bl_label = "MML Render Request"
    #image: bpy.props.PointerProperty(name='image')
    image_name: bpy.props.StringProperty(name='image_name')
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        data_dict = { "command":"request_render", "image name":self.image_name }
        image_rr_data = bpy.data.images[self.image_name].mml_properties.get_request_render_data()
        for key in image_rr_data:
            data_dict[key] = image_rr_data[key]
        data = json.dumps(data_dict)
        mml_client.MMLClient.instance.send_json(data)
        return {'FINISHED'}