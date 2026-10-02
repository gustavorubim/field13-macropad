#!/usr/bin/python3
"""Snapshot the final PCB footprint geometry into project-local libraries."""
import pcbnew as p,pathlib
R=pathlib.Path(__file__).parent;b=p.LoadBoard(str(R/'macropad.kicad_pcb'));io=p.PCB_IO_KICAD_SEXPR();seen=set();libs=set();hold=[];saved_project=(R/'macropad.kicad_pro').read_text()
for original in b.GetFootprints():
 id=original.GetFPID();lib=str(id.GetLibNickname());name=str(id.GetLibItemName())
 if not lib:lib='MountingHole';original.SetFPID(p.LIB_ID(lib,name))
 libs.add(lib)
 if (lib,name)in seen:continue
 seen.add((lib,name));dest=R/'libraries'/(lib+'.pretty');dest.mkdir(exist_ok=True)
 f=p.FOOTPRINT(original);tmp=p.BOARD();tmp.Add(f);hold.append((tmp,f));f.SetPosition(p.VECTOR2I(0,0));f.SetOrientationDegrees(0)
 if f.GetLayer()==p.B_Cu:f.Flip(p.VECTOR2I(0,0),p.FLIP_DIRECTION_TOP_BOTTOM)
 for pad in f.Pads():pad.SetNetCode(0)
 io.FootprintSave(str(dest),f)
(R/'fp-lib-table').write_text('(fp_lib_table (version 7)\n'+''.join(f' (lib (name "{lib}")(type "KiCad")(uri "${{KIPRJMOD}}/libraries/{lib}.pretty")(options "")(descr "Project-local snapshot of final prototype geometry"))\n'for lib in sorted(libs))+')\n')
p.SaveBoard(str(R/'macropad.kicad_pcb'),b)
(R/'macropad.kicad_pro').write_text(saved_project)
print('Saved',len(seen),'footprint definitions across',len(libs),'libraries')
