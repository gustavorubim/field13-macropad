from pathlib import Path
import json, uuid, csv
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'electronics'; L=E/'libraries/symbols'; D=ROOT/'docs'
for p in (E,L,D):p.mkdir(parents=True,exist_ok=True)
U=lambda:str(uuid.uuid4())
components=[]
def comp(ref,value,footprint,pins,**kw):
 c=dict(ref=ref,uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'macropad:component:'+ref)),value=value,footprint=footprint,pins={str(k):v for k,v in pins.items()},**kw); components.append(c);return c
pico_pins={1:'ROW0',2:'ROW1',3:'GND',4:'ROW2',5:'ROW3',6:'COL0',7:'COL1',8:'GND',9:'COL2',10:'COL3',11:'ENC_A',12:'ENC_B',13:'GND',14:'ENC_SW',15:'JOY_SW',16:'TOUCH_SDA',17:'TOUCH_SCL',18:'GND',19:None,20:'RGB_DATA',21:'MIC_BCLK',22:'MIC_WS',23:'GND',24:'MIC_DATA',25:None,26:None,27:None,28:'GND',29:None,30:None,31:'JOY_X',32:'JOY_Y',33:'GND',34:None,35:None,36:'3V3',37:None,38:'GND',39:None,40:'5V_USB'}
comp('U1','Raspberry Pi Pico W','Macropad:PicoW_Castellated',pico_pins,manufacturer='Raspberry Pi',mpn='SC0918',source='https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf',side='B',description='USB-powered Pico W; castellated carrier mount; USB connector faces left edge; antenna faces right')
for i,(r,c) in enumerate([(0,1),(0,2)]+[(1,c)for c in range(4)]+[(2,c)for c in range(4)]+[(3,c)for c in range(3)],1):
 comp('SW'+str(i),'MX hot-swap','Macropad:MX_Hotswap_CPG151101S11_16',{'1':f'COL{c}','2':f'KEY{i}_A'},manufacturer='Kailh',mpn='CPG151101S11-16',source='https://www.kailhswitch.com/Content/upload/pdf/202215927/CPG151101S11-16.pdf',row=r,col=c,side='B',description='Socket on B.Cu; MX switch inserted from F.Cu; socket and switch are distinct BOM items')
 comp('D'+str(i),'1N4148W','Diode_SMD:D_SOD-123',{'1':f'ROW{r}','2':f'KEY{i}_A'},manufacturer='Diodes Incorporated',mpn='1N4148W-7-F',source='https://www.diodes.com/assets/Datasheets/ds12019.pdf',side='B',description='Pin 1 cathode toward row; pin 2 anode toward switch')
comp('ENC1','EC11E15244B2','Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm',{'A':'ENC_A','B':'ENC_B','C':'GND','S1':'ENC_SW','S2':'GND','MP':'GND'},manufacturer='Alps Alpine',mpn='EC11E15244B2',source='https://tech.alpsalpine.com/e/products/detail/EC11E15244B2/',side='F',description='30 detents / 15 pulses, 20 mm flat shaft, push switch')
comp('JOY1','RKJXV1224005','Macropad:Joystick_RKJXV1224005',{'X1':'3V3','X2':'JOY_X','X3':'GND','Y1':'3V3','Y2':'JOY_Y','Y3':'GND','S1':'JOY_SW','S2':'GND','MP':'GND'},manufacturer='Alps Alpine',mpn='RKJXV1224005',source='https://tech.alpsalpine.com/e/products/detail/RKJXV1224005/',side='F',description='Bare 2-axis 10k potentiometer joystick with click; custom logical pad names X/Y1..3 map to manufacturer potentiometer terminals 1..3; NRND')
for ref,n,pins,value in [('J1',4,{1:'3V3',2:'GND',3:'TOUCH_SDA',4:'TOUCH_SCL'},'TOUCH_I2C'),('J2',3,{1:'5V_USB',2:'RGB_DOUT',3:'GND'},'RGB_STRIP'),('J3',6,{1:'3V3',2:'GND',3:'MIC_BCLK',4:'MIC_WS',5:'MIC_DATA',6:'GND'},'MIC_I2S')]:
 comp(ref,value,f'Connector_PinHeader_2.54mm:PinHeader_1x0{n}_P2.54mm_Vertical',pins,manufacturer='Samtec',mpn=f'TSW-10{n}-07-G-S',source=f'https://www.samtec.com/products/tsw',side='F',optional=True,description='Optional 2.54 mm header; external peripherals not on PCB')
