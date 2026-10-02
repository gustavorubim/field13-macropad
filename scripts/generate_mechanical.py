#!/usr/bin/env python3
"""Regenerate all native FreeCAD assembly parts and manufacturing meshes, mm.
Run /usr/bin/python3 scripts/generate_mechanical.py; FreeCAD modules installed.
parameters.json is the single mechanical parameter source. FCStd contains named
named editable BRep solids plus design sketches. Parameters regenerate via JSON.
This is a prototype for fit checking, not a claim of physical validation.
"""
import sys,json,math,os
from pathlib import Path
sys.path.extend(['/usr/lib/freecad/lib','/usr/lib/freecad-python3/lib'])
import FreeCAD as App, Part, Mesh, MeshPart, Sketcher
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'mechanical/parameters.json').read_text())
OUT=ROOT/'mechanical'; (OUT/'stl').mkdir(exist_ok=True); (OUT/'mesh').mkdir(exist_ok=True)
doc=App.newDocument('FIELD13_Assembly')
V=App.Vector
sheet=doc.addObject('Spreadsheet::Sheet','Parameters');sheet.Label='Dimensions (mm) • edit JSON then regenerate'
sheet.set('A1','FIELD 13 / REV A0');sheet.set('A2','Native model + reproducible parameter source')
row=4
for key,value in P.items():
 if isinstance(value,(int,float)):
  sheet.set(f'A{row}',key);sheet.set(f'B{row}',str(value));sheet.setAlias(f'B{row}',key);row+=1
sheet.setColumnWidth('A',220)
parts=[]; printable=[]
def rounded(x,y,w,d,z,h,r):
 b=Part.makeBox(w,d,h,V(x,y,z))
 if r:
  edges=[e for e in b.Edges if len(e.Vertexes)==2 and abs(e.Vertexes[0].Point.z-e.Vertexes[1].Point.z)>h-.001]
  b=b.makeFillet(r,edges)
 return b

def box(x,y,z,w,d,h):return Part.makeBox(w,d,h,V(x,y,z))
def cylinder(x,y,z,r,h):return Part.makeCylinder(r,h,V(x,y,z))
def union(shapes):
 s=shapes[0]
 for x in shapes[1:]:s=s.fuse(x)
 return s.removeSplitter()
def feat(name,shape,color=(.8,.8,.8),kind='component',printit=False):
 obj=doc.addObject('Part::Feature',name);obj.Label=name.replace('_',' ');obj.Shape=shape
 obj.addProperty('App::PropertyString','Role');obj.Role=kind
 obj.addProperty('App::PropertyString','Revision');obj.Revision=P['revision']
 obj.addProperty('App::PropertyString','Source');obj.Source='scripts/generate_mechanical.py + mechanical/parameters.json'
 obj.addProperty('App::PropertyColor','MaterialColor');obj.MaterialColor=color
 parts.append(obj)
 if printit:printable.append(obj)
 return obj
# Preserve design profiles as individually editable native sketches; manufacturing
# solids below are named by process to make manual FreeCAD editing straightforward.
def rounded_sketch(name,x,y,w,d,z,r):
 sk=doc.addObject('Sketcher::SketchObject',name);sk.Placement.Base=V(0,0,z)
 pts=[(x+r,y),(x+w-r,y),(x+w,y+r),(x+w,y+d-r),(x+w-r,y+d),(x+r,y+d),(x,y+d-r),(x,y+r)]
 arcs={1:(x+w-r,y+r,-90,0),3:(x+w-r,y+d-r,0,90),5:(x+r,y+d-r,90,180),7:(x+r,y+r,180,270)}
 for i,p in enumerate(pts):
  q=pts[(i+1)%8]
  if i in arcs:
   cx,cy,a,b=arcs[i];circ=Part.Circle(V(cx,cy,0),V(0,0,1),r);sk.addGeometry(Part.ArcOfCircle(circ,math.radians(a),math.radians(b)),False)
  else:sk.addGeometry(Part.LineSegment(V(p[0],p[1],0),V(q[0],q[1],0)),False)
 return sk
