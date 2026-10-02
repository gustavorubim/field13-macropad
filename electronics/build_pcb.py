#!/usr/bin/python3
"""Generate editable two-layer prototype PCB from exact electrical manifest.
Coordinates share the enclosure datum; rear is y=0. Run with KiCad9 pcbnew.
"""
import pcbnew as p,json,math,pathlib,os
ROOT=pathlib.Path(__file__).parent
LIB=ROOT/'libraries/Macropad.pretty'; LIB.mkdir(parents=True,exist_ok=True)
io=p.PCB_IO_KICAD_SEXPR()
b=p.BOARD(); b.SetCopperLayerCount(2)
def LS(layers):
 s=p.LSET()
 for i in layers:s.AddLayer(i)
 return s
mm=p.FromMM; V=lambda x,y:p.VECTOR2I(mm(x),mm(y))
def shape(parent,typ,layer,width=.15):
 s=p.PCB_SHAPE(parent);s.SetShape(typ);s.SetLayer(layer);s.SetWidth(mm(width));parent.Add(s);return s
def line(parent,x1,y1,x2,y2,layer=p.F_SilkS,width=.15):
 s=shape(parent,p.SHAPE_T_SEGMENT,layer,width);s.SetStart(V(x1,y1));s.SetEnd(V(x2,y2));return s
def rect(parent,x1,y1,x2,y2,layer=p.F_Fab,width=.1):
 for a,c in [((x1,y1),(x2,y1)),((x2,y1),(x2,y2)),((x2,y2),(x1,y2)),((x1,y2),(x1,y1))]:line(parent,*a,*c,layer,width)
def pad(fp,num,x,y,sx,sy,drill=0,smd=False,oval=False):
 q=p.PAD(fp);q.SetNumber(str(num));q.SetPosition(V(x,y));q.SetSize(V(sx,sy));q.SetShape(p.PAD_SHAPE_OVAL if oval else (p.PAD_SHAPE_RECT if smd else p.PAD_SHAPE_CIRCLE))
 if smd:q.SetAttribute(p.PAD_ATTRIB_SMD);q.SetLayerSet(LS([p.F_Cu,p.F_Mask,p.F_Paste]))
 else:q.SetAttribute(p.PAD_ATTRIB_PTH if num else p.PAD_ATTRIB_NPTH);q.SetDrillSize(V(drill,drill));q.SetLayerSet(LS([p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask]))
 fp.Add(q);return q
def fp_new(name):
 f=p.FOOTPRINT(b);f.SetFPID(p.LIB_ID('Macropad',name));f.SetValue(name);f.Reference().SetVisible(True);f.Value().SetVisible(False);return f
def keepout(x1,y1,x2,y2,layers=[p.F_Cu,p.B_Cu],tracks=True,pads=True):
 z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayerSet(LS(layers));z.SetDoNotAllowTracks(tracks);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(pads);z.SetDoNotAllowCopperPour(True)
 poly=z.Outline();poly.NewOutline()
 for x,y in [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]:poly.Append(mm(x),mm(y))
 b.Add(z);return z
# MX switch reference is switch stem center. Socket is physically underside.
f=fp_new('MX_Hotswap_CPG151101S11_16')
# Template mirrored in Y on placement to retain standard Cherry switch top-side geometry.
for x,y,d in [(0,0,4),(-5.08,0,1.7),(5.08,0,1.7),(-3.81,2.54,3),(2.54,5.08,3)]:pad(f,'',x,y,d,d,d)
pad(f,'1',-7.385,2.54,2.55,2.5,smd=True);pad(f,'2',6.115,5.08,2.55,2.5,smd=True)
rect(f,-7,-7,7,7,p.F_Fab);rect(f,-8.8,1,7.8,6.9,p.F_CrtYd)
# Fab socket body; cap outline on front fabrication layer mirrored by placement.
rect(f,-5.81,1.0,4.54,6.6,p.F_SilkS)
io.FootprintSave(str(LIB),f)
# Pico castellated pads; no testpoint copper underneath module. USB left; antenna right.
f=fp_new('PicoW_Castellated')
for i in range(20):
 x=-24.13+2.54*i
 pad(f,str(i+1),x,9.69,1.6,3.2,smd=True)
 pad(f,str(40-i),x,-9.69,1.6,3.2,smd=True)