for ref,val,net1,net2,mpn in [('R1','4.7k','3V3','TOUCH_SDA','RC0603FR-074K7L'),('R2','4.7k','3V3','TOUCH_SCL','RC0603FR-074K7L'),('R3','330','RGB_5V','RGB_DOUT','RC0603FR-07330RL')]:
 comp(ref,val,'Resistor_SMD:R_0603_1608Metric',{'1':net1,'2':net2},manufacturer='Yageo',mpn=mpn,source='https://www.yageo.com/en/PartSearch',side='B',optional=ref!='R3',description='I2C pull-up: DNP if peripheral already fitted with pull-ups' if ref!='R3' else 'RGB data series damping resistor')
comp('U2','SN74AHCT1G125DBVR','Package_TO_SOT_SMD:SOT-23-5',{'1':'GND','2':'RGB_DATA','3':'GND','4':'RGB_5V','5':'5V_USB'},manufacturer='Texas Instruments',mpn='SN74AHCT1G125DBVR',source='https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf',side='B',description='5V TTL-input buffer; 3.3V input accepted; /OE grounded')
comp('C1','100nF','Capacitor_SMD:C_0603_1608Metric',{'1':'5V_USB','2':'GND'},manufacturer='Murata',mpn='GRM188R72A104KA35D',source='https://www.murata.com/en-us/products/productdetail?partno=GRM188R71C104KA01%23',side='B',description='100V X7R bypass adjacent to U2')
comp('C2','100uF / 16V','Capacitor_SMD:CP_Elec_6.3x5.8',{'1':'5V_USB','2':'GND'},manufacturer='Panasonic',mpn='EEE-FK1C101P',source='https://industrial.panasonic.com/ww/products/pt/aluminum-cap-smd/models/EEEFK1C101P',side='B',optional=True,description='Optional polarized bulk capacitor near RGB header; validate USB inrush before populating')
comp('R4','10k','Resistor_SMD:R_0603_1608Metric',{'1':'RGB_DATA','2':'GND'},manufacturer='Yageo',mpn='RC0603FR-0710KL',source='https://www.yageo.com/en/PartSearch',side='B',description='Pull-down holds AHCT input low during reset or high-impedance Pico GPIO state')
manifest=dict(schematic_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'macropad:schematic')),schema_version=1,project='macropad',kicad_version='9',components=components,nets=sorted({n for c in components for n in c['pins'].values()if n}),notes=['Null pin nets mean explicit no-connect.','Pin names X1/X2/X3 and Y1/Y2/Y3 are custom JOY1 footprint names for each potentiometer terminal 1/2/3.','Matrix direction COL -> SW pin1 -> SW pin2 -> diode pin2/anode -> diode pin1/cathode -> ROW; firmware drive rows low and read columns pull-up.','Pico W mounted on bottom carrier; no battery or charger; USB is sole intended power source.','Optional external modules are connectors only; stock and availability not checked.','74AHCT level shifter 5V output must never reach Pico GPIO.'])

