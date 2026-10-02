import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];P=json.loads((ROOT/'mechanical/parameters.json').read_text());M=json.loads((ROOT/'mechanical/assembly_manifest.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=80;scene.cycles.use_denoising=False
scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.world.color=(.15,.15,.15);scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-2.0
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
COL=bpy.data.collections.new('FIELD13 / actual CAD meshes');scene.collection.children.link(COL)
material_cache={}
def material(name,c,metal=0,rough=.42,texture=True):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;n=mat.node_tree.nodes;bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 if texture:
  noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1800;noise.inputs['Detail'].default_value=2
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.10;bump.inputs['Distance'].default_value=.00008
  mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);mat.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 return mat
mats={
'case':material('Warm mineral / printed GF-ABS',(.74,.78,.72),rough=.39),
'plate':material('Mist grey / printed switch plate',(.49,.56,.53),rough=.42),
'key':material('Graphite PBT',(.033,.051,.052),rough=.42),
'accent':material('Eucalyptus PBT',(.27,.58,.46),rough=.36),
'metal':material('Satin steel',(.48,.53,.52),metal=.8,rough=.25),
'brass':material('Threaded brass',(.45,.27,.06),metal=.8,rough=.3),
'pcb':material('Forest soldermask',(.016,.16,.10),rough=.32),
'rubber':material('Graphite TPU',(.025,.035,.03),rough=.65),
'black':material('Black molded polymer',(.017,.019,.018),rough=.55),
'ink':material('Bone white key legends',(.75,.8,.73),rough=.5,texture=False),
'darkink':material('Dark silkscreen',(.06,.12,.10),rough=.6,texture=False)
}
objects=[]
for item in M:
 bpy.ops.wm.stl_import(filepath=str(ROOT/item['mesh']),global_scale=.001)
 o=bpy.context.object;o.name=item['name'];o.location.x-=.054;o.location.y=.061;o.scale.y*=-1
 for c in list(o.users_collection):c.objects.unlink(o)
 COL.objects.link(o)
 name=item['name'];kind='black'
 if 'Base_shell' in name:kind='case'
 elif 'Switch_plate' in name:kind='plate'
 elif 'Keycap' in name:kind='accent' if int(name[-2:])<=2 else 'key'
 elif 'Foot_' in name or 'cap_TPU' in name:kind='rubber'
 elif 'PCB' in name or 'Pico_W_board' in name:kind='pcb'
 elif 'Insert_' in name:kind='brass'
 elif 'Screw_' in name or 'shield' in name or 'shaft' in name or 'stick' in name or 'USB_microB' in name:kind='metal'
 elif 'Encoder_knob' in name:kind='key'
 elif 'bezel' in name or 'Touch_cap' in name:kind='accent'
 o.data.materials.append(mats[kind])
 if any(x in name for x in ['Base_shell','Switch_plate','Keycap','Encoder_knob']):
  bevel=o.modifiers.new('Subtle manufactured edge','BEVEL');bevel.width=.00025;bevel.segments=2
  bevel.limit_method='ANGLE'
  weighted=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');weighted.keep_sharp=True
 for poly in o.data.polygons:poly.use_smooth=any(t in name for t in ["Keycap_", "Encoder_knob", "Joystick_cap"])
 if 'Microphone_bay' in name or 'Touch_electrode' in name:o.hide_render=True;o.hide_viewport=True
 objects.append(o)
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
try:font=bpy.data.fonts.load(fontpath)
except:font=None
labels=['LAYER','MIC','1','2','3','4','5','6','TAB','ESC','NO','GO','NEW']
def text_obj(name,text,x,y,z,size,mat):
 cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size/1000;cu.extrude=.000005
 if font:cu.font=font
 o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.location=(x/1000-.054,-y/1000+.061,z/1000);o.rotation_euler=(0,0,0);cu.materials.append(mats[mat]);return o
for i,((x,y),label) in enumerate(zip(P['keys'],labels)):
 o=text_obj(f'Legend_{i+1:02}',label,x,y,32.02,2.8 if len(label)==1 else 1.8,'darkink' if i<2 else 'ink');objects.append(o)
# Actual model branding can be printed as decal or engraved after final print calibration.
text_obj('FIELD13_brand','F I E L D   /   1 3',54,113.3,18.76,2.5,'darkink')
text_obj('prototype_badge','A 0   •   P R O T O T Y P E',54,16,18.76,1.45,'darkink')
text_obj('encoder_label','D I A L',24,20.5,18.76,1.25,'darkink')
text_obj('joystick_label','N A V',84,20.5,18.76,1.25,'darkink')
# Small visible optional-status lenses form a discreet rear strip.
for i in range(6):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.00085,location=((44+i*4)/1000-.054,-.012+.061,.01885));o=bpy.context.object;o.name=f'Optional status lens {i+1}';o.scale.z=.25;o.data.materials.append(mats['accent']);o.hide_render=True
# Fine physical knurl ribs around the printed knob exterior.
ex,ey=P['encoder']
for i in range(48):
 a=i*2*math.pi/48
 bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.00018,depth=.017,location=(ex/1000-.054+.0102*math.cos(a),-ey/1000+.061+.0102*math.sin(a),.0308));o=bpy.context.object;o.name='Knob knurl';o.data.materials.append(mats['key']);objects.append(o)
# USB cable exits rear, visualization only.
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.00175));floor=bpy.context.object;floor.name='Studio sweep';floor.data.materials.append(material('Warm studio grey',(.68,.71,.68),rough=.65,texture=False))
def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.015))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox / left',(-.18,.02,.28),12,.22,(.87,.94,1))
area('Key strip / right',(.17,-.08,.16),8,.16,(1,.90,.77))
area('Front fill',(0,.24,.20),5,.18,(1,1,1))
camd=bpy.data.cameras.new('Product camera');cam=bpy.data.objects.new('Product camera',camd);scene.collection.objects.link(cam);scene.camera=cam;camd.type='ORTHO';camd.ortho_scale=.205

def camera(loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camd.ortho_scale=scale

def render(name,loc,target,scale):
 camera(loc,target,scale);scene.render.filepath=str(ROOT/'renders'/name);bpy.ops.render.render(write_still=True)
# All views are directly rendered from the generated native CAD geometry.
render('FIELD13_studio_front.png',(.19,-.235,.225),(0,0,.016),.202)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'mechanical/FIELD13_studio.blend'))
render('FIELD13_studio_top.png',(0,-.002,.40),(0,0,.0),.170)
render('FIELD13_studio_rear.png',(-.16,.20,.145),(0,0,.015),.205)
# Exploded separation. No artistic coordinate change in primary views.
for o in objects:
 n=o.name
 dz=0
 if 'PCB' in n or 'Pico_' in n or 'Hotswap' in n or 'Joystick_body' in n or 'Encoder_body' in n or 'Encoder_shaft' in n:dz=.032
 elif 'Switch_plate' in n or 'Insert' in n or 'Touch_' in n or 'bezel' in n:dz=.063
 elif n.startswith('Switch_'):dz=.088
 elif 'Keycap' in n or 'Legend' in n or 'knob' in n or 'Knob knurl' in n or 'cap_TPU' in n or 'Joystick_stick' in n:dz=.120
 elif n.startswith('Foot_'):dz=-.010
 o.location.z+=dz
# Hide assembled decals/lenses on exploded image.
for o in scene.objects:
 if any(x in o.name for x in ['brand','badge','_label','Optional status lens']):o.hide_render=True
render('FIELD13_exploded.png',(.24,-.285,.26),(0,0,.070),.260)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'mechanical/FIELD13_exploded.blend'))
