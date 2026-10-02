#!/usr/bin/python3
"""Finish remaining two nets against actual KiCad copper; DRC is mandatory afterwards."""
import pcbnew as p, numpy as np, heapq,math,json,pathlib
R=pathlib.Path(__file__).parent;b=p.LoadBoard(str(R/'macropad-routed.kicad_pcb'));mm=p.FromMM;M=p.ToMM;V=lambda x,y:p.VECTOR2I(mm(x),mm(y))
G=.125;W=865;H=977
YY,XX=np.mgrid[0:H,0:W];XX=XX*G;YY=YY*G
nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
def circle(mask,x,y,r):
 x0=max(0,int((x-r)/G));x1=min(W,int((x+r)/G)+2);y0=max(0,int((y-r)/G));y1=min(H,int((y+r)/G)+2)
 mask[y0:y1,x0:x1]|=(XX[y0:y1,x0:x1]-x)**2+(YY[y0:y1,x0:x1]-y)**2<=r*r

def box(mask,x1,y1,x2,y2):mask[max(0,int(y1/G)):min(H,int(y2/G)+2),max(0,int(x1/G)):min(W,int(x2/G)+2)]=True

def seg(mask,a,c,r):
 x,y=a;u,v=c;x0=max(0,int((min(x,u)-r)/G));x1=min(W,int((max(x,u)+r)/G)+2);y0=max(0,int((min(y,v)-r)/G));y1=min(H,int((max(y,v)+r)/G)+2)
 xx=XX[y0:y1,x0:x1];yy=YY[y0:y1,x0:x1];dx=u-x;dy=v-y;d=dx*dx+dy*dy
 t=np.clip(((xx-x)*dx+(yy-y)*dy)/d,0,1) if d>0 else 0
 mask[y0:y1,x0:x1]|=(xx-x-t*dx)**2+(yy-y-t*dy)**2<=r*r

def masks(net,extra=.325):
 m=np.zeros((2,H,W),bool)
 for l in [0,1]:
  m[l]|=(XX<4.4)|(XX>103.6)|(YY<4.4)|(YY>115.6)
  for cx,cy,cond in [(10,10,(XX<10)&(YY<10)),(98,10,(XX>98)&(YY<10)),(10,110,(XX<10)&(YY>110)),(98,110,(XX>98)&(YY>110))]:m[l]|=cond&((XX-cx)**2+(YY-cy)**2>(5.6**2))
  box(m[l],81-extra,8.5-extra,96+extra,22.5+extra)
 box(m[1],42-extra,8.5-extra,81+extra,22.5+extra)
 box(m[0],80.5-extra,33.5-extra,87.5+extra,46.75+extra)
 for x in [80.5,87.5]:
  for y in [33.5,40.5]:box(m[0],x-1.3-extra,y-1.3-extra,x+1.3+extra,y+1.3+extra)
 for f in b.GetFootprints():
  for q in f.Pads():
   x,y=M(q.GetPosition().x),M(q.GetPosition().y)
   if q.GetAttribute()==p.PAD_ATTRIB_NPTH:
    for l in [0,1]:circle(m[l],x,y,M(q.GetDrillSize().x)/2+extra+.075)
   elif q.GetNetname()!=net:
    bb=q.GetBoundingBox();x1,y1=M(bb.GetX()),M(bb.GetY());x2,y2=x1+M(bb.GetWidth()),y1+M(bb.GetHeight())
    for l,kl in [(0,p.F_Cu),(1,p.B_Cu)]:
     if q.IsOnLayer(kl):box(m[l],x1-extra,y1-extra,x2+extra,y2+extra)
 for t in b.GetTracks():
  if t.GetNetname()==net:continue
  if isinstance(t,p.PCB_VIA):
   x,y=M(t.GetPosition().x),M(t.GetPosition().y)
   for l in [0,1]:circle(m[l],x,y,M(t.GetWidth(p.F_Cu))/2+extra)
  else:
   l=0 if t.GetLayer()==p.F_Cu else 1;seg(m[l],(M(t.GetStart().x),M(t.GetStart().y)),(M(t.GetEnd().x),M(t.GetEnd().y)),M(t.GetWidth())/2+extra)
 return m

def astar(net,a,c):
 m=masks(net);vm=masks(net,.525);start=(0,round(a[1]/G),round(a[0]/G));goals={(l,round(c[1]/G),round(c[0]/G))for l in [0,1]}
 # SMD destination is bottom only; start thru-hole may originate either side.
 goals={(1,round(c[1]/G),round(c[0]/G))}
 starts=[(l,start[1],start[2])for l in [0,1] if not m[l,start[1],start[2]]]
 def h(u):return (abs(u[1]-round(c[1]/G))+abs(u[2]-round(c[0]/G)))
 heap=[(h(u),0,u)for u in starts];dist={u:0 for u in starts};prev={};visits=0
 while heap:
  _,cost,u=heapq.heappop(heap)
  if cost!=dist[u]:continue
  if u in goals:
   path=[u]
   while u in prev:u=prev[u];path.append(u)
   return path[::-1]
  visits+=1
  if visits>2000000:break
  l,y,x=u
  for dl,dy,dx in [(0,0,1),(0,0,-1),(0,1,0),(0,-1,0),(1,0,0)]:
   ll=1-l if dl else l;yy=y+dy;xx=x+dx
   if not(0<=xx<W and 0<=yy<H)or m[ll,yy,xx]:continue
   if dl and(vm[0,y,x]or vm[1,y,x]):continue
   v=(ll,yy,xx);nc=cost+(18 if dl else 1)
   if nc<dist.get(v,1e12):dist[v]=nc;prev[v]=u;heapq.heappush(heap,(nc+h(v),nc,v))
 raise RuntimeError(f'Cannot route {net},visited {visits}')

def track(n,a,c):
 if a[1:]==c[1:]:return
 t=p.PCB_TRACK(b);t.SetStart(V(a[1],a[2]));t.SetEnd(V(c[1],c[2]));t.SetWidth(mm(.2));t.SetLayer(p.F_Cu if a[0]==0 else p.B_Cu);t.SetNet(nets[n]);b.Add(t)
def write(n,path,a,c):
 pts=[(l,x*G,y*G)for l,y,x in path];pts=[(pts[0][0],*a)]+pts+[(pts[-1][0],*c)]
 run=last=pts[0];direction=None
 for nxt in pts[1:]:
  if nxt==last:continue
  if nxt[0]!=last[0]:
   track(n,run,last);v=p.PCB_VIA(b);v.SetPosition(V(last[1],last[2]));v.SetWidth(p.F_Cu,mm(.6));v.SetDrill(mm(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(nets[n]);b.Add(v);run=nxt;direction=None
  else:
   dx=nxt[1]-last[1];dy=nxt[2]-last[2];di=(round(dx/(math.hypot(dx,dy)),3),round(dy/math.hypot(dx,dy),3))
   if direction is not None and di!=direction:track(n,run,last);run=last
   direction=di
  last=nxt
 track(n,run,last)
for n,a,c in [('3V3',(20,23),(53.53,25.19)),('ENC_SW',(31,39.5),(76.39,5.81))]:
 path=astar(n,a,c);write(n,path,a,c);print(n,len(path),'steps',flush=True)
# Pads are allowed within underside keepout solely for four NPTH USB relief holes.
for z in b.Zones():
 if z.GetLayerSet().Contains(p.B_Cu) and not z.GetLayerSet().Contains(p.F_Cu):z.SetDoNotAllowPads(False)
p.SaveBoard(str(R/'macropad-routed.kicad_pcb'),b)
