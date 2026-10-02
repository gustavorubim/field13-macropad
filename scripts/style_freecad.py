#!/usr/bin/env python3
"""Optional view styling for the native FreeCAD document, no geometry changes.
Run with FreeCAD's Python or a system Python with FreeCAD libs installed.
For a headless run set QT_QPA_PLATFORM=offscreen; GPU preview may be unavailable.
"""
import sys
from pathlib import Path
sys.path.extend(['/usr/lib/freecad/lib','/usr/lib/freecad-python3/lib'])
import FreeCAD as App,FreeCADGui as Gui
Gui.showMainWindow()
root=Path(__file__).resolve().parents[1]
doc=App.openDocument(str(root/'mechanical/FIELD13_assembly.FCStd'))
for obj in doc.Objects:
    if hasattr(obj,'MaterialColor'):
        obj.ViewObject.ShapeColor=tuple(obj.MaterialColor)[:3]
        obj.ViewObject.LineColor=(.12,.14,.13)
        obj.ViewObject.DisplayMode='Flat Lines'
    elif obj.TypeId=='Sketcher::SketchObject':
        obj.ViewObject.Visibility=False
    if 'Microphone_bay' in obj.Name or 'Touch_electrode' in obj.Name:
        obj.ViewObject.Visibility=False
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
doc.recompute()
doc.save()
print('Native FreeCAD colors and visibility saved')