W,D=P['width'],P['depth']; wall=P['wall']; floor=P['floor']; pz=P['plate_z']; pt=P['plate_thickness']
# Replace script syntactic helper below handled by call; native outlines are authorable.
profile_group=doc.addObject('App::DocumentObjectGroup','Design_Profiles')
for args in [('Shell_outer_profile',0,0,W,D,0,P['corner_radius']),('Shell_inner_profile',wall,wall,W-2*wall,D-2*wall,floor,P['corner_radius']-wall),('Plate_outline_profile',wall+P['plate_clearance'],wall+P['plate_clearance'],W-2*(wall+P['plate_clearance']),D-2*(wall+P['plate_clearance']),pz,P['corner_radius']-wall-P['plate_clearance'])]:
 profile_group.addObject(rounded_sketch(*args))
outer=rounded(0,0,W,D,0,pz,P['corner_radius'])
inner=rounded(wall,wall,W-2*wall,D-2*wall,floor,pz+1,P['corner_radius']-wall)
base=outer.cut(inner)
# Perimeter shelf supporting the thin switch plate.
shelf=rounded(wall,wall,W-2*wall,D-2*wall,pz-2.0,2.0,P['corner_radius']-wall).cut(rounded(wall+1.8,wall+1.8,W-2*(wall+1.8),D-2*(wall+1.8),pz-2.1,2.2,P['corner_radius']-wall-1.8))
base=base.fuse(shelf)
for x,y in P['mounts']:
 # PCB landing is top z12; screws enter from the underside.
 post=cylinder(x,y,floor,3.4,P['pcb_z']-floor)
 base=base.fuse(post).cut(cylinder(x,y,-1,1.45,18)).cut(cylinder(x,y,-.01,2.7,1.71))
# Micro-B panel port through rear wall; flexible mount-ear pitch per Adafruit3258.
ux,uz=P['usb_center_x'],P['usb_center_z']
base=base.cut(box(ux-P['usb_opening_width']/2,-1,uz-P['usb_opening_height']/2,P['usb_opening_width'],wall+2,P['usb_opening_height']))
for dx in [-P['usb_mount_pitch']/2,P['usb_mount_pitch']/2]:
 base=base.cut(Part.makeCylinder(1.7,wall+2,V(ux+dx,-1,uz),V(0,1,0)))
# Feet sit in shallow underside pockets. No glue necessary for test fit; tape optional.
for x,y in P['foot_centers']:base=base.cut(cylinder(x,y,-.1,P['foot_diameter']/2+.15,.75))
# Two unobstructed ties retain the USB slack near the front; no conductive hardware by antenna.
for x in [18,90]:
 tie=box(x-3,113,floor,6,4,2.8).cut(box(x-3.1,114,floor+.8,6.2,2,1.2));base=base.fuse(tie)
base=base.removeSplitter();base_obj=feat('01_Base_shell',base,(.82,.84,.79),'printable / GF-ABS or PETG',True)
# Plate inset leaves controlled perimeter fit. Full thickness at switch apertures 1.5.
pc=P['plate_clearance']; plate=rounded(wall+pc,wall+pc,W-2*(wall+pc),D-2*(wall+pc),pz,pt,P['corner_radius']-wall-pc)
for x,y in P['keys']:
 a=P['switch_cutout'];plate=plate.cut(box(x-a/2,y-a/2,pz-.1,a,a,pt+.2))
ex,ey=P['encoder'];jx,jy=P['joystick'];tx,ty=P['touch']
plate=plate.cut(rounded(ex-6.2,ey-6.2,12.4,12.4,pz-.1,pt+.2,.5))
# Joystick travel aperture with annular removable bezel above the plate.
plate=plate.cut(rounded(jx-8.5,jy-9.8,18.6,22.1,pz-.1,pt+.2,.4))
# Touch cover is a replaceable 1mm dielectric disc, no exposed conductor.
plate=plate.cut(cylinder(tx,ty,pz-.1,7.6,pt+.2))
for x,y in P['mounts']:
 boss=cylinder(x,y,13.8,3.4,pz-13.8)
 plate=plate.fuse(boss).cut(cylinder(x,y,13.7,P['insert_hole']/2,P['insert_depth']+.1))
