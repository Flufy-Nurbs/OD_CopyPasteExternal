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
#       if you are in Geometry scope (e.g. /obj/geo1/), it will create a python node 'pastefromexternal' which will output the geometry.
#       if you are in Object scope (i.e. /obj/), it will create a geo node, inside which will contain the 'pastefromexternal' python node.
#       if you are in Solaris scope (i.e. /stage/), it will create a "SOP Create" node, inside which will contain the 'pastefromexternal' python node.
#       Other scopes are not supported and will cause an error.
#   The python SOP is given a "Reload Geometry" button that you can click to rebuild the cached geometry using that latest contents of ODVertexData.txt.
#   The python SOP will also merge its output with the first input it is given.
#   Note: Any time the python SOP re-cooks it will also reload the geometry from the clipboard.

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

node = parentNode.createNode("python", "pastefromexternal1")
node.setUserData("nodeshape", "tabbed_left")  # Make node look like a little file folder icon.

# Hide node's parameter interface and add our own ("Reload Geometry" button, etc):
templateGroup = node.parmTemplateGroup()
for p in templateGroup.entries():
    p.hide(True)
    templateGroup.replace(p.name(), p)
    
templateGroup.append(hou.ButtonParmTemplate("btnReloadGeometry", "Reload Geometry", script_callback_language=hou.scriptLanguage.Python,
    script_callback="hou.pwd().cook(force=True)"
))

node.setParmTemplateGroup(templateGroup)

node.setParms({ "python": '''
import toolutils, tempfile, os, sys, re
node = hou.pwd()
geo = hou.Geometry()

lines = []
with open(os.path.join(tempfile.gettempdir(), "ODVertexData.txt"), "r") as line:
    for header in map(lambda l: l.rstrip().split(":"), line):
        if header[0] == "VERTICES":
            for _ in range(int(header[1])):
                xyz = next(line).split(" ")
                point = geo.createPoint()
                point.setPosition( [ float(xyz[0]), float(xyz[1]), float(xyz[2].rstrip()) ])
        elif header[0] == "POLYGONS":
            for _ in range(int(header[1])):
                groups = next(line).split(";;")
                polygon = geo.createPolygon()
                for pointNum in map(int, groups[0].split(",")):
                    polygon.addVertex(geo.point(pointNum))
        elif header[0] == "UV":
            uvAttr = geo.addAttrib(hou.attribType.Vertex, header[1], (0.0, 0.0, 0.0))
            uvAttr.setOption("type", "texturecoord")
            
            for _ in range(int(header[2])):
                uvEntry = next(line).split(":")
                polygon = geo.prim(int(uvEntry[2]))

                for v in polygon.vertices():
                    if v.point().number() == int(uvEntry[4]):
                        uv = uvEntry[0].split(" ")
                        v.setAttribValue(uvAttr, (float(uv[0]), float(uv[1]), 0.0))
                        break
        elif header[0] == "VERTEXNORMALS":
            normalAttr = geo.addAttrib(hou.attribType.Point, "N", (0.0, 0.0, 0.0))
            normalAttr.setOption("type", "normal")
            for i in range(int(header[1])):
                rgba = next(line).split(" ")
                geo.point(i).setAttribValue(normalAttr, (float(xyz[0]), float(xyz[1]), float(xyz[2].rstrip())))
        elif header[0] == "VERTEXCOLORS":
            defaultRgba = header[2].split(" ") if len(header) > 2 else [0.0, 0.0, 0.0, 1.0]
            colorAttr = geo.addAttrib(hou.attribType.Point, "Cd", (float(defaultRgba[0]), float(defaultRgba[1]), float(defaultRgba[2]), float(defaultRgba[3])))
            colorAttr.setOption("type", "color")
            for i in range(int(header[1])):
                rgba = next(line).split(" ")
                geo.point(i).setAttribValue(colorAttr, (float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3].rstrip())))
                               
hou.sopNodeTypeCategory().nodeVerb("reverse").execute(geo, [geo])
                    
node.geometry().merge(geo)
''' })

#node.parm("btnReloadGeometry").pressButton();   # Progammatically 'push' the ReloadGeometry button to give it initial geometry.

# Place the node in a convenient location and select it:
node.moveToGoodPosition()
hou.clearAllSelected()
node.setSelected(True)
