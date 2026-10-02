#!/usr/bin/env python3
"""Read-only CAD / PCB coordinate and mesh validation; requires KiCad/FreeCAD.
Run /usr/bin/python3 scripts/validate_mechanical_pcb.py. No hardware validation.
"""
from pathlib import Path
import json,sys
sys.path.extend(['/usr/lib/freecad/lib','/usr/lib/freecad-python3/lib'])
import FreeCAD as App,pcbnew as pcb
root=Path(__file__).resolve().parents[1]
params=json.loads((root/'mechanical/parameters.json').read_text())
b=pcb.LoadBoard(str(root/'electronics/macropad.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
checks=[]
def check(name,passed,**details):checks.append({'check':name,'passed':bool(passed),**details})
for i,(x,y) in enumerate(params['keys'],1):
 p=fps['SW'+str(i)].GetPosition();q=(pcb.ToMM(p.x),pcb.ToMM(p.y));check('Switch '+str(i),abs(x-q[0])+abs(y-q[1])<1e-6,pcb_xy=q,cad_xy=[x,y])
for i,(x,y) in enumerate(params['mounts'],1):
 p=fps['H'+str(i)].GetPosition();q=(pcb.ToMM(p.x),pcb.ToMM(p.y));check('Mount '+str(i),abs(x-q[0])+abs(y-q[1])<1e-6,pcb_xy=q,cad_xy=[x,y])
d=App.openDocument(str(root/'mechanical/FIELD13_assembly.FCStd'))
board=next(o for o in d.Objects if 'Main_PCB_envelope' in o.Name)
box=b.GetBoardEdgesBoundingBox();eb=[pcb.ToMM(box.GetX()),pcb.ToMM(box.GetY()),pcb.ToMM(box.GetRight()),pcb.ToMM(box.GetBottom())]
sb=board.Shape.BoundBox;cb=[sb.XMin,sb.YMin,sb.XMax,sb.YMax]
check('Board outline envelope',all(abs(a-c)<.06 for a,c in zip(eb,cb)),pcb_xy_bounds=eb,cad_xy_bounds=cb)
manifest=json.loads((root/'mechanical/assembly_manifest.json').read_text())
check('Every CAD part valid',all(x['valid'] for x in manifest),part_count=len(manifest))
r=json.loads((root/'mechanical/validation.json').read_text());check('Every named clearance passes',all(t['pass'] for t in r['critical_clearance_checks']),check_count=len(r['critical_clearance_checks']))
check('13 hot-swap footprints',len([f for f in fps if f.startswith('SW')])==13)
result={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','checks':checks,'not_tested':'Physical fit, component envelope accuracy, hardware, RF, input injection'}
(root/'mechanical/cad_pcb_alignment.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));sys.exit(0 if result['status']=='PASS' else 1)