# Underside reinforcement webs stay in the gaps between switch bodies.
for x in [34,54,74]:plate=plate.fuse(box(x-1,49,14.1,2,60,3.1))
for y in [50.5,69,89,109]:plate=plate.fuse(box(12,y-1,14.1,84,2,3.1))
plate_obj=feat('03_Switch_plate',plate.removeSplitter(),(.64,.68,.66),'printable plate / 1.5 mm switch retention',True)
# A prototype PCB envelope follows shared coordinates; replace with KiCad STEP to inspect traces.
pcb=rounded(4,3.5,100,112.5,12,1.6,6)
for x,y in P['mounts']:pcb=pcb.cut(cylinder(x,y,11.9,1.35,1.8))
ax,ay,aw,ah=P['antenna_cutout'];pcb=pcb.cut(box(ax,ay,11.9,aw,ah,1.8))
# USB shell solder-bulge relief holes from the same Pico carrier footprint.
for x,y in [(43.5,12.775),(43.5,18.225),(46.53,13.075),(46.53,17.925)]:pcb=pcb.cut(cylinder(x,y,11.9,1.0,1.8))
# Mechanical MX central and alignment holes.
for x,y in P['keys']:
 for dx,dy,r in [(0,0,2.0),(-5.08,0,.85),(5.08,0,.85),(-3.81,-2.54,1.5),(2.54,-5.08,1.5)]:pcb=pcb.cut(cylinder(x+dx,y+dy,11.9,r,1.8))
pcb_obj=feat('02_Main_PCB_envelope',pcb,(.035,.19,.17),'mechanical envelope; final KiCad source authoritative')
# Switch assemblies and keycap envelope proxies, intentionally no brand geometry.
for i,(x,y) in enumerate(P['keys']):
 lower=box(x-6.95,y-6.95,13.6,13.9,13.9,5.1)
 flange=box(x-7.75,y-7.75,18.7,15.5,15.5,.8)
 top=rounded(x-5.7,y-5.7,11.4,11.4,19.5,5.0,1)
 stem=box(x-2,y-.65,24.5,4,1.3,1.4).fuse(box(x-.65,y-2,24.5,1.3,4,1.4))
 feat(f'Switch_{i+1:02}',union([lower,flange,top,stem]),(.07,.08,.075),'MX-compatible envelope')
 socket=rounded(x-7,y-6.9,14,6.4,9.0,3.0,1)
 feat(f'Hotswap_{i+1:02}',socket,(.11,.095,.08),'Kailh socket envelope; check footprint drawing')
 cap=rounded(x-9,y-9,18,18,24.6,7.4,1.6)
 # Scoop key top is a shallow spherical subtraction, keeping min top >=1.8mm.
 sphere=Part.makeSphere(50,V(x,y,81.0));cap=cap.cut(sphere)
 cap=cap.cut(rounded(x-6.4,y-6.4,12.8,12.8,24.5,4.6,1))
 feat(f'Keycap_{i+1:02}',cap,(.08,.105,.11) if i>1 else (.46,.73,.66),'standard 1U purchased keycap envelope')