# USB shell solder-bulge relief, rev3 drawing positions; prevents rocking during hand soldering.
for x,y in [(-24,2.725),(-24,-2.725),(-20.97,2.425),(-20.97,-2.425)]:pad(f,'',x,y,2,2,2)
rect(f,-25.5,-10.5,25.5,10.5,p.F_Fab);rect(f,-25.75,-11.6,25.75,11.6,p.F_CrtYd)
rect(f,-25.5,-4,-20.5,4,p.F_SilkS)
line(f,16.5,-7,25.5,-7,p.F_Fab);line(f,16.5,7,25.5,7,p.F_Fab);line(f,16.5,-7,16.5,7,p.F_Fab)
io.FootprintSave(str(LIB),f)
# ALPS RKJXV1224005 viewed from mounting side. Pin-labelled drawing in sources.
f=fp_new('Joystick_RKJXV1224005')
for n,x,y in [('Y3',-2.5,-8.73),('Y2',0,-8.73),('Y1',2.5,-8.73),('X3',8.73,-2.5),('X2',8.73,0),('X1',8.73,2.5),('S1',-4.3,0),('S2',4.3,0)]:
 d=1.5 if n.startswith('S') else 1.0;pad(f,n,x,y,d+.7,d+.7,d)
for x in [-6.325,6.325]:
 for y in [-5,5]:pad(f,'MP',x,y,2.3,2.3,1.6)
rect(f,-8.1,-9.4,9.7,11.9,p.F_Fab);rect(f,-9.4,-10.5,10.2,11.8,p.F_CrtYd);rect(f,-6.575,-6.575,6.575,6.575,p.F_SilkS)
io.FootprintSave(str(LIB),f)
# Outer board 100x112mm R6 plus physical antenna cutout 9x14mm.
for a,c in [((10,3.5),(98,3.5)),((104,9.5),(104,110)),((98,116),(10,116)),((4,110),(4,9.5))]:line(b,*a,*c,p.Edge_Cuts,.05)
for st,mid,en in [((98,3.5),(102.2426407,5.2573593),(104,9.5)),((104,110),(102.2426407,114.2426407),(98,116)),((10,116),(5.7573593,114.2426407),(4,110)),((4,9.5),(5.7573593,5.2573593),(10,3.5))]:
 s=shape(b,p.SHAPE_T_ARC,p.Edge_Cuts,.05);s.SetArcGeometry(V(*st),V(*mid),V(*en))
rect(b,84,8.5,93,22.5,p.Edge_Cuts,.05)
# 3mm extra RF margin around antenna keepout, excludes needed castellated rails.
# No-metal enclosure volume is separately documented; copper restricted cutout + end region.
keepout(81,8.5,96,22.5)
# Inner underside area under Pico testpoints: keep copper away from unknown exposed test pads.
keepout(42,8.5,81,22.5,[p.B_Cu],pads=False)
# Joystick prohibited wiring regions: conservative whole central underside contact area on F.Cu.
keepout(80.5,33.5,87.5,46.75,[p.F_Cu],pads=False)
for x in [80.5,87.5]:
 for y in [33.5,40.5]:keepout(x-1.3,y-1.3,x+1.3,y+1.3,[p.F_Cu],pads=False)
manifest=json.load(open(ROOT/'net_manifest.json'));nets={}
for i,n in enumerate(manifest['nets'],1):
 ni=p.NETINFO_ITEM(b,n,i);b.Add(ni);nets[n]=ni
