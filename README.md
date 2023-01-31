[![](http://img.youtube.com/vi/KLEHdDST6gA/0.jpg)](http://www.youtube.com/watch?v=KLEHdDST6gA "Video Title")

# Material Maker Linker
Material Maker Linker is an addon that connects (through a websocket-based network connection) to a special Material Maker client [available here](https://github.com/Silvergust/MM-Linker-Godot/tree/master) (original is [here](https://github.com/RodZill4/material-maker)), allowing the user to load a PTex file and manipulate its parameters within Blender, automatically apply those changes in Material Maker and in turn send back to Blender a render of the updated material's textures, overwriting existing textures, allowing you to have theoretically real-time feedback while making use of MM's versatile procedural texture generation tools.

To use it, first install the addon in this repository (as with any addon, through the "preferences -> addons -> install" option or by saving the files to Blender's addons folder) and setting up the MM client (by modifying the original MM client as stated in [this repository](https://github.com/Silvergust/MM-Linker-Godot/tree/master) or by unzipping one of its [release versions](https://github.com/Silvergust/MM-Linker-Godot/releases/tag/Main_Release)). Afterwards, open the "Blender Linker" menu from MM's Tools panel, then in Blender you select the image you want to modify within the Image Editor, go to the "MML" panel in the properties tab (`N` button) and press the "Connect to MM" button, then if it's the first time you modify this image press the "Submit and Reset Parameters" button, this will load each parameter of each node in the PTex file, ready to be modified.

For ease of use you can select to show only parameters from a remote node (presumably with an easily identifiable name), but keep in mind that the majority of nodes available online do not use remote nodes. After each render request (either through the "Request Render" button or by modifying a parameter with the "Auto-Update" toggle on) it will attempt to retrieve a render of each selected map (according to the "Albedo", "Metallicity" etc. toggles) and save them on image datablocks named with a suffix following the maps's name, e.g. doing this on "Wood" will create "Wood_roughness", "Wood_normal", etc., the exception to this are albedo maps, which are saved on that same datablock (e.g. "Wood" and not "Wood_albedo"). It is not necessary to manually create additional datablocks. Pressing the "Submit and Reset Parameters" button again will restore parameters to whatever they are in the PTex file, press "Submit PTex to MM" if you want to load it without having them reset.
Requires [aaugustin's websockets library](https://github.com/aaugustin/websockets) to work (included in releases, but not in repository).
# Notes and known issues:
* The MM client does not do anything to stop unwanted connections from working, avoid using it on unsecure networks.
* The addon is currently not intended to work with output nodes besides the default Static PBR Material one.
* You activate MM's linker by opening the Blender Linker menu once and it will keep working even if the menu is closed (intentionally, though some features from the main client are removed), however trying to open it again will cause issues, try to restart it instead.
* The addon works under the assumption that there's only one remote node and will not try to retrieve parameters from any other besides the first one it finds.
* The resolution of the rendered images depend on the resolution of its datablock in Blender, it ignores that of Material Maker. (You can change an image's resolution from the Image panel in the Image Editor.)
* Due to a bug, MM will stop rendering properly after a while and will instead send back a 0% alpha image back to Blender, requiring you to restart MM to fix.
* Due to a bug, Sometimes the material will not update "completely" and Blender will only receive a partially modified texture, for example changing brick sizes in a brick texture without changing its mortar. This seems to occur more often in complicated materials.
* Vector parameters are yet to be implemented, as a workaround you can add float parameters to the material to manipulate each of those vectors individually.
* The addon will not always cause the 3D viewport to update properly when modifying some (perhaps most) materials and requires the user to cause an update in some other way (for example, by changing rendering mode in 3D view). Images will still update properly automatically.
* Similarly, material changes will not be reflected in texture properties, thus requirews manually causing an update.
* The transparency in the rendered result will be stored as part of the main (albedo) texture's alpha channel, not an individual transparency map as might be expected from MM's material node.

# TODO
* Implement vector parameter inputs.
* Implement use of multiple remote nodes.
* Implement simultaneous open PTex files.
* Have the addon dentify relevant maps to render on each parameter change.
* Bug and stability fixes, potentially forever.

# Donations
If you find this software useful, please consider an Ethereum donation to the following address: `0xe04946Dfe2cdc98A0c812671B3492a4B21c70c11`

If you find the original Material Maker useful as-is, also consider a donation to that project as well.