# Encoder envelope with simple D shaft + printable original knob.
feat('Encoder_body',box(ex-5.85,ey-6,13.6,11.7,12,4.5),(.7,.7,.7),'ALPS EC11 envelope pending exact selected variant')
shaft=cylinder(ex,ey,18.1,3,20).cut(box(ex+1.5,ey-4,28.1,3,8,10.1));feat('Encoder_shaft',shaft,(.7,.7,.72))
knob=cylinder(ex,ey,21.5,10.3,18.5)
knob=knob.cut(cylinder(ex,ey,21.4,3.1,17.4)).fuse(box(ex+1.7,ey-2.6,28.1,1.4,5.2,10.7))
# Small index line recess; knurl is added in renderer only as texture detail.
knob=knob.cut(box(ex-.45,ey-9.3,39.6,.9,4,.6))
feat('Encoder_knob',knob.removeSplitter(),(.12,.17,.18),'printable D-shaft friction fit; coupon first',True)
joybody=rounded(jx-8.1,jy-9.4,17.8,21.3,13.6,11.2,.5)
feat('Joystick_body',joybody,(.12,.12,.12),'ALPS RKJXV1224005 bounding envelope')
feat('Joystick_stick',cylinder(jx,jy,24.8,2,7.75),(.7,.7,.7))
joycap=cylinder(jx,jy,30.2,8.5,3).fuse(Part.makeSphere(9,V(jx,jy,29.7))).common(cylinder(jx,jy,30.2,9,5))
joycap=joycap.cut(cylinder(jx,jy,30.1,2.1,2.6))
feat('Joystick_cap_TPU',joycap,(.085,.12,.115),'printable TPU; actual shaft fit must be measured',True)
bezel=rounded(jx-9.5,jy-10.8,20.6,24.1,pz+pt,.6,.5).cut(rounded(jx-8.5,jy-9.8,18.6,22.1,pz+pt-.1,.8,.4));feat('Joystick_bezel',bezel,(.44,.63,.57),'printable removable travel bezel',True)
touch=cylinder(tx,ty,pz,7.5,1.0);feat('Touch_cap_PETG',touch,(.45,.71,.64),'printable dielectric cap; optional touch PCB beneath',True)
# A 1 mm underside electrode envelope for capacitance experiment, not fitted by default.
feat('Touch_electrode_optional',cylinder(tx,ty,15.9,6.8,.2),(.7,.4,.13),'optional / unpopulated')
# Soldered Pico W underside: components project down, GPIO castellations toward carrier.
px,py,pw,pd=P['pico_outline'];pico=rounded(px,py,pw,pd,11.0,1.0,1.0);feat('Pico_W_board',pico,(.07,.33,.18),'soldered / no plug-in headers')
feat('Pico_RF_shield',box(px+21,py+3,8.5,14,15,2.5),(.7,.7,.7))
feat('Pico_USB_microB',box(px-1,py+6.5,7.9,5.7,8,3.1),(.72,.72,.75))
# Panel receptacle clearance model: manufacturing opening finalizes after cable measurement.
usb=rounded(ux-5.2,-.5,10.4,3.0,5.5,5.0,.4).fuse(rounded(ux-6,2.5,12,18,5.0,6,1)).fuse(box(ux-12,2.5,6,24,3,4))
usb=usb.cut(box(ux-3.8,-.6,uz-1.4,7.6,4.0,2.8))
feat('Rear_USB_microB_panel',usb,(.045,.045,.045),'Adafruit 3258; body envelope provisional')
# Cable path demonstrator at safe floor plane; verifies space reservation not bend rating.
pts=[V(ux,18,5.7),V(15,30,5.7),V(15,104,5.7),V(88,104,5.7),V(88,32,5.7),V(37,32,5.7),V(35,15.5,9.4),V(42,15.5,9.4)]
segments=[]
for a,b in zip(pts,pts[1:]):
 delta=b-a;segments.append(Part.makeCylinder(2.0,delta.Length,a,delta.normalize()))
feat('USB_cable_route_envelope',Part.Compound(segments),(.045,.045,.045),'4mm representative cable corridor; bend radii and actual length to verify')
# Reserved microphone board bay, no sensor/transducer included by default.
mic=box(70,109,3.0,15,9,6.0);feat('Microphone_bay_reserved',mic,(.2,.4,.7),'15x9x6mm reserved volume only; not populated')
for i,(x,y) in enumerate(P['foot_centers']):
 foot=cylinder(x,y,-1.7,5,2.3);feat(f'Foot_{i+1:02}_TPU',foot,(.06,.08,.075),'printable TPU foot',True)
for i,(x,y) in enumerate(P['mounts']):
 screw=cylinder(x,y,-.42,2.5,2.12).fuse(cylinder(x,y,1.7,1.2,16))
 feat(f'Screw_{i+1:02}_M2p5x16',screw,(.18,.18,.19),'M2.5x16 ISO7045/DIN7985 pan head, maxheight2.12mm envelope')
 ins=cylinder(x,y,14,P["insert_od"]/2,P["insert_length"]).cut(cylinder(x,y,13.9,1.1,P["insert_length"]+.2))
 feat(f'Insert_{i+1:02}',ins,(.58,.37,.12),'Trianglelab M2.5 D4.2 L3 heat-set insert / pilot fit to calibrate')
