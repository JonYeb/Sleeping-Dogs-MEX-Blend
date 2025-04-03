import bpy
import os
import struct
import zlib
import mathutils
from math import radians
import bmesh

# Sleeping Dogs PC game model importer for Blender 4.2
# Based on original Blender 2.49 script
# Usage:
# 1. Unpack 'CharactersHD.big' from game with SDBIGUnpacker.exe (www.xentax.com)
# 2. Install this script as an add-on in Blender
# 3. Use the importer from File > Import > Sleeping Dogs (.perm.bin)

bl_info = {
    "name": "Sleeping Dogs Model Importer",
    "author": " Marcius Szkaradek (original author) + updated for 4.2",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "File > Import > Sleeping Dogs (.perm.bin)",
    "description": "Import models from Sleeping Dogs PC game",
    "category": "Import-Export",
}

class BinaryReader:
    def __init__(self, file):
        self.file = file
        self.debug = False
        self.log = False
        self.logfile = None
    
    def tell(self):
        return self.file.tell()
    
    def seek(self, offset, whence=0):
        self.file.seek(offset, whence)
    
    def fileSize(self):
        current = self.file.tell()
        self.file.seek(0, 2)  # Seek to end
        size = self.file.tell()
        self.file.seek(current)
        return size
    
    def i(self, count):
        result = []
        for _ in range(count):
            result.append(struct.unpack("<i", self.file.read(4))[0])
        return result
    
    def h(self, count):
        result = []
        for _ in range(count):
            result.append(struct.unpack("<H", self.file.read(2))[0])
        return result
    
    def half(self, count):
        result = []
        for _ in range(count):
            val = struct.unpack("<H", self.file.read(2))[0] * 2**-14
            result.append(val)
        return result
    
    def H(self, count):
        result = []
        for _ in range(count):
            result.append(struct.unpack("<H", self.file.read(2))[0])
        return result
    
    def f(self, count):
        result = []
        for _ in range(count):
            result.append(struct.unpack("<f", self.file.read(4))[0])
        return result
    
    def B(self, count):
        result = []
        for _ in range(count):
            result.append(struct.unpack("B", self.file.read(1))[0])
        return result
    
    def word(self, length):
        result = ""
        for _ in range(length):
            char = self.file.read(1)
            if char == b'\x00':
                self.file.seek(length - _ - 1, 1)
                break
            result += char.decode('ascii', errors='ignore')
        return result

class Mesh:
    def __init__(self):
        self.name = ""
        self.TRIANGLE = True
        self.vertexlist = []
        self.vertexuvlist = []
        self.indiceslist = []
        self.facesgroupslist = []
        self.vertexgroupslist = []
    
    def draw(self):
        # Create a new mesh and object
        mesh_data = bpy.data.meshes.new(self.name)
        obj = bpy.data.objects.new(self.name, mesh_data)
        
        # Link object to scene
        bpy.context.collection.objects.link(obj)
        
        # Create mesh with vertices
        bm = bmesh.new()
        
        # Add vertices
        for v in self.vertexlist:
            bm.verts.new((v[0], v[2], v[1]))  # Convert to Blender coordinate system
        
        bm.verts.ensure_lookup_table()
        
        # Add faces
        face_count = len(self.indiceslist) // 3
        for i in range(face_count):
            try:
                v1 = bm.verts[self.indiceslist[i*3]]
                v2 = bm.verts[self.indiceslist[i*3+1]]
                v3 = bm.verts[self.indiceslist[i*3+2]]
                bm.faces.new((v1, v2, v3))
            except Exception as e:
                print(f"Error adding face {i}: {e}")
        
        # Finalize BMesh and update mesh
        bm.to_mesh(mesh_data)
        bm.free()
        
        # Add UV data
        if self.vertexuvlist:
            mesh_data.uv_layers.new(name="UVMap")
            uv_layer = mesh_data.uv_layers[-1].data
            
            for i, loop in enumerate(mesh_data.loops):
                vidx = mesh_data.polygons[loop.polygon_index].vertices[loop.index % 3]
                if vidx < len(self.vertexuvlist):
                    uv = self.vertexuvlist[vidx]
                    uv_layer[i].uv = (uv[0], 1.0 - uv[1])  # Flip Y for Blender
        
        # Add vertex groups
        for vg in self.vertexgroupslist:
            # Create vertex groups for each bone
            for b_idx, bone_name in enumerate(vg.usedbones):
                if bone_name:
                    if bone_name not in obj.vertex_groups:
                        obj.vertex_groups.new(name=bone_name)
            
            # Assign weights
            for v_idx in range(vg.vertexIDstart, vg.vertexIDstart + vg.vertexIDcount):
                if v_idx >= len(vg.indiceslist) or v_idx - vg.vertexIDstart >= len(vg.weightslist):
                    continue
                    
                bone_indices = vg.indiceslist[v_idx - vg.vertexIDstart]
                weights = vg.weightslist[v_idx - vg.vertexIDstart]
                
                for i in range(4):
                    if weights[i] > 0 and bone_indices[i] < len(vg.usedbones):
                        bone_name = vg.usedbones[bone_indices[i]]
                        if bone_name and bone_name in obj.vertex_groups:
                            obj.vertex_groups[bone_name].add([v_idx], weights[i], 'REPLACE')
        
        # Add materials from face groups
        for fg in self.facesgroupslist:
            mat_name = fg.name
            mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
            
            # Set up material as Principled BSDF
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            bsdf = nodes.get("Principled BSDF")
            
            # Add texture if available
            if hasattr(fg, 'diffuse') and fg.diffuse:
                tex_image = nodes.new('ShaderNodeTexImage')
                try:
                    img = bpy.data.images.load(fg.diffuse)
                    tex_image.image = img
                    mat.node_tree.links.create(tex_image.outputs['Color'], bsdf.inputs['Base Color'])
                except:
                    print(f"Failed to load texture: {fg.diffuse}")
            
            # Add material to object if not already there
            if mat_name not in mesh_data.materials:
                mesh_data.materials.append(mat)
            
            # Assign material to faces
            mat_idx = mesh_data.materials.find(mat_name)
            if mat_idx >= 0:
                for i in range(fg.faceIDstart, fg.faceIDstart + fg.faceIDcount):
                    if i < len(mesh_data.polygons):
                        mesh_data.polygons[i].material_index = mat_idx
        
        # Update mesh
        mesh_data.update()
        
        # Select the imported object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

