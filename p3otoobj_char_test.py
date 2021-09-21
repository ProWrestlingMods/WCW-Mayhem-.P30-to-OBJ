import glob
import binascii
import struct
import codecs
import itertools
import math

class MDL:
 def __init__(self):
    self.vertex_count  = 0
    self.vertex_offset = 0
    self.uv_offset     = 0
    self.uv_count      = 0
    self.face_count    = 0 
    self.vertices      = []
    self.faces         = []
    self.uvs           = []

class P3O:
 def __init__(self):
    self.object_count   = 0
    self.face_count     = 0
    self.face_offset    = 0
    self.identifier     = 0
    self.vert_count     = 0
    self.vert_offset    = 0
    self.uv_offset_1    = 0
    self.uv_offset_2    = 0
    self.tex_count      = 0
    self.meshes         = ()



path = "*.p3o"

class TypeFormat:
    SByte = '<b'
    Byte = '<B'
    Int16 = '<h'
    BInt16 = '>h'
    UInt16 = '<H'
    Int32 = '<i'
    UInt32 = '<I'
    Int64 = '<l'
    UInt64 = '<L'
    Single = '<f'
    Double = '<d'

def read_texture_data(f):
    active_chunk = int.from_bytes(f.read(4), "little")
    f.seek(f.tell() - 4) # go back
    
    while True:
        temp_chunk = int.from_bytes(f.read(4), "little")
        if temp_chunk == active_chunk :
            continue
        else :
            f.seek(f.tell() - 4) # go back
            break

def read_verts(f, vert_count):
    vert_array = []
    for v in range(0, vert_count) :

        scaleIToF = 1.0 / 256.0

        vtX = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)
        vtY = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)
        vtZ = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)

        # padding
        f.read(2)

        vert_array.append([f'{vtX:.4f}', f'{vtY:.4f}', f'{vtZ:.4f}'])
    return vert_array
    
def read_face(f):
    return int(((int.from_bytes(f.read(2), "little") / 4 ) + 1))



def read_uvs(f, faces):
    uv_data = []
    for uv in range(0, faces) :
        scaleMod = -64

        f.read(12)
        aU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
        aV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
        f.read(10) 
        bU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
        bV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
        f.read(10) 
        cU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
        cV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
        f.read(10)
        dU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
        dV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
        f.read(2)

        uv_data.append( [ [cU,cV], [aU,aV] ,[bU,bV], [dU,dV] ] )
        
    return uv_data

