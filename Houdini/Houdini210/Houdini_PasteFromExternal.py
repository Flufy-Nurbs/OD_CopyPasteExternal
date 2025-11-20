import toolutils, tempfile, os, sys

# OD_CopyPasteExternal Houdini IMPORT script (Paste from external program)
# Tested with Houdini 21.0 using Blender 4.5.3 as a source.
# Instructions:
#   1.  Right-click an empty area of the tool shelf and click "New Tool..."
#   2.  In the Options tab, provide a Label like "Paste (from External)"
#   3.  In the Script tab, paste this entire document to the large text block provided.
#       Ensure Script Language is set to "Python".
#   Pressing this button will paste previously copied geometry from a OD_CopyPasteExternal copy.
#   The paste location follows the viewport focus,
#       if you are in Object scope (i.e. /obj/), it will create a geo object which has the wrangle node that emits the geometry.
#       if you are in Geometry scope (e.g. /obj/geo1/), it will create the wrangle node in that location.
#       if you are in Solaris scope (i.e. /stage/), it will create a SOP Create node and generate the wrangle node within that.
#       Other scopes are not supported and will cause an error.
#   The wrangle SOP is given a "Reload Geometry" button that you can click to rebuild the cached geometry using that latest contents of ODVertexData.txt

parentNode = toolutils.sceneViewer().pwd()

# Find parent SOP, i.e. where to add the geometry. Uses active node in the scene viewport and confirms that it is a SOP context:

if parentNode.childTypeCategory().name() == "Object":
    parentNode = parentNode.createNode("geo")
    parentNode.moveToGoodPosition()
elif parentNode.childTypeCategory().name() == "Lop":
    parentNode = parentNode.createNode("sopcreate")
    parentNode.moveToGoodPosition()
    parentNode = parentNode.node("./sopnet/create/")
elif parentNode.childTypeCategory().name() != "Sop":
    hou.ui.displayMessage("The active scene view needs to be in a SOP, OBJ or LOP context to paste", severity=hou.severityType.Error, title="Error")
    
# Create a attribute wrangle that runs on detail, this contains the VEX script snippet that generates the geometry.

node = parentNode.createNode("attribwrangle", "pastefromexternal1")
node.setUserData("nodeshape", "tabbed_left")  # Make node look like a little file folder icon.

# Hide node's parameter interface and add our own ("Reload Geometry" button, etc):
templateGroup = node.parmTemplateGroup()
for p in templateGroup.entries():
    p.hide(True)
    templateGroup.replace(p.name(), p)
    
templateGroup.append(hou.ButtonParmTemplate("btnReloadGeometry",
    "Reload Geometry",
    script_callback_language=hou.scriptLanguage.Python,
    script_callback='''import toolutils, tempfile, os, sys
    
# Reads ODVertexData.txt and builds a string array "vexlines" which contains lines VEX code that will generate the geometry from a detail wrangle node.

vexlines = []

lines = []
with open(os.path.join(tempfile.gettempdir(), "ODVertexData.txt"), "r") as f:
    lines = f.readlines()

vertline = []; polyline = []; uvMaps = []; morphMaps = []; weightMaps = []; vertexnormals = []; vertexcolors = []

count = 0
for line in lines:
    if line.startswith("VERTICES:"):
        vertline.append([int(line.strip().split(":")[1].strip()), count])
    if line.startswith("POLYGONS:"):
        polyline.append([int(line.strip().split(":")[1].strip()), count])
    if line.startswith("UV:"):
        uvMaps.append([line.strip().split(":")[1:], count])  # changed this to add the # of uv coordinates into the mix
    if line.startswith("MORPH"):
        morphMaps.append([line.split(":")[1].strip(), count])
    if line.startswith("WEIGHT"):
        weightMaps.append([line.split(":")[1].strip(), count])
    if line.startswith("VERTEXNORMALS:"):
        vertexnormals.append([int(line.strip().split(":")[1].strip()), count])
    if line.startswith("VERTEXCOLORS:"):
        vertexcolors.append([int(line.strip().split(":")[1].strip()), count])
    count += 1

for verts in vertline:
    for i in range(verts[1] + 1, verts[1] + verts[0] + 1):
        x = lines[i].split(" ")
        vexlines.append(f'addpoint(0, set({float(x[0])}, {float(x[1])}, {float(x[2].strip())}));')
        
if len(vertexnormals) > 0:
    vexlines.append(f'addpointattrib(0, "N", set(0, 0, 0), "normal");')
        
for normals in vertexnormals:    
    for p, i in enumerate(range(normals[1] + 1, normals[1] + normals[0] + 1)):
        x = lines[i].split(" ")
        vexlines.append(f'setpointattrib(0, "N", {p}, set({float(x[0])}, {float(x[1])}, {float(x[2].strip())}));')

if len(vertexcolors) > 0:
    vexlines.append(f'addpointattrib(0, "Cd", set(1, 1, 1), "color");')
        
for colors in vertexcolors:    
    for p, i in enumerate(range(colors[1] + 1, colors[1] + colors[0] + 1)):
        x = lines[i].split(" ")
        vexlines.append(f'setpointattrib(0, "Cd", {p}, set({float(x[0])}, {float(x[1])}, {float(x[2].strip())}));')
        
polygonindices = []
for polygons in polyline:
    for i in range(polygons[1] + 1, polygons[1] + polygons[0] + 1):
        parts = lines[i].split(";"); # [0] = indices, [2] = material, [4] = type
        polygonindices.append(list(map(int, parts[0].split(",")[::-1])))
        if(parts[4].strip() != "FACE"): # Provide error message for polygons that are not faces, those aren't supported yet.
            print(f'{parts[4].strip()} was not "FACE", treating as a primitive anyway')
            
        vexlines.append("{")
        vexlines.append(f'int id = addprim(0, "poly", reverse({{{parts[0]}}}));')
        if len(parts[2]) > 0 and parts[2].casefold() != "DEFAULT".casefold():
            vexlines.append(f'setprimattrib(0, "shop_materialpath", id, "{parts[2]}");')            
        vexlines.append("}")
   
for i, uvMap in enumerate(uvMaps):
    vexlines.append(f'append(s[]@uvLayerNames, "{uvMap[0][0]}");')

    uvAttributeName = "uv" if i == 0 else f"uv{i + 1}"
    vexlines.append(f'addvertexattrib(0, "{uvAttributeName}", set(0, 0, 0), "texturecoord");')
    
    count = 0
    for _ in range(int(uvMap[0][1])):
        line = lines[uvMap[1]+1+count]
        split = line.split(":")
        if len(split) > 3:
            plyid = int(split[2]);
            vexlines.append(f'setvertexattrib(0, "{uvAttributeName}", {plyid}, {polygonindices[plyid].index(int(split[4]))}, set({split[0].replace(" ", ",")}, 0));')
        else:
           print("TODO: UVs without plyid")
        count += 1

hou.pwd().setParms({"snippet" : os.linesep.join(vexlines)}) # Concatenate the lines of VEX and set as this node's 'snippet' parameter, i.e. the VEXcode that it will execute.
'''
))
node.setParmTemplateGroup(templateGroup)

node.setParms({ "class": 0 }) # "Run on: Detail"

node.parm("btnReloadGeometry").pressButton();   # Progammatically 'push' the ReloadGeometry button to give it initial geometry.

# Place the node in a convenient location and select it:
node.moveToGoodPosition()
hou.clearAllSelected()
node.setSelected(True)
