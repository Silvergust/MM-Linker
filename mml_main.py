import bpy
import json
import mml_sender
import mml_client
import asyncio
import time
import math


class MMLProperties(bpy.types.PropertyGroup):
    port: bpy.props.IntProperty(name="Port") # Unfortunately couldn't go on something more sensible like MMLClient
    ptex_filepath: bpy.props.StringProperty(name = "PTex Filepath", subtype='FILE_PATH')
    use_remote_parameters: bpy.props.BoolProperty(name="Use remote parameters")
    auto_update: bpy.props.BoolProperty(name="Auto-Update")
    request_albedo: bpy.props.BoolProperty(name="Request albedo map")
    request_metallicity: bpy.props.BoolProperty(name="Request metallicity map")
    request_roughness: bpy.props.BoolProperty(name="Request roughness map")
    request_emission: bpy.props.BoolProperty(name="Request emission map")
    request_normal: bpy.props.BoolProperty(name="Request normal map")
    request_occlusion: bpy.props.BoolProperty(name="Request ambient occlusion map")
    request_depth: bpy.props.BoolProperty(name="Request depth map")
    request_opacity: bpy.props.BoolProperty(name="Request opacity map")
    request_sss: bpy.props.BoolProperty(name="Request SSS map")
    
    def get_request_render_data(self):
        data = {}
        data['image_name'] = self.id_data.name
        data['resolution'] = self.id_data.size[0]
        data['render'] = 'true'
        maps = []
        # There should be a way to get a reference to the parameter, not just its value
        if self.request_albedo:
            maps.append("albedo")
        if self.request_roughness:
            maps.append("roughness")
        if self.request_metallicity:
            maps.append("metallicity")
        if self.request_normal:
            maps.append("normal")
        if self.request_occlusion:
            maps.append("occlusion")
        if self.request_emission:
            maps.append("emission")
        if self.request_depth:
            maps.append("depth")
        if self.request_opacity:
            maps.append("opacity")
        if self.request_sss:
            maps.append("sss")
        data["maps"] = maps
        return data


def update_test(self, context):
        if self.should_update and self.owner_image.mml_properties.auto_update:
            data_to_send = {}
            data_to_send["command"] = "parameter_change"
            data_to_send["node_name"] = self.node_name
            data_to_send["param_name"] = self.param_name
            data_to_send["param_value"] = self.value
            data_to_send["parameter_type"] = "remote" if self.is_remote else "local"

            image_rr_data = self.owner_image.mml_properties.get_request_render_data()
            for key in image_rr_data:
                data_to_send[key] = image_rr_data[key]
            mml_client.MMLClient.instance.send_json(json.dumps(data_to_send))
            

class MMLParameters(bpy.types.PropertyGroup):
    node_name: bpy.props.StringProperty()
    param_name: bpy.props.StringProperty()
    param_label: bpy.props.StringProperty()
    value: bpy.props.StringProperty(update=update_test)
    owner_image: bpy.props.PointerProperty(type=bpy.types.Image)
    should_update: bpy.props.BoolProperty()
    is_remote: bpy.props.BoolProperty()
    
    def get_id(self):
        return "{}/{}".format(self.node_name, self.param_name if self.param_label == "" else self.param_label)
    
    
class MMLGlobalProperties(bpy.types.PropertyGroup):
    port : bpy.props.IntProperty()
    
    