for filename in glob.glob(path):
    with open(filename, 'rb') as f :

        f.read(2)                                                       # file ID

        # Header
        mesh = P3O()
        mesh.object_count   = int.from_bytes(f.read(2), "little")       # total objects in p3o
        mesh.identifier     = int.from_bytes(f.read(2), "little")       # unknown id        
        mesh.vert_count     = int.from_bytes(f.read(2), "little")       # vertex count    
        mesh.vert_offset    = int.from_bytes(f.read(2), "little")       # vertex offset
        f.read(2)                                                       # padding
        mesh.uv_offset_1 = int.from_bytes(f.read(2), "little") 
        f.read(6)                                                       # padding // ^this always duplicates twice 
        mesh.uv_offset_2 = int.from_bytes(f.read(2), "little")      
        read_texture_data(f)                                            # temporary algorithm to work out this strange non-consistent data
        mesh.tex_count  = int.from_bytes(f.read(2), "big")              # number of textures the p3o has

        object_array = []
        sub_meshes =[]
        for obj in range(0, mesh.object_count) :

            sub_mesh = MDL()
            sub_mesh.vertex_count       = int.from_bytes(f.read(2), "little")
            sub_mesh.face_count         = (4 * int((sub_mesh.vertex_count / 4)))
            sub_mesh.uv_count           = ((4 * sub_mesh.vertex_count) + 36)

            f.read(2) # padding
            sub_mesh.vertex_offset      = int.from_bytes(f.read(2), "little")            
            f.read(2) # padding

            # now split the objects into poly groups
            last_position                       = f.tell()
            f.seek(sub_mesh.vertex_offset)
            sub_mesh.vertices                   = read_verts(f, sub_mesh.vertex_count)
            f.seek(last_position)
            
            sub_mesh.uv_offset          = int.from_bytes(f.read(2), "little")
            f.read(2) # padding

            sub_meshes.append(sub_mesh)
            object_array.append([sub_mesh.vertex_count, sub_mesh.vertex_offset, sub_mesh.uv_offset])

        f.read(2) # padding

        mesh.face_count     = int.from_bytes(f.read(2), "little")       # number of quadratic faces
        mesh.face_offset    = int.from_bytes(f.read(2), "little")       # starting offset for faces

        previous_face_offset    = 0
        previous_uv_offset      = 0
        for obj in sub_meshes:
            last_position                       = f.tell()

            # HACK: remember face offset for polygon groups
            if previous_face_offset <= 0 :
                f.seek(mesh.face_offset)
            else:
                f.seek(previous_face_offset)

            faces_array = []
            for face in range(0, int((obj.face_count / 4)) ) :
                fA = read_face(f)
                fB = read_face(f)
                fC = read_face(f)
                fD = read_face(f)
                faces_array.append([fC,fA, fB,fD])            

            obj.faces = faces_array
            previous_face_offset = f.tell()

            # HACK: same for UV
            if previous_uv_offset <= 0 :
                f.seek(mesh.uv_offset_1)
            else:
                f.seek(previous_uv_offset)

            uv_data = []
            for uv in range(0, int((obj.face_count / 4))) :
                scaleMod = -64

                f.read(12)
                aU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
                aV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
                f.read(10) 
                bU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
                bV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
                f.read(10) 
                cU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
                cV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
                f.read(10)
                dU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
                dV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
                f.read(2)

                uv_data.append( [ [cU,cV], [aU,aV] ,[bU,bV], [dU,dV] ] )
                
            obj.uvs = uv_data
            previous_uv_offset = f.tell()
                      
            
       
        print("\nInput: " + str(filename.split(".")))
        print("=========================================================================")
        print("Vertex Count:\t" + str(mesh.vert_count) + "\t[" + format(mesh.vert_count,'04X') + "]"
              ,"\t\tVertex Offset:\t" + str(mesh.vert_offset) +"\t[" + format(mesh.vert_offset,'04X') + "]")
        print("Face Count:\t" + str(mesh.face_count) + "\t[" + format(mesh.face_count,'04X') + "]"
              ,"\t\tFace Offset:\t" + str(mesh.face_offset) + "\t[" + format(mesh.face_offset,'04X') + "]")
        print("UV #1 Offset:\t" + str(mesh.uv_offset_1) +"\t[" + format(mesh.uv_offset_1,'04X') + "]",
              "\t\tUV #2 Offset:\t" + str(mesh.uv_offset_2) +"\t[" + format(mesh.uv_offset_2,'04X') + "]")

        print("Texture Count:\t" + str(mesh.tex_count ))
        print("=========================================================================")

        f.seek(mesh.vert_offset)

        vert_array = []
        for v in range(0,mesh.vert_count) :

            scaleIToF = 1.0 / 256.0

            vtX = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)
            vtY = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)
            vtZ = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)

            # padding
            f.read(2)

            vert_array.append([f'{vtX:.4f}', f'{vtY:.4f}', f'{vtZ:.4f}'])

        f.seek(mesh.face_offset)

        faces_array = []
        for face in range(0, mesh.face_count) :
            fA = read_face(f)
            fB = read_face(f)
            fC = read_face(f)
            fD = read_face(f)

            #faces_array.append([fD,fB, fA,fC])
            faces_array.append([fC,fA, fB,fD])


        # now explode the uv data
        f.seek(mesh.uv_offset_1)

        # VU --> \/
        uv_data = []
        for uv in range(0, mesh.face_count) :
            scaleMod = -64

            f.read(12)
            aU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
            aV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
            f.read(10) 
            bU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
            bV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
            f.read(10) 
            cU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
            cV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
            f.read(10)
            dU = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
            dV = (float(struct.unpack(TypeFormat.Byte, f.read(1))[0]) / scaleMod)
            f.read(2)

            uv_data.append( [ [cU,cV], [aU,aV] ,[bU,bV], [dU,dV] ] )


        # C D B A

        with open(filename.split(".")[0] + '_2.obj', 'w') as convMdl:           
            convMdl.write("o " + str(filename.split(".")[0]) + "\n")
            convMdl.write("s 1\n")
            
            for idx, obj in enumerate(sub_meshes, start=1):
                convMdl.write("g " + str(filename.split(".")[0])+ "_" + str(idx) + "\n")
                convMdl.write("usemtl mat_" + str(filename.split(".")[0])+ "_" + str(idx) + "\n")

                for vertex in obj.vertices :
                    convMdl.write("v %.4f %.4f %.4f\n" % (float(vertex[:][0]), float(vertex[:][1]), float(vertex[:][2])))

                for uvs in obj.uvs :
                    convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][0][0]), float(uvs[:][0][1]))) #a
                    convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][1][0]), float(uvs[:][1][1]))) #b             
                    convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][2][0]), float(uvs[:][2][1]))) #c
                    convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][3][0]), float(uvs[:][3][1]))) #d   

                face_index = 1
                for fc in obj.faces :
                    convMdl.write("f %i/%i %i/%i %i/%i %i/%i\n" % (int(fc[:][0]), int( face_index ), int(fc[:][1]), int( face_index + 1 ),
                                                                   int(fc[:][2]), int( face_index + 2 ), int(fc[:][3]), int(face_index + 3)
                                                                   ))
                    face_index += 4  
            
        
        with open(filename.split(".")[0] + '.obj', 'w') as convMdl:
            
            convMdl.write("o " + str(filename.split(".")[0]) + "\n")

            for vertex in vert_array :
                convMdl.write("v %.4f %.4f %.4f\n" % (float(vertex[:][0]), float(vertex[:][1]), float(vertex[:][2])))

            face_index = 1
            for fc in faces_array :
                convMdl.write("f %i/%i %i/%i %i/%i %i/%i\n" % (int(fc[:][0]), int( face_index ), int(fc[:][1]), int( face_index + 1 ),
                                                               int(fc[:][2]), int( face_index + 2 ), int(fc[:][3]), int(face_index + 3)
                                                               ))
                face_index += 4

            convMdl.write("s 1\n")

            for uvs in uv_data :
                convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][0][0]), float(uvs[:][0][1]))) #a
                convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][1][0]), float(uvs[:][1][1]))) #b             
                convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][2][0]), float(uvs[:][2][1]))) #c
                convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][3][0]), float(uvs[:][3][1]))) #d    
           

              #convMdl.write("vt %.8f %.8f\n" % (float(uvs[:][1]), float(uvs[:][0])))





















            
        
   
