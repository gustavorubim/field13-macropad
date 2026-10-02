#!/usr/bin/python3
import pcbnew as p,pathlib,json
R=pathlib.Path(__file__).parent;b=p.LoadBoard(str(R/'macropad.kicad_pcb'));mm=p.FromMM;M=p.ToMM;V=lambda x,y:p.VECTOR2I(mm(x),mm(y))
for s in b.GetDrawings():
 if not isinstance(s,p.PCB_SHAPE)or s.GetLayer()!=p.Edge_Cuts:continue
 if s.GetShape()==p.SHAPE_T_ARC:
  mid=s.GetArcMid()
  if M(mid.y)<10 and (abs(M(s.GetStart().y)-4)<.001 or abs(M(s.GetEnd().y)-4)<.001):
   a=s.GetStart();c=s.GetEnd();s.SetArcGeometry(V(M(a.x),M(a.y)-.5),V(M(mid.x),M(mid.y)-.5),V(M(c.x),M(c.y)-.5))
 else:
  a=s.GetStart();c=s.GetEnd()
  if abs(M(a.y)-4)<.001 and abs(M(c.y)-4)<.001:s.SetStart(V(M(a.x),3.5));s.SetEnd(V(M(c.x),3.5))
  elif abs(M(a.x)-104)<.001 and abs(M(a.y)-10)<.001:s.SetStart(V(104,9.5))
  elif abs(M(c.x)-4)<.001 and abs(M(c.y)-10)<.001:s.SetEnd(V(4,9.5))
# Move two antenna-edge vias and every coincident track endpoint together.
for via in list(b.GetTracks()):
 if not isinstance(via,p.PCB_VIA):continue
 pos=via.GetPosition()
 if abs(M(pos.y)-7.7367)<.001 and any(abs(M(pos.x)-x)<.001 for x in [85.2551,87.8045]):
  new=V(M(pos.x),7.68)
  for t in b.GetTracks():
   if isinstance(t,p.PCB_VIA):continue
   if (t.GetStart()-pos).EuclideanNorm()<1000:t.SetStart(new)
   if (t.GetEnd()-pos).EuclideanNorm()<1000:t.SetEnd(new)
  via.SetPosition(new)
for f in b.GetFootprints():
 if f.GetReference()=='C2':f.SetValue('100uF / 16V')
b.GetDesignSettings().m_CopperEdgeClearance=mm(.5);p.SaveBoard(str(R/'macropad.kicad_pcb'),b)
pro=R/'macropad.kicad_pro';j=json.load(open(pro));j['board']['design_settings']['rules']['min_copper_edge_clearance']=.5;pro.write_text(json.dumps(j,indent=2)+'\n')