class MML():
    command_key_requirements = {
        "pong" : [],
        "replace_image" : ["image_name", "image_data"], # TODO: Make use of image names for proper identification
        "init_parameters" : ["image_name", "parameters_type", "parameters"],
        "inform" : ["info"],
        "request_parameters": ["image_name"],
        "parameters_loaded": []
    }
    info_message = ""
    received_messages = []
    mm_parameters_loaded = False

    @classmethod
    def key_check(self, data):
        if "command" not in data:
            print("ERROR: \"command\" key not found in data")
            return False
        for key in self.command_key_requirements[data["command"]]:
            if key not in data:
                MML.inform("ERROR: key \"{}\" not found in data".format(key))
                return False
        return True
        
    @classmethod
    def interpret(self, data):
        if data[:5] == b"json|":
            self.interpret_json(data[5:]) 
        elif data[:6] == b"image|":
            padding = int(data[6:9])
            image_name = str(data[10:padding-6])[2:-1]
            size = int(data[padding-5:padding-1])
            self.replace_image(image_name, size, data[padding:]) # TODO: Do away with the unnecessary copying
        else:
            print("Failed to interpret message")
        return
    
    @classmethod
    def interpret_json(self, data):
        data = json.loads(data)
        if not self.key_check(data):
            MML.inform("Error: Key check fail")
            return
        command = data["command"]
        if command == "pong":
            #print("pong")
            pass
        elif command == "init_parameters":
            print("Initializing parameters ({})".format(data["parameters_type"]))
            MML.initialize_parameters(data)
        elif command == "inform":
            MML.inform(data["info"])
        elif command == "request_parameters":
            data_to_send = { "command":"set_multiple_parameters", "parameters":[] }
            img = bpy.data.images[data["image_name"]]
            for parameter in img.mml_remote_parameters:
                parameter_data = json.dumps({ "node_name":parameter.node_name, "param_name":parameter.param_name, "param_label":parameter.param_label, "param_value":parameter.value, "image_name":parameter.owner_image.name, "render":"False", "param_type":"remote"})
                data_to_send["parameters"].append(parameter_data)
            for parameter in img.mml_local_parameters:
                parameter_data = json.dumps({ "node_name":parameter.node_name, "param_name":parameter.param_name, "param_label":"",  "param_value":parameter.value, "image_name":parameter.owner_image.name, "render":"False", "param_type":"local"})
                data_to_send["parameters"].append(parameter_data)
                mml_client.MMLClient.instance.send_json(json.dumps(data_to_send))
            print(data_to_send)
        elif command == "parameters_loaded":
            MML.mm_parameters_loaded = True


    @classmethod
    def replace_image(self, image_name, size, data):
        if image_name in bpy.data.images:
            img = bpy.data.images[image_name]
        else:
            img = bpy.data.images.new(name=image_name, width=size, height=size)

        t0 = time.time()
        if len(img.pixels) != len(data):
            MML.inform("ERROR: Expected data of size {}, got {}".format(len(img.pixels), len(data)))
            return
        img.pixels.foreach_set([byte / 255.0 for byte in data])
        img.pack()
        img.update()
        bpy.context.view_layer.update()
        MML.inform("Image replaced in {} seconds.".format(time.time() - t0))


    @classmethod
    def initialize_parameters(self, data, remote=False):
        MML.inform("Initializing parameters.")
        img = bpy.data.images[data["image_name"]]
        parameters = None
        if data["parameters_type"] == "remote":
            print("\n Remote parameters: \n")
            parameters = img.mml_remote_parameters
        elif data["parameters_type"] == "local":
            print("\n Local: \n")
            parameters = img.mml_local_parameters
        else:
            MML.inform("ERROR: Incorrect parameters type on initialization.")
        parameters.clear()
        received_parameters_data = data["parameters"]

        for entry in received_parameters_data:
            print("entry['node']: ", entry['node'])
            new_parameter = parameters.add()
            new_parameter.owner_image = img
            new_parameter.node_name = entry['node']
            new_parameter.param_name = entry['param_name']
            new_parameter.should_update = False
            new_parameter.value = str(entry['param_value'])
            new_parameter.should_update = True
            new_parameter.param_label = entry['param_label']
        return
        
    @classmethod
    def is_ready(self):
        return mml_client.MMLClient.instance.status == mml_client.Status.connected and MML.mm_parameters_loaded
    
    @classmethod
    def on_disconnect(self):
        MML.mm_parameters_loaded = False
        
    @classmethod
    def inform(self, message):
        self.info_message = message
        print(message)