class Facesgroups:
    def __init__(self):
        self.name = ""
        self.diffuse = None
        self.faceIDstart = 0
        self.faceIDcount = 0

class Vertexgroups:
    def __init__(self):
        self.indiceslist = []
        self.weightslist = []
        self.vertexIDstart = 0
        self.vertexIDcount = 0
        self.usedbones = []

def create_object_name():
    count = len(bpy.data.objects)
    return f"SleepingDogs_{count}"

def ddsheader():
    return b'\x44\x44\x53\x20\x7C\x00\x00\x00\x07\x10\x0A\x00\x00\x04\x00\x00\x00\x04\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x0B\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x05\x00\x00\x00\x44\x58\x54\x31\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x10\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

def bin_parser(filename):
    global g, model_id, dirname
    
    streams = {}
    materials = {}
    streamsID = []
    mesh_list = []
    meshID = 0
    bonenamelist = []
    
    while True:
        if g.tell() == g.fileSize():
            break
        vm = g.i(4)
        t = g.tell()    
        g.seek(vm[3], 1)  
        vc = g.i(7)
        g.word(36)
        
        if vm[0] == -1742448933:
            vn = g.i(8)
            g.B(160)
            for m in range(vn[1]):
                bonenamelist.append(g.word(64))
            for m in range(vn[1]):
                v1 = g.H(1)[0] * 2**-14
                v2 = g.H(1)[0] * 2**-14 
                v3 = g.H(1)[0] * 2**-14 
                v4 = g.H(1)[0] * 2**-14 
                print(v1, v2, v3, v4)
        
        if vm[0] == -843079536:  # texture
            tempfile = open(filename.replace('.perm.', '.temp.'), 'rb')
            temp = BinaryReader(tempfile)
            vn = g.i(55)
            w, h, dxt = None, None, None
            
            if vn[4] == 65546:
                w, h = 2048, 2048
            if vn[4] == 65545:
                w, h = 1024, 1024
            if vn[4] == 65544:
                w, h = 512, 512
            if vn[4] == 65543:
                w, h = 256, 256
            if vn[4] == 65542:
                w, h = 128, 128
            if vn[4] == 65541:  # Fixed typo from original script
                w, h = 64, 64
                
            if vn[1] == 1:
                dxt = b'DXT1'
            if vn[1] == 3:
                dxt = b'DXT5'
            if vn[1] == 2:
                dxt = b'DXT3'
            
            if w is not None:
                new = open(dirname + os.sep + str(vc[3]) + '.dds', 'wb')
                new.write(ddsheader())
                new.seek(0xC)
                new.write(struct.pack('i', h))
                new.seek(0x10)
                new.write(struct.pack('i', w))
                new.seek(0x54)
                new.write(dxt)
                new.seek(128)
                
                tempfile.seek(vn[12])
                new.write(tempfile.read(vn[13]))
                new.close()
            tempfile.close()
        
        if vm[0] == 1845060531:  # meshes info section
            vn = g.i(15)
            vn = g.i(17)
            off = g.tell()
            offsetlist = g.i(vn[1])
            
            for m in range(vn[1]):
                g.seek(m * 4 + off + offsetlist[m])
                va = g.i(36)
                
                if str(va[11]) in streams:
                    materialID = va[3]
                    material = Facesgroups()
                    material.name = str(model_id) + '-mat-' + str(m)
                    
                    try:
                        material.diffuse = dirname + os.sep + str(materials[str(materialID)]['diffID']) + '.dds'
                    except:
                        pass
                        
                    if va[15] not in streamsID:
                        streamsID.append(va[15])
                        mesh = Mesh() 
                        mesh.name = str(model_id) + '-model-' + str(meshID)
                        mesh.TRIANGLE = True
                        mesh_list.append(mesh)
                        meshID += 1
                    
                    mesh = mesh_list[streamsID.index(va[15])]
                    
                    # Process indices stream
                    indicesstream = streams[str(va[11])]
                    g.seek(indicesstream[1])            
                    mesh.indiceslist.extend(g.h(indicesstream[0][4])[va[29]:va[29] + va[30] * 3])
                    
                    material.faceIDstart = len(mesh.indiceslist) // 3 - va[30]
                    material.faceIDcount = va[30]
                    mesh.facesgroupslist.append(material)
                    
                    # Process UV stream
                    if str(va[23]) in streams:
                        uvstream = streams[str(va[23])]
                        g.seek(uvstream[1])
                        for n in range(uvstream[0][4]):
                            tn = g.tell()
                            mesh.vertexuvlist.append(g.half(2))
                            g.seek(tn + uvstream[0][3])
                    
                    # Process skin stream
                    if str(va[19]) in streams:
                        vertexgroups = Vertexgroups()
                        skinstream = streams[str(va[19])]
                        g.seek(skinstream[1])
                        vertexgroups.vertexIDstart = len(mesh.vertexlist)
                        vertexgroups.vertexIDcount = skinstream[0][4]    
                        
                        for n in range(skinstream[0][4]):
                            tn = g.tell()
                            vertexgroups.indiceslist.append(g.B(4))
                            w1 = g.B(1)[0] / 255.0
                            w2 = g.B(1)[0] / 255.0
                            w3 = g.B(1)[0] / 255.0
                            w4 = g.B(1)[0] / 255.0
                            vertexgroups.weightslist.append([w1, w2, w3, w4])
                            g.seek(tn + skinstream[0][3])
                            
                        vertexgroups.usedbones = bonenamelist    
                        mesh.vertexgroupslist.append(vertexgroups)    
                    
                    # Process vertex position stream
                    vertexstream = streams[str(va[15])]
                    g.seek(vertexstream[1])
                    g.debug = False
                    
                    if vertexstream[0][3] == 16:
                        for n in range(vertexstream[0][4]):
                            tn = g.tell()
                            x = g.h(1)[0] * 2**-14
                            y = g.h(1)[0] * 2**-14
                            z = g.h(1)[0] * 2**-14
                            mesh.vertexlist.append([x, y, z])
                            g.seek(tn + vertexstream[0][3])
                    
                    if vertexstream[0][3] == 12:
                        for n in range(vertexstream[0][4]):
                            tn = g.tell()
                            mesh.vertexlist.append(g.f(3))
                            g.seek(tn + vertexstream[0][3])
        
        if vm[0] == -168275601:  # material section
            materials[str(vc[3])] = {}        
            vn = g.i(8)
            
            for m in range(vn[4]):
                vp = g.i(8)
                if vp[0] == -589273463:
                    materials[str(vc[3])]['diffID'] = vp[6]
                if vp[0] == -1396934011:
                    materials[str(vc[3])]['specID'] = vp[6]
                    
            g.i(4)  
        
        if vm[0] == 2056721529:  # streams section: vertex position, vertex uv, vertex indices, vertex skin
            v = g.i(32)
            streams[str(vc[3])] = [v, g.tell()]
            
        g.seek(t + vm[1])    
    
    for mesh in mesh_list:
        mesh.draw()

def import_sleeping_dogs(context, filepath):
    global g, model_id, dirname
    
    print(f"\nImporting: {filepath}\n")
    
    model_id = create_object_name()
    dirname = os.path.dirname(filepath)
    ext = filepath.split('.')[-1].lower()
    
    if ext == 'bin':
        file = open(filepath, 'rb')
        g = BinaryReader(file)
        bin_parser(filepath)
        file.close()
    
    return {'FINISHED'}

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class ImportSleepingDogs(Operator, ImportHelper):
    """Import from Sleeping Dogs PERM.BIN format"""
    bl_idname = "import_model.sleeping_dogs"
    bl_label = "Import Sleeping Dogs Model"

    # ImportHelper mixin class uses this
    filename_ext = ".bin"

    filter_glob: StringProperty(
        default="*.perm.bin",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped
    )

    def execute(self, context):
        return import_sleeping_dogs(context, self.filepath)

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSleepingDogs.bl_idname, text="Sleeping Dogs (.perm.bin)")

def register():
    bpy.utils.register_class(ImportSleepingDogs)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportSleepingDogs)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
