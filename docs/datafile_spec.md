# ODVertexInfo.txt Format Specification

ODVertexInfo.txt is a file written to by copy plugins and read from paste plugins. It contains whatever data was able to be gathered from the program to represent the geometry.

The file is located in the standard system temp directory, for example in Python this is found using

```python
import tempfile

tempfile.gettempdir()
```

## Format overview:
```
VERTICES:#number of vertices(points)
x y z (of each vertex)
POLYGONS:#number of polygons
comma separate list of each vertid in the polygon;;materialname;;polytype (which can be FACE, SubD, or CCSS)
WEIGHT:name of weightmap
weight of vertice (in same order as VERTICES)
MORPH:name of morphmap
deltax deltay deltaz
UV:name of uvmap:number of uv coordinates
u v:polyid:pntid (for discontinuous UVs) or
u v:pntid        (for continuous UVs)
VERTEXNORMALS:# of vertexnormals
x y z (for each normal)
VERTEXCOLORS:# of vertexcolors;DEF:r g b
r g b a;PNT:pntid (for each color, each component is 0-1 float. If all you have is r g b, set 'a' to 1)
```

### Example data format for a box:

The first 4 vertices are colored red, green, blue and black in that order. Other vertices are white.

```
VERTICES:8
-0.5 -0.5 -0.5
-0.5 -0.5 0.5
-0.5 0.5 0.5
-0.5 0.5 -0.5
0.5 -0.5 -0.5
0.5 -0.5 0.5
0.5 0.5 0.5
0.5 0.5 -0.5
POLYGONS:6
0,1,2,3;;Default;;FACE
0,4,5,1;;Default;;FACE
1,5,6,2;;Default;;FACE
3,2,6,7;;Default;;FACE
0,3,7,4;;Default;;FACE
4,7,6,5;;Default;;FACE
WEIGHT:simpleweights
1.0
1.0
1.0
1.0
1.0
1.0
1.0
1.0
UV:txuvmap:24
0.339743584394 0.339743584394:PLY:0:PNT:0
0.660256385803 0.339743584394:PLY:0:PNT:1
0.660256385803 0.660256385803:PLY:0:PNT:2
0.339743584394 0.660256385803:PLY:0:PNT:3
0.660256385803 0.326923072338:PLY:1:PNT:5
0.339743584394 0.326923072338:PLY:1:PNT:1
0.00641027092934 0.339743584394:PLY:3:PNT:3
0.00641027092934 0.660256385803:PLY:3:PNT:2
0.326923072338 0.660256385803:PLY:3:PNT:6
0.326923072338 0.339743584394:PLY:3:PNT:7
0.673076927662 0.00641025649384:PLY:4:PNT:0
0.993589758873 0.00641025649384:PLY:4:PNT:4
0.673076927662 0.339743584394:PLY:5:PNT:4
0.673076927662 0.660256385803:PLY:5:PNT:7
0.993589758873 0.660256385803:PLY:5:PNT:6
0.993589758873 0.339743584394:PLY:5:PNT:5
0.339743584394 0.00641025649384:PNT:0
0.660256385803 0.00641025649384:PNT:4
0.00641027092934 0.00641025649384:PNT:1
0.326923072338 0.00641025649384:PNT:5
0.326923072338 0.326923072338:PNT:6
0.00641027092934 0.326923072338:PNT:2
0.673076927662 0.326923072338:PNT:3
0.993589758873 0.326923072338:PNT:7
MORPH:simplemorph
None
None
0.0 0.290000021458 0.0
0.0 0.290000021458 0.0
None
None
0.0 0.290000021458 0.0
0.0 0.290000021458 0.0
VERTEXCOLORS:4;DEF:1 1 1 1
1 0 0 1;PNT:0
0 1 0 1;PNT:1
0 0 1 1;PNT:2
0 0 0 1;PNT:3
```

## Important notes:

Different DCC applications may have different conventions regarding
* Vertex ordering of front/back faces (winding order)
* Coordinate system handedness. (Is Y up? Z up?)

ODVertexInfo.txt has to be unambiguous, so each plugin knows how to interpret the data inside.

For this reason, plugins must import/export the geometry making conversions to conform to the following conventions:
* Front facing polygons use counter-clockwise (CCW) vertex order.
* +Y extends upwards, +Z extends in the direction of the front of the model and +X extends to the left-hand side of the model (From the model's perspective)

```
     Y (up)
     ↑
     |
     |
     •----→ X (right)
    /
   /
  Z (forward)
```

### Example implications:

#### Blender

Blender stores vertices in CCW order, so it can export and import the vertex data as-is.

Blender uses the Z is up convention, so it needs to ensure vertex positions and normals are exported in such a way that Y coordinates correspond to 'up' instead of Z. When importing it also has to make the reverse conversion

#### Houdini

Houdini stores vertices in CW order, so it must flip the face direction before exporting and flip them back when importing.

Houdini uses the Y-up convention, so vertex components can be exported and imported as-is.
