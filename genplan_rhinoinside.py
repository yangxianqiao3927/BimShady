# Run inside Revit Python environment (pyRevit / RevitPythonShell)
# Requires Rhino.Inside to be installed and loaded.

import json
import sys
import clr

# --- Load Rhino.Inside ---
try:
    clr.AddReference("RhinoInside.Revit")
    import RhinoInside
    RhinoInside.Revit.Initialize()
except:
    raise Exception("Rhino.Inside.Revit is not loaded. Open Revit → Add-Ins → Rhino.Inside first.")

# --- Load RhinoCommon ---
clr.AddReference("RhinoCommon")
import Rhino
import scriptcontext as sc

# --- JSON floor plan definition ---
json_text = r'''
{
  "walls": [
    {
      "id": "ext_top",
      "type": "exterior",
      "start": [0, 20],
      "end": [24, 20]
    },
    {
      "id": "ext_bottom",
      "type": "exterior",
      "start": [0, 0],
      "end": [24, 0]
    },
    {
      "id": "ext_left",
      "type": "exterior",
      "start": [0, 0],
      "end": [0, 20]
    },
    {
      "id": "ext_right",
      "type": "exterior",
      "start": [24, 0],
      "end": [24, 20]
    },
    {
      "id": "int_vertical",
      "type": "interior",
      "start": [5, 0],
      "end": [5, 20]
    },
    {
      "id": "int_partition_1",
      "type": "interior",
      "start": [0, 13],
      "end": [5, 13]
    },
    {
      "id": "int_partition_2",
      "type": "interior",
      "start": [0, 7],
      "end": [5, 7]
    }
  ],
  "metadata": {
    "units": "feet",
    "width": 24,
    "height": 20,
    "description": "Floor plan sketch interpreted into wall segments."
  }
}
'''
data = json.loads(json_text)

# --- Prepare Rhino document ---
rhino_doc = Rhino.RhinoDoc.ActiveDoc

# Create a layer for the plan
layer_name = "FloorPlan"
layer_index = rhino_doc.Layers.FindByFullPath(layer_name, True)

if layer_index < 0:
    new_layer = Rhino.DocObjects.Layer()
    new_layer.Name = layer_name
    layer_index = rhino_doc.Layers.Add(new_layer)

rhino_doc.Layers.SetCurrentLayerIndex(layer_index)

# --- Generate geometry ---
created_ids = []

for w in data["walls"]:
    sid = w["id"]
    x1, y1 = w["start"]
    x2, y2 = w["end"]

    p1 = Rhino.Geometry.Point3d(x1, y1, 0)
    p2 = Rhino.Geometry.Point3d(x2, y2, 0)

    line_curve = Rhino.Geometry.LineCurve(p1, p2)

    obj_id = rhino_doc.Objects.AddCurve(line_curve)
    created_ids.append(obj_id)

# --- Finalize ---
rhino_doc.Views.Redraw()

print("Generated {} wall curves in Rhino.".format(len(created_ids)))