# Compact print coupon: three switch-fit openings and three shaft bores.
coupon=box(0,0,0,59,26,1.5)
for i,a in enumerate([13.9,14.1,14.3]):coupon=coupon.cut(box(3+i*19,3,-.1,a,a,1.7))
for i,r in enumerate([3.0,3.1,3.2]):coupon=coupon.cut(cylinder(10+i*19,22,-.1,r,1.7))
# Control aperture coupon for provisional drawing-derived joystick body offset.
control_coupon=rounded(0,0,66,34,0,1.5,3)
control_coupon=control_coupon.cut(rounded(9,10,12.4,12.4,-.1,1.7,.5))
control_coupon=control_coupon.cut(rounded(37,5.5,18.6,22.1,-.1,1.7,.4))
control_coupon.exportStl(str(OUT/'stl/Control_fit_coupon.stl'))
control_coupon.exportStep(str(OUT/'Control_fit_coupon.step'))
# Do not add coupon to assembled device; export separately.
coupon.exportStl(str(OUT/'stl/Fit_coupon.stl'));coupon.exportStep(str(OUT/'Fit_coupon.step'))
# Save all real solids in editable native format and neutral STEP.
doc.recompute();doc.saveAs(str(OUT/'FIELD13_assembly.FCStd'))
Part.export(parts,str(OUT/'FIELD13_assembly.step'))
manifest=[]
for o in parts:
 m=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.08,AngularDeflection=.15,Relative=False)
 path=OUT/'mesh'/f'{o.Name}.stl';m.write(str(path))
 if o in printable:
  # Printable export shifted onto z=0 for uncomplicated slicing.
  shape=o.Shape.copy();shape.translate(V(0,0,-shape.BoundBox.ZMin))
  pm=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.05,AngularDeflection=.1,Relative=False)
  pm.write(str(OUT/'stl'/f'{o.Name}.stl'))
 manifest.append({'name':o.Name,'label':o.Label,'mesh':str(path.relative_to(ROOT)),'role':o.Role,'color':list(o.MaterialColor),'volume_mm3':o.Shape.Volume,'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids),'bounds':[o.Shape.BoundBox.XMin,o.Shape.BoundBox.YMin,o.Shape.BoundBox.ZMin,o.Shape.BoundBox.XMax,o.Shape.BoundBox.YMax,o.Shape.BoundBox.ZMax]})
(OUT/'assembly_manifest.json').write_text(json.dumps(manifest,indent=2))
# Critical non-mating clearances. An overlap is a FAIL, not silently filtered.
checks=[]
for a,b in [(base_obj,pcb_obj),(base_obj,plate_obj),(plate_obj,pcb_obj)]:
 volume=a.Shape.common(b.Shape).Volume;checks.append({'a':a.Name,'b':b.Name,'overlap_mm3':volume,'pass':volume<1e-5})
for a in [base_obj,plate_obj]:
 for b in parts:
  if any(t in b.Name for t in ['Joystick_body','Encoder_body','Pico_W','Pico_RF','Rear_USB','Hotswap']):
   volume=a.Shape.common(b.Shape).Volume
   checks.append({'a':a.Name,'b':b.Name,'overlap_mm3':volume,'pass':volume<1e-5})
checks.extend([{'check':'13 keys','pass':len(P['keys'])==13},{'check':'MX plate thickness 1.5 mm','value':pt,'pass':abs(pt-1.5)<1e-8},{'check':'PCB top to plate top 5.1 mm','value':pz+pt-(P['pcb_z']+P['pcb_thickness']),'pass':abs(pz+pt-(P['pcb_z']+P['pcb_thickness'])-5.1)<1e-8}])
report={'revision':P['revision'],'all_solids_valid':all(x['valid'] for x in manifest),'parts':len(parts),'critical_clearance_checks':checks,'hardware_validation':'NOT RUN','fabrication_status':'PROTOTYPE / NOT FABRICATION RELEASED','unverified':['Actual keycap/switch/joystick/encoder fit; joystick body offset approximate from manufacturer drawing','Panel cable body envelope and flexible cable bend radius','Chosen printer/nozzle/material dimensional compensation','Heat-set insert installation fit in selected print material','Final PCB footprints and electrical DRC','RF performance, audio, wireless HID']}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
