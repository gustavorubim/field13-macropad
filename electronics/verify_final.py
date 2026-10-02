#!/usr/bin/python3
import pcbnew as p,json,pathlib,hashlib,datetime
R=pathlib.Path(__file__).parent;m=json.load(open(R/'net_manifest.json'));b=p.LoadBoard(str(R/'macropad.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};errors=[];count=0
for c in m['components']:
 f=fps[c['ref']]
 for number,net in c['pins'].items():
  pads=[q for q in f.Pads()if q.GetNumber()==number]
  if not pads:errors.append({'ref':c['ref'],'pin':number,'error':'missing PCB pad'});continue
  for pad in pads:
   actual=pad.GetNetname()
   ok=actual.lstrip('/')==net if net is not None else actual.startswith('unconnected-') or not actual
   if not ok:errors.append({'ref':c['ref'],'pin':number,'expected':net,'actual':actual})
  count+=1
summary={'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_pin_mappings_checked':count,'mismatches':errors,'component_count':len(m['components']),'pcb_footprints':len(fps),'copper_layers':2,'track_segments':sum(not isinstance(t,p.PCB_VIA)for t in b.GetTracks()),'plated_vias':sum(isinstance(t,p.PCB_VIA)for t in b.GetTracks()),'board_mm':{'x_min':4,'x_max':104,'y_min':3.5,'y_max':116,'corner_radius':6},'rules_mm':{'minimum_track_width':.2,'minimum_clearance':.2,'minimum_copper_edge':.5,'via_diameter':.6,'via_drill':.3},'release_status':'Engineering prototype; physical fit, custom footprint, RF and power gates open'}
(R/'reports/pcb_connectivity_check.json').write_text(json.dumps(summary,indent=2)+'\n')
files=['macropad.kicad_pcb','macropad.kicad_sch','macropad.kicad_pro','net_manifest.json','reports/DRC.rpt','reports/DRC.json','reports/ERC.rpt','reports/ERC.json']
hashes={f:hashlib.sha256((R/f).read_bytes()).hexdigest()for f in files}
(R/'reports/final_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n');print(json.dumps(summary,indent=2))
