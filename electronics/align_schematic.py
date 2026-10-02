#!/usr/bin/python3
import pcbnew as p,json,pathlib,xml.etree.ElementTree as ET
R=pathlib.Path(__file__).parent;b=p.LoadBoard(str(R/'macropad.kicad_pcb'));m=json.load(open(R/'net_manifest.json'));cs={c['ref']:c for c in m['components']}
for n in list(b.GetNetsByNetcode().values()):
 if n.GetNetname() and not n.GetNetname().startswith('/') and not n.GetNetname().startswith('unconnected-'):n.SetNetname('/'+n.GetNetname())
ni={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
for e in ET.parse(R/'exports/macropad.xml').findall('./nets/net'):
 name=e.attrib['name']
 if not name.startswith('unconnected-'):continue
 name=name.replace('/','{slash}')
 if name not in ni:
  n=p.NETINFO_ITEM(b,name,len(ni)+1);b.Add(n);ni[name]=n
 for node in e.findall('node'):
  for f in b.GetFootprints():
   if f.GetReference()==node.attrib['ref']:
    for pad in f.Pads():
     if pad.GetNumber()==node.attrib['pin']:pad.SetNet(ni[name])
for f in b.GetFootprints():
 c=cs.get(f.GetReference())
 if c:
  lib,name=c['footprint'].split(':');f.SetFPID(p.LIB_ID(lib,name));f.SetDNP(c.get('optional',False))
 else:f.SetBoardOnly(True);f.SetExcludedFromBOM(True);f.SetExcludedFromPosFiles(True)
p.SaveBoard(str(R/'macropad.kicad_pcb'),b)
