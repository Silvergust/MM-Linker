import json

import asyncio
import time
import math

if "bpy" in locals():
    import importlib
    importlib.reload(mml_client)
    importlib.reload(mml_sender)
else:
    import bpy
    from . import mml_client
    from . import mml_sender


class MMLProperties(bpy.types.PropertyGroup):
    port: bpy.props.IntProperty(name="Port", default=6001) # Unfortunately couldn't go on something more sensible like MMLClient
    ptex_filepath: bpy.props.StringProperty(name = "PTex Filepath", subtype='FILE_PATH')
    island_only: bpy.props.BoolProperty(name = "Selected Island Only")
    use_remote_parameters: bpy.props.BoolProperty(name="Use remote parameters")
    auto_update: bpy.props.BoolProperty(name="Auto-Update")
    request_albedo: bpy.props.BoolProperty(name="Request albedo map")
    request_metallicity: bpy.props.BoolProperty(name="Request metallicity map")
    request_roughness: bpy.props.BoolProperty(name="Request roughness map")
    request_emission: bpy.props.BoolProperty(name="Request emission map")
    request_normal: bpy.props.BoolProperty(name="Request normal map")
    request_occlusion: bpy.props.BoolProperty(name="Request ambient occlusion map")
    request_depth: bpy.props.BoolProperty(name="Request depth map")
    request_transparency: bpy.props.BoolProperty(name="Request transparency map")
    request_sss: bpy.props.BoolProperty(name="Request SSS map")
    
    def get_request_render_data(self):
        data = {}
        data['image_name'] = self.id_data.name
        data['resolution'] = self.id_data.size[0]
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
        #if self.request_opacity:
        #    maps.append("transparency")
        if self.request_sss:
            maps.append("sss")
        data["maps"] = maps
        return data


def parameter_update(self, context):
        if self.should_update:
            data_to_send = {}
            data_to_send["command"] = "parameter_change"
            data_to_send["node_name"] = self.node_name
            data_to_send["param_name"] = self.param_name
            data_to_send["param_value"] = self.value
            data_to_send["parameter_type"] = "remote" if self.is_remote else "local" # TODO: Rename (e.g. "is the type int or is the type remote?")
            data_to_send["render"] = str(self.owner_image.mml_properties.auto_update)
            print(" A data_to_send['render']: ", data_to_send['render'])
            print("AAAAAAAAAAAAAAAAAAA ", self.owner_image.mml_properties.auto_update)

            image_rr_data = self.owner_image.mml_properties.get_request_render_data()
            for key in image_rr_data:
                data_to_send[key] = image_rr_data[key]
            print("data_to_send['render']: ", data_to_send['render'])
            mml_client.MMLClient.instance.send_json(json.dumps(data_to_send))
            

class MMLParameters(bpy.types.PropertyGroup):
    node_name: bpy.props.StringProperty()
    param_name: bpy.props.StringProperty()
    param_label: bpy.props.StringProperty()
    value: bpy.props.StringProperty(update=parameter_update)
    owner_image: bpy.props.PointerProperty(type=bpy.types.Image)
    should_update: bpy.props.BoolProperty()
    is_remote: bpy.props.BoolProperty()
    
    def get_id(self):
        return self.param_label if self.owner_image.mml_properties.use_remote_parameters else "{}/{}".format(self.node_name, self.param_name)
    
    

