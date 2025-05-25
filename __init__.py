bl_info = {
    "name": "Material Maker Linker",
    "author": "Crunchsoft",
    "version": (0, 1),
    "blender": (3, 4, 0),
    "location": "ImageEditor > Sidebar > MML",
    "description": "Link between Material Maker's ptex materials and Blender's image editor.",
    "warning": "",
    "category": "Paint",
}

if "bpy" in locals():
    import importlib
    importlib.reload(ui_mml)
    importlib.reload(mml_main)
    importlib.reload(mml_client)
    importlib.reload(mml_sender)
else:
    import bpy
    from . import ui_mml
    from . import mml_main as mml
    from . import mml_client
    from . import mml_sender

classes = [
    mml.MMLProperties,
    mml.MMLParameters,
    ui_mml.MMLPanel,
    mml_sender.MMLSubmit,
    mml_sender.MMLRequestRender,
    mml_client.OBJECT_OT_connect,
    ui_mml.UI_UL_ParamsList,
    mml_client.OBJECT_OT_update_islands
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Image.mml_remote_parameters = bpy.props.CollectionProperty(type=mml.MMLParameters)
    bpy.types.Image.mml_local_parameters = bpy.props.CollectionProperty(type=mml.MMLParameters) # A local parameter is one from a non-remote node
    bpy.types.Image.mml_properties = bpy.props.PointerProperty(type=mml.MMLProperties, name="MML Properties", description="MML properties")
    bpy.types.Image.params_list_index = bpy.props.IntProperty(name = "Index for ParamList",
                                             default = 0)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Image.mml_remote_parameters
    del bpy.types.Image.mml_local_parameters
    del bpy.types.Image.mml_properties
    del mml_sender.OBJECT_OT_send.mml_properties

    
if __name__ == '__main__':
        register()

