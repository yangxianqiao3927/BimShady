# Revit Python script — create walls from JSON definition
# Works in pyRevit or RevitPythonShell
import json
import sys

# Try to get the Revit Document in several runtimes
doc = None
uidoc = None
try:
    # pyRevit / standard hosted environment
    doc = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument
except NameError:
    try:
        # RevitPythonShell / RevitServices
        import clr
        clr.AddReference("RevitServices")
        from RevitServices.Persistence import DocumentManager
        from RevitServices.Transactions import TransactionManager
        doc = DocumentManager.Instance.CurrentDBDocument
        uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
    except Exception:
        pass

if doc is None:
    raise RuntimeError("Could not find Revit document. Run inside pyRevit or RevitPythonShell.")

# Import Revit API
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog

# --- JSON input (use your JSON) ---
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

# --- Utility helpers ---
def find_level_by_elevation(doc, elevation_feet, tol=1e-6):
    """Return existing Level at elevation (feet) or None."""
    collector = FilteredElementCollector(doc).OfClass(Level)
    for lvl in collector:
        if abs(lvl.Elevation - elevation_feet) < tol:
            return lvl
    return None

def get_or_create_base_level(doc, elevation_feet=0.0):
    lvl = find_level_by_elevation(doc, elevation_feet)
    if lvl is not None:
        return lvl
    # create new level
    lvl = Level.Create(doc, elevation_feet)
    lvl.Name = "Auto_Level_{:.2f}ft".format(elevation_feet)
    return lvl

def pick_wall_type(doc, preferred_name=None):
    collector = FilteredElementCollector(doc).OfClass(WallType)
    types = list(collector)
    if not types:
        raise RuntimeError("No WallType found in document.")
    if preferred_name:
        for t in types:
            if t.Name == preferred_name:
                return t
    # fallback: return first wall type
    return types[0]

# --- Preparation: choose wall type and level ---
# Optional: change to the exact wall type name you prefer present in your project
WALL_TYPE_NAME = None  # e.g. 'Generic - 8"' or None to pick the first available

# Use metadata height if present (unconnected height for created walls)
metadata = data.get("metadata", {})
height_ft = None
if "height" in metadata:
    try:
        height_ft = float(metadata["height"])
    except Exception:
        height_ft = None

# Convert height to feet (metadata units declared as 'feet' in our JSON)
# If the user uses other units you'd need to convert here.

# Start Revit transaction
t = Transaction(doc, "Create walls from JSON")
t.Start()

try:
    # ensure we have a base level at elevation 0
    base_level = get_or_create_base_level(doc, elevation_feet=0.0)
    wall_type = pick_wall_type(doc, WALL_TYPE_NAME)

    created = []
    for w in data.get("walls", []):
        sid = w.get("id", "wall")
        start = w.get("start")
        end = w.get("end")
        if not start or not end:
            print("Skipping wall {}: missing start/end".format(sid))
            continue

        x1, y1 = float(start[0]), float(start[1])
        x2, y2 = float(end[0]), float(end[1])

        # Revit XYZ: X = x, Y = y, Z = elevation (0)
        p1 = XYZ(x1, y1, 0.0)
        p2 = XYZ(x2, y2, 0.0)

        curve = Line.CreateBound(p1, p2)

        # Create the wall. The Wall.Create method needs a Document, Curve, WallTypeId, LevelId, height, offset, flip
        # We will set unconnected height if metadata height exists, otherwise the WallType's default height is used.
        new_wall = Wall.Create(doc, curve, wall_type.Id, base_level.Id, 10.0, 0.0, False, False)
        # new_wall is created as unconnected; change UnconnectedHeight if metadata height provided
        if height_ft is not None:
            try:
                # UnconnectedHeight property expects double in feet
                new_wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).Set(height_ft)
            except Exception:
                # Some walls use WALL_HEIGHT_TYPE or WALL_USER_HEIGHT_PARAM
                try:
                    param = new_wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)
                    if param and not param.IsReadOnly:
                        # attempting to set via this param will not accept a raw double; skip
                        pass
                except Exception:
                    pass

        # (optional) set the wall location line to center
        try:
            new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM)  # just probe
            # Set location line to center if available via Wall.Location
            loc = new_wall.Location
            # There is a LocationCurve, we can set its curve if needed — not required here.
        except Exception:
            pass

        # store id & element info
        created.append((sid, new_wall.Id.IntegerValue))
        print("Created wall '{}' -> ElementId {}".format(sid, new_wall.Id.IntegerValue))

    t.Commit()
    print("Created {} walls.".format(len(created)))

    # Provide a simple Revit UI notification if available
    try:
        TaskDialog.Show("Create Walls", "Created {} walls from JSON.".format(len(created)))
    except Exception:
        pass

except Exception as ex:
    t.RollBack()
    raise

# end of script