class Island():
    def __init__(self, vert):
        #self.vertices = bm.verts
        self.vertices = self.get_island_vertices(vert)
        #self.boundary_points = self.get_boundary_points()
        self.boundary_uv_points = self.get_boundary_uv_points(bm.loops.layers.uv[0])
        print("vertices:")
        print(self.vertices)


    def get_island_vertices(self, vertex):
        stack = [vertex]
        output = []
        while len(stack) > 0:
            vert = stack.pop()
            other_verts = [loop.other_vert(vert) for loop in vert.link_loops]
            for other_vert in other_verts:
                if other_vert not in output:
                    output.appen(other_vert)
        return output



    ### UNTESTED ###
    def get_boundary_points(self):
        loops = set()
        for vert in self.vertices:
            loops = loops.union(vert.link_loops[:]) # Slow?
        boundary_loops = [loop for loop in loops if Island.is_loop_boundary(loop)] #Island.loops_are_adjacent(loop)]
        sorted_boundary_loops = boundary_loops[0]
        while len(sorted_boundary_loops) < boundary_loops:
            next_loop = sorted_boundary_loops[-1].link_loop_next
            if Island.is_boundary_loop(next_loop):
                sorted_boundary_loops.append(next_loop)
            else:
                #sorted_boundary_loops.append(next_loop.link_loop_next)
                sorted_boundary_loops.append(next_loop.link_loops[0].link_loop_next)
        return sorted_boundary_loops
    
    
    def get_boundary_uv_points(self, uv_layer):
        loops = set()
        for vert in self.vertices:
            loops = loops.union(vert.link_loops[:]) # Slow?
        boundary_loops = [loop for loop in loops if Island.is_uv_loop_boundary(loop, uv_layer)]
        sorted_boundary_loops = [boundary_loops[0]]
        sorted_boundary_uv_loops = [boundary_loops[0][uv_layer]]
        i = 0
        while len(sorted_boundary_loops) < len(boundary_loops):
            i += 1
            if i > 1000:
                print("Too many iterations")
                break
            next_loop = sorted_boundary_loops[-1].link_loop_next
            if Island.is_uv_loop_boundary(next_loop, uv_layer):
                sorted_boundary_loops.append(next_loop)
                sorted_boundary_uv_loops.append(next_loop[uv_layer])
            else:
                #sorted_boundary_loops.append(next_loop.link_loop_next)
                sorted_boundary_loops.append(next_loop.link_loops[0].link_loop_next)
                sorted_boundary_uv_loops.append(next_loop.link_loops[0].link_loop_next[uv_layer])
        return sorted_boundary_uv_loops


    def get_inner_points(self):
        pass


    def __repr__(self):
        return str([p.uv for p in self.boundary_uv_points])


    @classmethod
    def is_loop_boundary(cls, loop):
        #diff_1 = loop_a.vert.co - loop_b.link_loop_next.vert.co
        #if max(diff_1) or -min(diff_1) > 0.001:
        #    return False
        #diff = loop_a.link_loop_next.co - loop_b.vert.co
        #if max(diff_1) or -min(diff_1) > 0.001:
        #    return False
        if not Island.are_vectors_equal(loop.vert.co, loop.link_loops[0].link_loop_next.vert.co):
            return False
        if not Island.are_vectors_equal(loop.link_loop_next.vert.co, loop.link_loops[0].vert.co):
            return False
        return True
    
    @classmethod
    def is_uv_loop_boundary(cls, loop, uv_layer):
        if len(loop.link_loops) == 0: # It's assumed that if it's a boundary loop, it's an uv boundary loop
            return True
        if not Island.are_vectors_equal(loop[uv_layer].uv, loop.link_loops[0].link_loop_next[uv_layer].uv):
            return False
        if not Island.are_vectors_equal(loop.link_loop_next[uv_layer].uv, loop.link_loops[0][uv_layer].uv):
            return False
        return True
        

    @classmethod
    def are_vectors_equal(cls, vec_a, vec_b):
        diff = vec_b - vec_a
        return max(diff) > 0.001 or -min(diff) > 0.001



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
            data_to_send = { "command":"set_multiple_parameters", "parameters":[], "image_name":data["image_name"] }
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
            MML.inform("Warning: Expected data of size {}, got {}".format(len(img.pixels), len(data)))
            img.scale(size, size)
        img.pixels.foreach_set([byte / 255.0 for byte in data])
        img.pack()
        img.update()
        bpy.context.view_layer.update()
        bpy.context.scene.view_layers.update()
        MML.inform("Image replaced in {} seconds.".format(time.time() - t0))


    @classmethod
    def initialize_parameters(self, data):
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