if not (E/'net_manifest.json').exists(): (E/'net_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Native editable KiCad symbols and schematic: physical pin numbers retained.
# Load current selected components before symbol authoring.
manifest=json.loads((E/'net_manifest.json').read_text());components=manifest['components']
root_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'macropad:schematic')); symbols={}; geom={}
def q(s):return json.dumps(str(s))
def ef(size=1.0,extra=''):return f'(effects (font (size {size} {size})) {extra})'
def line(points,width=.254):return '(polyline (pts '+' '.join(f'(xy {x} {y})'for x,y in points)+f') (stroke (width {width}) (type default)) (fill (type none)))'
def rect(x1,y1,x2,y2,fill='background'):return f'(rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.254) (type default)) (fill (type {fill})))'
def circle(x,y,r):return f'(circle (center {x} {y}) (radius {r}) (stroke (width .254) (type default)) (fill (type none)))'
def txt(s,x,y,size=1):return f'(text {q(s)} (at {x} {y} 0) {ef(size)})'
def sym(name,pins,graphics,show_names=True,power=False):
 # pins: number,name,x,y,angle,type,length
 pp=[]
 for num,nm,x,y,a,ty,ln in pins:
  pp.append(f'(pin {ty} line (at {x} {y} {a}) (length {ln}) (name {q(nm)} {ef(.9)}) (number {q(num)} {ef(.9)}))')
 body=f'''(symbol {q(name)} {'(power)' if power else ''} (pin_names (offset 0.8) {'(hide yes)'if not show_names else ''}) (exclude_from_sim no) (in_bom {'no'if power else 'yes'}) (on_board {'no'if power else 'yes'})
 (property "Reference" "{'#FLG'if power else 'U'}" (at 0 5.08 0) {ef(1.27)})
 (property "Value" {q(name)} (at 0 -5.08 0) {ef(1.27)})
 (property "Footprint" "" (at 0 0 0) {ef(1,'(hide yes)')})
 (symbol {q(name+'_0_1')} {' '.join(graphics)})
 (symbol {q(name+'_1_1')} {' '.join(pp)}))'''
 symbols[name]=body;geom[name]=pins
# Pico module: exact physical 1..40 pinout.
names={1:'GP0',2:'GP1',3:'GND',4:'GP2',5:'GP3',6:'GP4',7:'GP5',8:'GND',9:'GP6',10:'GP7',11:'GP8',12:'GP9',13:'GND',14:'GP10',15:'GP11',16:'GP12',17:'GP13',18:'GND',19:'GP14',20:'GP15',21:'GP16',22:'GP17',23:'GND',24:'GP18',25:'GP19',26:'GP20',27:'GP21',28:'GND',29:'GP22',30:'RUN',31:'GP26/ADC0',32:'GP27/ADC1',33:'AGND',34:'GP28/ADC2',35:'ADC_VREF',36:'3V3_OUT',37:'3V3_EN',38:'GND',39:'VSYS',40:'VBUS'}
pins=[]
for n in range(1,41):
 left=n<=20; idx=n-1 if left else 40-n
 ty='power_out'if n in (36,40)else 'power_in'if n in (3,8,13,18,23,28,33,38,39)else 'input'if n in (30,37)else'passive'if n==35 else 'bidirectional'
 pins.append((str(n),names[n],-22.86 if left else 22.86,36.83-idx*3.81,0 if left else 180,ty,5.08))
