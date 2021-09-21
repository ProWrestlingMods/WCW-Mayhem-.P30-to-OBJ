import glob
import binascii
import struct
import codecs
import itertools
import math

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
    
def read_face(f):
    return int(((int.from_bytes(f.read(2), "little") / 4 ) + 1))

def read_uv(f, arr):
    scaleMod = 32767

    f.read(12)
    A = (((struct.unpack(TypeFormat.UInt16, f.read(2))[0]) / scaleMod))
    f.read(2)
    f.read(8) 
    B = (((struct.unpack(TypeFormat.UInt16, f.read(2))[0]) / scaleMod))
    f.read(2)
    f.read(8) 
    C = (((struct.unpack(TypeFormat.UInt16, f.read(2))[0]) / scaleMod))
    f.read(2)
    f.read(8) 
    D = (((struct.unpack(TypeFormat.UInt16, f.read(2))[0]) / scaleMod))
    f.read(2)

    arr.append([A, B, C, D])
    

for filename in glob.glob(path):
    with open(filename, 'rb') as f :

        f.read(2) # file ID
       
        sub_object_cnt = int.from_bytes(f.read(2), "little")    # total objects in p3o
        unknown_id = int.from_bytes(f.read(2), "little")        # unknown id        
        num_of_verts = int.from_bytes(f.read(2), "little")      # vertex count
        vertex_offset = int.from_bytes(f.read(2), "little")     # vertex offset

        f.read(2) # padding

        uv_set1_offset = int.from_bytes(f.read(2), "little") 

        f.read(6) # padding // ^this always duplicates twice 

        uv_set2_offset = int.from_bytes(f.read(2), "little")

        # temporary algorithm to work out this strange non-consistent data
        active_chunk = int.from_bytes(f.read(4), "little")
        f.seek(f.tell() - 4) # go back
        
        while True:
            temp_chunk = int.from_bytes(f.read(4), "little")
            if temp_chunk == active_chunk :
                continue
            else :
                f.seek(f.tell() - 4) # go back
                break

        num_of_textures = int.from_bytes(f.read(2), "big")  # number of textures the p3o has
        
        object_array = []
        for obj in range(0, sub_object_cnt) :
            obj_vert_cnt    = int.from_bytes(f.read(2), "little")
            f.read(2) # padding
            obj_vert_offset = int.from_bytes(f.read(2), "little")
            f.read(2) # padding
            obj_uv_offset   = int.from_bytes(f.read(2), "little")
            f.read(2) # padding

            object_array.append([obj_vert_cnt, obj_vert_offset, obj_uv_offset])

        f.read(2) # padding

        num_of_faces = int.from_bytes(f.read(2), "little") # number of quadratic faces
        face_offset = int.from_bytes(f.read(2), "little") # starting offset for faces
       
        print("\nInput: " + str(filename.split(".")))
        print("=========================================================================")
        print("Vertex Count:\t" + str(num_of_verts) + "\t[" + format(num_of_verts,'04X') + "]"
              ,"\t\tVertex Offset:\t" + str(vertex_offset) +"\t[" + format(vertex_offset,'04X') + "]")
        print("Face Count:\t" + str(num_of_faces) + "\t[" + format(num_of_faces,'04X') + "]"
              ,"\t\tFace Offset:\t" + str(face_offset) + "\t[" + format(face_offset,'04X') + "]")
        print("UV #1 Offset:\t" + str(uv_set1_offset) +"\t[" + format(uv_set1_offset,'04X') + "]",
              "\t\tUV #2 Offset:\t" + str(uv_set2_offset) +"\t[" + format(uv_set2_offset,'04X') + "]")

        print("Texture Count:\t" + str(num_of_textures))
        print("=========================================================================")

        f.seek(vertex_offset)

        vert_array = []
        for v in range(0,num_of_verts) :

            scaleIToF = 1.0 / 256.0

            vtX = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)
            vtY = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)
            vtZ = round(((struct.unpack(TypeFormat.Int16, f.read(2))[0])* scaleIToF), 4)

            # padding
            f.read(2)

            vert_array.append([f'{vtX:.4f}', f'{vtY:.4f}', f'{vtZ:.4f}'])

        f.seek(face_offset)

        faces_array = []
        for face in range(0, num_of_faces) :
            fA = read_face(f)
            fB = read_face(f)
            fC = read_face(f)
            fD = read_face(f)

            #faces_array.append([fD,fB, fA,fC])
            faces_array.append([fC,fA, fB,fD])


        # now explode the uv data
        f.seek(uv_set1_offset)

        # VU --> \/
        uv_data = []
        for uv in range(0, num_of_faces) :
            #scaleMod = 32767
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

            #uv_data.append( [ [dU,dV], [bU,bV] ,[aU,aV], [cU,cV] ] )
            uv_data.append( [ [cU,cV], [aU,aV] ,[bU,bV], [dU,dV] ] )


        # C D B A
        
        with open(filename.split(".")[0] + '.obj', 'w') as convMdl:

            for vertex in vert_array :
                convMdl.write("v %.4f %.4f %.4f\n" % (float(vertex[:][0]), float(vertex[:][1]), float(vertex[:][2])))

            face_index = 1
            for fc in faces_array :
                convMdl.write("f %i/%i %i/%i %i/%i %i/%i\n" % (int(fc[:][0]), int( face_index ), int(fc[:][1]), int( face_index + 1 ),
                                                               int(fc[:][2]), int( face_index + 2 ), int(fc[:][3]), int(face_index + 3)
                                                               ))
                face_index += 4

            for uvs in uv_data :
                convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][0][0]), float(uvs[:][0][1]))) #a
                convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][1][0]), float(uvs[:][1][1]))) #b             
                convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][2][0]), float(uvs[:][2][1]))) #c
                convMdl.write("vt %.6f %.6f\n" % (float(uvs[:][3][0]), float(uvs[:][3][1]))) #d    
           

              #convMdl.write("vt %.8f %.8f\n" % (float(uvs[:][1]), float(uvs[:][0])))





















            
        
   