components={c['ref']:c for c in manifest['components']}
keys=[(44,37),(64,37)]+[(x,59)for x in [24,44,64,84]]+[(x,79)for x in [24,44,64,84]]+[(x,99)for x in [24,44,64]]
pos={'U1':(67.5,15.5,0),'ENC1':(16.5,34.5,0),'JOY1':(84,37,0),'J1':(91,94,90),'J2':(19,15,90),'J3':(20,23,90),'U2':(31,15,0),'C1':(31,11.5,0),'C2':(16,9,0),'R3':(27,18.5,0),'R4':(32.5,18.5,0),'R1':(83,89,0),'R2':(83,91,0)}
for i,(x,y)in enumerate(keys,1):pos[f'SW{i}']=(x,y,0);pos[f'D{i}']=(x+6,y+8,0)
for ref,c in components.items():
 lib,name=c['footprint'].split(':');path=LIB if lib=='Macropad' else pathlib.Path('/usr/share/kicad/footprints')/(lib+'.pretty')
 f=p.FootprintLoad(str(path),name)
 if f is None:raise ValueError(c['footprint'])
 b.Add(f);f.SetReference(ref);f.SetValue(c['value']);f.Value().SetVisible(False)
 x,y,ang=pos[ref]
 if c.get('side')=='B':f.Flip(V(0,0),p.FLIP_DIRECTION_TOP_BOTTOM)
 f.SetOrientationDegrees(ang);f.SetPosition(V(x,y));
 if 'uuid' in c:
  path=p.KIID_PATH();path.push_back(p.KIID(manifest['schematic_uuid']));path.push_back(p.KIID(c['uuid']));f.SetPath(path)
 f.Reference().SetLayer(p.B_Fab if c.get('side')=='B' else p.F_Fab);f.Reference().SetTextSize(V(.85,.85));f.Reference().SetTextThickness(mm(.13));f.Reference().SetPosition(V(x,y+9 if ref.startswith('SW') else y-2.5))
 for drawing in f.GraphicalItems():
  if drawing.GetLayer()==p.F_SilkS:drawing.SetLayer(p.F_Fab)
  if drawing.GetLayer()==p.B_SilkS:drawing.SetLayer(p.B_Fab)
 for q in f.Pads():
  n=c['pins'].get(q.GetNumber())
  if ref=='JOY1' and q.GetNumber()=='MP':n='GND'
  if n:q.SetNet(nets[n])
# Mounting holes are no-plated, radius1.35. No copper in radius3mm.
for i,(x,y)in enumerate([(9,9),(99,9),(9,63),(99,63),(9,111),(99,111)],1):
 f=p.FootprintLoad('/usr/share/kicad/footprints/MountingHole.pretty','MountingHole_2.7mm_M2.5');f.SetReference('H'+str(i));f.SetPosition(V(x,y));f.Value().SetVisible(False);b.Add(f)
# Helpful top and bottom legend, away from routing pads.
for txt,x,y,layer in [('MICRO 13  /  REV A PROTOTYPE',53,111,p.F_SilkS),('USB ONLY   3V3 GPIO',28,48,p.B_SilkS),('RF CUTOUT',88.5,25,p.F_SilkS)]:
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(V(x,y));t.SetTextSize(V(1,1));t.SetTextThickness(mm(.15));t.SetLayer(layer)
 if layer==p.B_SilkS:t.SetMirrored(True)
 b.Add(t)
# Pre-route two constrained SMD escapes before global routing.
def tr(n,x1,y1,x2,y2,layer=p.B_Cu,w=.25):
 t=p.PCB_TRACK(b);t.SetStart(V(x1,y1));t.SetEnd(V(x2,y2));t.SetWidth(mm(w));t.SetLayer(layer);t.SetNet(nets[n]);b.Add(t)
def via(n,x,y):
 v=p.PCB_VIA(b);v.SetPosition(V(x,y));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(nets[n]);b.Add(v)
tr('ROW0',43.37,5.81,41,5.81);tr('ROW0',41,5.81,40.2,6.61);via('ROW0',40.2,6.61)
tr('RGB_5V',32.1375,14.05,34.5,14.05);via('RGB_5V',34.5,14.05)
# Standard budget fabrication geometry. DRC remains required after router import.
ds=b.GetDesignSettings();ds.m_MinClearance=mm(.2);ds.m_TrackMinWidth=mm(.2);ds.m_ViasMinSize=mm(.6);ds.m_MinThroughDrill=mm(.3);ds.m_CopperEdgeClearance=mm(.5)
defnc=ds.m_NetSettings.GetDefaultNetclass();defnc.SetClearance(mm(.2));defnc.SetTrackWidth(mm(.25));defnc.SetViaDiameter(mm(.6));defnc.SetViaDrill(mm(.3))
b.SetFileName(str(ROOT/'macropad.kicad_pcb'));p.SaveBoard(str(ROOT/'macropad.kicad_pcb'),b)
p.ExportSpecctraDSN(b,str(ROOT/'macropad.dsn'))
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Macropad")(type "KiCad")(uri "${KIPRJMOD}/libraries/Macropad.pretty")(options "")(descr "Project-local reviewed prototype footprints")))\n')
print('Wrote',len(list(b.GetFootprints())),'footprints;',len(nets),'nets')
