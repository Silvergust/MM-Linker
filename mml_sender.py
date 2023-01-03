import bpy
import websockets
import asyncio
import os
import mml_main as mml
import time
import mml_client
import json

class MMLSubmit(bpy.types.Operator):
    """Send shader data to the MML program."""
    bl_idname = "image.mml_send"
    bl_label = "MML Send"
    data_to_send: bpy.props.StringProperty(name="data")
    image_name: bpy.props.StringProperty(name='image_name')
    expected_packets: bpy.props.IntProperty(name='expected_packets')
    reset_parameters: bpy.props.BoolProperty(name='reset_parameters')
        
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        print("Sending data: ")
        #mml_client.MMLClient.instance.send_command(mml.MML.commands_dict['connect'], self.image_name, self.data_to_send)
        data_dict = { "command" : "load_ptex", "reset_parameters":self.reset_parameters, "image_name":self.image_name, "filepath" : self.data_to_send }
        data = json.dumps(data_dict)
        mml_client.MMLClient.instance.send_json(data)
        return {'FINISHED'}