sym('PicoW',pins,[rect(-17.78,40.005,17.78,-40.005),txt('USB',0,36.195,1.27),rect(-5.08,33.655,5.08,40.005),txt('PICO W',0,0,1.5),txt('BOTTOM',0,-3.81,1),txt('carrier mount',0,-6.35,1)])
sym('MX_Switch',[('1','1',-5.08,0,0,'passive',2.54),('2','2',5.08,0,180,'passive',2.54)],[circle(-2.54,0,.5),circle(2.54,0,.5),line([(-2.54,.5),(2.0,2.5)])],False)
sym('Diode',[('2','A',-5.08,0,0,'passive',3.81),('1','K',5.08,0,180,'passive',3.81)],[line([(-1.27,-1.27),(-1.27,1.27),(1.27,0),(-1.27,-1.27)]),line([(1.27,-1.27),(1.27,1.27)])],False)
sym('Resistor',[('1','1',-5.08,0,0,'passive',2.54),('2','2',5.08,0,180,'passive',2.54)],[rect(-2.54,1.016,2.54,-1.016,'none')],False)
sym('Capacitor',[('1','1',-5.08,0,0,'passive',4.572),('2','2',5.08,0,180,'passive',4.572)],[line([(-.508,-1.778),(-.508,1.778)]),line([(.508,-1.778),(.508,1.778)])],False)
sym('Capacitor_Polar',[('1','+',-5.08,0,0,'passive',4.572),('2','-',5.08,0,180,'passive',4.572)],[line([(-.508,-1.778),(-.508,1.778)]),rect(.508,1.778,1.016,-1.778,'none'),txt('+',-2.54,2.54)],False)
sym('AHCT125',[('2','A',-12.7,2.54,0,'input',5.08),('1','~{OE}',-12.7,-2.54,0,'input',5.08),('4','Y',12.7,2.54,180,'tri_state',5.08),('5','VCC',0,12.7,270,'power_in',5.08),('3','GND',0,-12.7,90,'power_in',5.08)],[rect(-7.62,7.62,7.62,-7.62),line([(-2.54,5.08),(-2.54,0),(2.54,2.54),(-2.54,5.08)])])
# Mechanical controls retain one footprint each; shaft, pots, and contact functions are shown.
sym('Encoder',[('A','A',-15.24,7.62,0,'passive',5.08),('C','COM',-15.24,0,0,'passive',5.08),('B','B',-15.24,-7.62,0,'passive',5.08),('S1','SW',15.24,7.62,180,'passive',5.08),('S2','SW',15.24,0,180,'passive',5.08),('MP','FRAME',15.24,-7.62,180,'passive',5.08)],[rect(-10.16,12.7,10.16,-12.7),circle(-1.27,3.81,3.81),line([(-3.81,1.27),(1.27,6.35)]),txt('15 PPR',0,-5.08),txt('30 detents',0,-8.89)])
sym('Joystick',[('X1','X:1',-20.32,12.7,0,'passive',5.08),('X2','X:2',-20.32,7.62,0,'passive',5.08),('X3','X:3',-20.32,2.54,0,'passive',5.08),('Y1','Y:1',20.32,12.7,180,'passive',5.08),('Y2','Y:2',20.32,7.62,180,'passive',5.08),('Y3','Y:3',20.32,2.54,180,'passive',5.08),('S1','SW',-20.32,-10.16,0,'passive',5.08),('S2','SW',20.32,-10.16,180,'passive',5.08),('MP','FRAME',0,-20.32,90,'passive',5.08)],[rect(-15.24,17.78,15.24,-15.24),txt('2-axis / 10k',0,-3.81),rect(-2.54,12.7,-1.27,2.54,'none'),line([(-6.35,7.62),(-2.54,7.62)]),rect(1.27,12.7,2.54,2.54,'none'),line([(6.35,7.62),(2.54,7.62)]),line([(-6.35,-10.16),(-2.54,-10.16),(2.54,-7.62)]),line([(2.54,-10.16),(6.35,-10.16)])])
for n in [3,4,6]:
 sym('Header'+str(n),[(str(i),str(i),-7.62,(n-1)*1.27-(i-1)*2.54,0,'passive',5.08) for i in range(1,n+1)],[rect(-2.54,n*1.27,2.54,-n*1.27)]+[rect(-2.54,(n-1)*1.27-(i-1)*2.54+.508,-1.016,(n-1)*1.27-(i-1)*2.54-.508,'none')for i in range(1,n+1)],False)
