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
    limits: bpy.props.IntProperty(default=0)
        
    @classmethod
    def poll(cls, context):
        return True
    
    def modal(self, context, event):
        if event.type in {'ESC'} or self.limits > 30:
            self.limits = 0
            self.cancel(context)
            return {'FINISHED'}
        
        if event.type == 'TIMER':
            self.limits += 1
            
        return {'PASS_THROUGH'}

    def execute(self, context):
        mml.MML.inform("Sending data: ")
        data_dict = { "command" : "load_ptex", "reset_parameters":self.reset_parameters, "image_name":self.image_name, "filepath" : self.data_to_send }
        data = json.dumps(data_dict)
        mml_client.MMLClient.instance.send_json(data)
        #return {'FINISHED'}
        
        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step = 0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
    
class MMLRequestRender(bpy.types.Operator):
    """Send a render request to the MML server."""
    bl_idname = "image.mml_request_render"
    bl_label = "MML Render Request"
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