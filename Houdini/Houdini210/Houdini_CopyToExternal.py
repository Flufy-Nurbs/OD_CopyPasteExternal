import tempfile, os, random, sys, re

# OD_CopyPasteExternal Houdini EXPORT script (Copy to external program)
# Tested with Houdini 21.0 using Blender 4.5.3 as a destination.
# Instructions:
#   1.  Right-click an empty area of the tool shelf and click "New Tool..."
#   2.  In the Options tab, provide a Label like "Paste (from External)"
#   3.  In the Script tab, paste this entire document to the large text block provided.
#       Ensure Script Language is set to "Python".
#   Pressing this button will copy the currently selected SOP for use with another program via its corresponding IMPORT script.

#   Features and Limitations:
#   Only one SOP must be selected at a time.
#   Only supports polygon face geometry, no bezier curves or NURBS surfaces etc.
#   Exports point positions, normals (N) and colors (Cd). Does not convert vertex normals to point normals.
#   Exports named material assignments by the path to the material node (shop_materialpath attribute).
#   Exports the vertex UV coordinate attributes (uv).

if len(hou.selectedNodes()) != 1:
    hou.ui.displayMessage("There must be exactly one selected node.", severity=hou.severityType.Error, title="Error")
else:
    node = hou.selectedNodes()[0];
    
    if not isinstance(node, hou.SopNode):
        hou.ui.displayMessage("Selected node must be a SOP node.", severity=hou.severityType.Error, title="Error")
    else:
        rev = node.node("..").createNode("reverse") # Houdini has faces flipped compared how other programs (E.g. Blender) export, so we compensate for this using a reverse node to flip the polygon winding order.
        rev.setInput(0, node)
        geo = rev.geometry()
        with open(os.path.join(tempfile.gettempdir(), "ODVertexData.txt"), "w") as f:

            texturecoordAttribs = [
                attrib
                for attrib in geo.vertexAttribs()
                if attrib.options().get("type") == "texturecoord"
            ]
            
            pointNormals = [] if geo.findPointAttrib("N") else None
            pointColors = [] if geo.findPointAttrib("Cd") else None
            
            print(f'VERTICES:{len(geo.points())}', file=f)
            for p in geo.points():
                print(f'{p.position()[0]} {p.position()[1]} {p.position()[2]}', file=f)
                if pointNormals != None:
                    pointNormals.append(p.attribValue("N"))
                if pointColors != None:
                    pointColors.append(p.attribValue("Cd"))
                    
            polygons = []
            polygonVertexPointIndices = []
            polygonUvEntries = {}
            for p in geo.prims():
                vertexPointIndices = []
                if isinstance(p, hou.Face):
                    for v in p.vertices():
                        vertexPointIndices.append(v.point().number())
                        for uvAttrib in texturecoordAttribs:
                            uvValue = v.attribValue(uvAttrib)
                            polygonUvEntries.setdefault(uvAttrib.name(), []).append(f'{uvValue[0]} {uvValue[1]}:PLY:{len(polygons)}:PNT:{v.point().number()}')
                            
                    materialName = p.attribValue("shop_materialpath") if geo.findPrimAttrib("shop_materialpath") else ""
                    polygons.append(f'{",".join(map(str, vertexPointIndices))};;{materialName};;FACE')
                else:
                    print(f'Skipping unsupported primitive type "{p}".')                    
                polygonVertexPointIndices.append(vertexPointIndices)
                
            print(f'POLYGONS:{len(polygons)}', file=f)
            for p in polygons:
                print(p, file=f)
                
            for uvAttrib in texturecoordAttribs:                
                print(f'UV:{uvAttrib.name()}:{len(polygonUvEntries[uvAttrib.name()])}', file=f)
                for u in polygonUvEntries[uvAttrib.name()]:
                    print(f'{u}', file=f)
                    
            if pointNormals != None:
                print(f'VERTEXNORMALS:{len(geo.points())}', file=f)
                for n in pointNormals:
                    print(f'{n[0]} {n[1]} {n[2]}', file=f)
                    
            if pointColors != None:
                print(f'VERTEXCOLORS:{len(geo.points())}:DEF:1 1 1 1', file=f)
                for c in pointColors:
                    print(f'{c[0]} {c[1]} {c[2]} 1.0', file=f)
                    
        rev.destroy()