sym('PWR_FLAG',[('1','pwr',0,0,90,'power_out',0)],[line([(0,0),(0,2.54),(-1.27,2.54),(0,3.81),(1.27,2.54),(0,2.54)])],False,True)
(L/'Macropad.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(symbols.values())+'\n)\n')
(E/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Macropad")(type "KiCad")(uri "${KIPRJMOD}/libraries/symbols/Macropad.kicad_sym")(options "")(descr "Macropad project symbols")))\n')
items=[]
def text(s,x,y,size=1.27,bold=False):items.append(f'(text {q(s)} (at {x} {y} 0) (effects (font (size {size} {size}) {"(bold yes)"if bold else""}) (justify left bottom)) (uuid {U()}))')
def wire(x,y,x2,y2):items.append(f'(wire (pts (xy {x} {y})(xy {x2} {y2})) (stroke (width 0) (type default)) (uuid {U()}))')
def label(n,x,y,angle=0):items.append(f'(label {q(n)} (at {x} {y} {angle}) {ef(.95,"(justify left bottom)")} (uuid {U()}))')
def no_connect(x,y):items.append(f'(no_connect (at {x} {y}) (uuid {U()}))')
def place(c,s,x,y,showvalue=True,refy=None):
 x=round(round(x/1.27)*1.27,4);y=round(round(y/1.27)*1.27,4)
 uid=c.get('uuid',str(uuid.uuid5(uuid.NAMESPACE_URL,'macropad:component:'+c['ref'])));ref=c['ref']; pins=geom[s]
 # Annotation set clear of pin labels and graphic body.
 if refy is None:refy= -max(p[3]for p in pins)-4
 refx=x+12.7 if s=='AHCT125' else x
 prop=f'(property "Reference" {q(ref)} (at {refx} {y+refy} 0) {ef(1.15)})'
 prop+=f'(property "Value" {q(c["value"])} (at {x} {y+refy-2.6} 0) {ef(1.05,""if showvalue else"(hide yes)")})'
 for nm,v in [('Footprint',c.get('footprint','')),('Datasheet',c.get('source','')),('Manufacturer',c.get('manufacturer','')),('MPN',c.get('mpn',''))]:prop+=f'(property {q(nm)} {q(v)} (at {x} {y} 0) {ef(1,"(hide yes)")})'
 items.append(f'(symbol (lib_id "Macropad:{s}") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom {"no"if s=="PWR_FLAG"else"yes"}) (on_board {"no"if s=="PWR_FLAG"else"yes"}) (dnp {"yes"if c.get("optional")else"no"}) (uuid {uid}) {prop} '+''.join(f'(pin {q(p[0])} (uuid {U()}))'for p in pins)+f' (instances (project "macropad" (path "/{root_uuid}" (reference {q(ref)}) (unit 1)))))')
 for n,nm,px,py,a,ty,ln in pins:
  xx=round(x+px,4);yy=round(y-py,4);net=c['pins'][n]
  if net is None:no_connect(xx,yy);continue
  if net.startswith('KEY'):continue
  dx=-5.08 if a==0 else 5.08 if a==180 else 0;dy=-5.08 if a==270 else 5.08 if a==90 else 0
  if s=='PWR_FLAG':dx=0;dy=2.54
  ex=round(xx+dx,4);ey=round(yy+dy,4);wire(xx,yy,ex,ey)
  label(net,ex,ey,180 if a==0 else 0)
by={c['ref']:c for c in components}
text('MACROPAD / 13-key USB + wireless-capable carrier',15,15,2.54,True)
text('REV A - engineering prototype | 3.3 V GPIO | USB-only power | KiCad 9 editable source',15,21,1.27)
text('01 / CONTROLLER',15,31,1.65,True)
place(by['U1'],'PicoW',56,90,refy=-46)
text('U1 solders to bottom carrier castellations',15,140,1.05)
text('Keep copper / metal clear of antenna end',15,145,1.05)
text('Unused Pico pins explicitly NC',15,150,1.05)
text('02 / 13-KEY DIODE MATRIX',116,31,1.65,True)
text('COL -> switch -> A diode K -> ROW; drive one ROW low, read COL pull-ups',116,37,1.05)
for i in range(1,14):
 c=by['SW'+str(i)];x=134+c['col']*67;y=54+c['row']*26
 place(c,'MX_Switch',x,y,False,refy=-5.08)
 # Switch outgoing pin and diode incoming pin share label KEYn_A; these are explicit labeled wires.
 place(by['D'+str(i)],'Diode',x+28,y,False,refy=-5.08)
 text(f'R{c["row"]} C{c["col"]}',x-7.62,y+7.62,.95)
 wire(round(round(x/1.27)*1.27+5.08,4),round(round(y/1.27)*1.27,4),round(round((x+28)/1.27)*1.27-5.08,4),round(round(y/1.27)*1.27,4))
 label(f'KEY{i}_A',round(round((x+14)/1.27)*1.27,4),round(round(y/1.27)*1.27,4))
text('D1-D13: 1N4148W / SOD-123, pin 1 = cathode stripe',116,144,1.05)
text('SW1-SW13: Kailh sockets underneath; switches inserted from top',116,150,1.05)
text('03 / ROTARY CONTROL',15,166,1.55,True)
place(by['ENC1'],'Encoder',51,197,False,refy=-18)
text('EC11E15244B2 | internal GPIO pull-ups',15,217,1.05)
text('04 / ANALOG JOYSTICK',107,166,1.55,True)
place(by['JOY1'],'Joystick',150,199,False,refy=-21)
text('RKJXV1224005 | 2 x 10k | 3.3 V only',107,229,1.05)
text('Axis directions calibrated in firmware',107,234,1.05)
text('05 / OPTIONAL I2C TOUCH',217,166,1.55,True)
place(by['J1'],'Header4',263,190,True,refy=-13)
place(by['R1'],'Resistor',238,210,True,refy=-4)
place(by['R2'],'Resistor',238,225,True,refy=-4)
text('DNP R1/R2 if module has pull-ups',217,235,1.0)
text('06 / I2S MICROPHONE RESERVE',302,166,1.55,True)
place(by['J3'],'Header6',353,195,True,refy=-17)
text('3.3 V module only; no analog microphone',302,222,1.0)
text('GP16 BCLK / GP17 WS / GP18 DATA',302,228,1.0)
text('07 / 5 V RGB OUTPUT',15,239,1.55,True)
place(by['U2'],'AHCT125',54,264,True,refy=-18)
place(by['R3'],'Resistor',112,254,True,refy=-4)
place(by['R4'],'Resistor',112,277,True,refy=-4)
place(by['J2'],'Header3',147,269,True,refy=-10)
place(by['C1'],'Capacitor',202,261,True,refy=-4)
place(by['C2'],'Capacitor_Polar',257,261,True,refy=-4)
place(dict(ref='#FLG01',value='USB_GND',pins={'1':'GND'}),'PWR_FLAG',320,261,False,refy=-6)
text('U2 TTL threshold accepts 3.3 V; /OE tied low',15,286,1)
text('Six external WS2812B LEDs maximum; limit brightness/current in firmware',15,291,1)
text('C2 optional: check USB inrush; external strip not included',170,281,1)
text('All optional headers / R1-R2 / C2 marked DNP',170,286,1)
text('Check footprint drawings + physical first article before manufacture',170,291,1)
lib='\n'.join(v.replace('(symbol '+q(k), '(symbol '+q('Macropad:'+k),1)for k,v in symbols.items())
# No drawing-sheet footer, keeping lower section clear; sheet title carries revision.
sch=f'''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")
(uuid {root_uuid}) (paper "A3")
(title_block (title "Macropad 13-key carrier") (date "2026-10-02") (rev "A") (company "Prototype - validate first article"))
(lib_symbols {lib})
{' '.join(items)}
(embedded_fonts no))\n'''
(E/'macropad.kicad_sch').write_text(sch)
print('Wrote manifest, schematic and project symbol library; shopping BOM is maintained separately')
