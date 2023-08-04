import os
import struct
import sys
import zlib

def main():

    file_index = int(sys.argv[1])
    file_path = "BB/" + str(file_index // 10) + "/" + str(file_index % 10) + ".BBK"
    file_path_decompressed = "BBDecomp/" + str(file_index // 10) + "/" + str(file_index % 10) + "/"
    sfx_path = file_path_decompressed + "SFX/"
    if not os.path.exists(file_path_decompressed):
        os.makedirs(file_path_decompressed)
    if not os.path.exists(sfx_path):
        os.makedirs(sfx_path)

    with open(file_path, mode="rb") as f:
        contents = f.read()

    SFX_CAT_OFFSET = 0x38
    SFX_INFO_LEN = 0x20
    SFX_COMPRESSED_SIZE_OFFSET = 0x14EC
    sfx_offset = SFX_COMPRESSED_SIZE_OFFSET + 4
    sfx_compressed_size = contents[SFX_COMPRESSED_SIZE_OFFSET:SFX_COMPRESSED_SIZE_OFFSET + 4]
    sfx_compressed_size = int.from_bytes(sfx_compressed_size, "little")
    sfx_end = sfx_offset + sfx_compressed_size
    
    uncompressed_sfx = zlib.decompress(contents[sfx_offset:sfx_end])
    with open(file_path_decompressed + "SFX.BBK", mode="wb") as o:
        o.write(uncompressed_sfx)
    
    # Store information about sfx
    sfx_index = 0
    sfx_info = []
    sfx_info_list = []
    hasAllZeros = False
    while not hasAllZeros:
        sfx_info = contents[SFX_CAT_OFFSET + (SFX_INFO_LEN * sfx_index):SFX_CAT_OFFSET + SFX_INFO_LEN * sfx_index + SFX_INFO_LEN]
        sfx_index = sfx_index + 1
        hasAllZeros = True
        for b in sfx_info:
            if b != 0:
                sfx_addr = int.from_bytes(sfx_info[0x0:0x4], "little")
                sfx_size = int.from_bytes(sfx_info[0x4:0x8], "little")
                sfx_img_addr = int.from_bytes(sfx_info[0x8:0xC], "little")
                sfx_img_size = int.from_bytes(sfx_info[0xC:0x10], "little")
                sfx_multi = int.from_bytes(sfx_info[0x10:0x14], "little")
                sfx_loop = int.from_bytes(sfx_info[0x14:0x18], "little")
                sfx_resource_id = int.from_bytes(sfx_info[0x18:0x1C], "little")
                sfx_loop_addr = int.from_bytes(sfx_info[0x1C:0x20], "little")
                sfx_info = {"addr": sfx_addr, "size": sfx_size, "img_addr": sfx_img_addr, "img_size": sfx_img_size,
                            "multi": sfx_multi, "loop": sfx_loop, "resource_id": sfx_resource_id, "loop_addr": sfx_loop_addr}
                sfx_info_list.append(sfx_info)
                hasAllZeros = False
                break
    
    current_sfx_offset = 0
    for s in sfx_info_list:
        current_sfx_offset = current_sfx_offset + s["size"]
        adp = uncompressed_sfx[s["addr"] - 0x5000:s["addr"] - 0x5000 + s["size"]]
        with open(sfx_path + str(s["resource_id"]) + ".adp", mode="wb") as o:
            o.write(adp)
        with open(sfx_path + str(s["resource_id"]) + ".adp.txth", mode="w") as o:
            o.write("codec = PSX\n")
            if s["multi"] == 1024:
                o.write("sample_rate = 11025\n")
            elif s["multi"] == 2048:
                o.write("sample_rate = 22050\n")
            elif s["multi"] == 2136:
                o.write("sample_rate = 32000\n")
            elif s["multi"] == 4096:
                o.write("sample_rate = 44100\n")
            else:
                print("Warning: no known sample rate for " + str(s["resource_id"]) + ".adp")
            o.write("channels = 1\n")
            o.write("interleave = 0x1000\n")
            o.write("start_offset = 0x10\n")
            o.write("num_samples = data_size\n")
            if s["loop"] == True:
                o.write("loop_start_sample = " + str(s["loop_addr"] - s["addr"]) + "\n")
                o.write("loop_end = data_size")
 
    tex_compressed_size_offset = sfx_end
    tex_offset = tex_compressed_size_offset + 4
    tex_compressed_size = contents[tex_compressed_size_offset:tex_compressed_size_offset + 4]
    tex_compressed_size = int.from_bytes(tex_compressed_size, "little")
    tex_end = tex_offset + tex_compressed_size
    
    uncompressed_tex = zlib.decompress(contents[tex_offset:tex_end])
    with open(file_path_decompressed + "TEX.BBK", mode="wb") as o:
        o.write(uncompressed_tex)
        
    anim_tex_compressed_size_offset = tex_end
    anim_tex_offset = anim_tex_compressed_size_offset + 4
    anim_tex_compressed_size = contents[anim_tex_compressed_size_offset:anim_tex_compressed_size_offset + 4]
    anim_tex_compressed_size = int.from_bytes(anim_tex_compressed_size, "little")
    anim_tex_end = anim_tex_offset + anim_tex_compressed_size
    
    uncompressed_anim_tex = zlib.decompress(contents[anim_tex_offset:anim_tex_end])
    with open(file_path_decompressed + "ANIM_TEX.BBK", mode="wb") as o:
        o.write(uncompressed_anim_tex)
        
    misc_compressed_size_offset = anim_tex_end
    misc_offset = misc_compressed_size_offset + 4
    misc_compressed_size = contents[misc_compressed_size_offset:misc_compressed_size_offset + 4]
    misc_compressed_size = int.from_bytes(misc_compressed_size, "little")
    misc_end = misc_offset + misc_compressed_size
    
    uncompressed_misc = zlib.decompress(contents[misc_offset:misc_end])
    with open(file_path_decompressed + "HANDLES.BBK", mode="wb") as o:
        o.write(uncompressed_misc)
        
    if file_index == 98:
        level_data = get_fe_level_data(uncompressed_anim_tex)
    #print(level_data)

HANDLES_END = 0x9876F0
TEX_END = 0x1050000
ANIM_TEX_END = 0x1FF0000
ANIM_TEX_END_OFFSET = 0x16ECF4C
def get_fe_level_data(in_anim_tex):
    data = in_anim_tex[-0x140:]
    level_data = {
        "pLvl": get__sLevelData(in_anim_tex, int.from_bytes(data[0x0:0x4], "little") - ANIM_TEX_END_OFFSET), # working on this
        "pBorderSet": int.from_bytes(data[0x4:0x8], "little"),
        "pColourSet": int.from_bytes(data[0x8:0xc], "little"),
        "pFixedFont": int.from_bytes(data[0xc:0x10], "little"),
        "pPropFont": int.from_bytes(data[0x10:0x14], "little"),
        "pScreen": int.from_bytes(data[0x14:0x18], "little"),
        "pUIGroup": int.from_bytes(data[0x18:0x1c], "little"),
        "pGamePropFont": int.from_bytes(data[0x1c:0x20], "little"),
        "pSFXData": int.from_bytes(data[0x20:0x24], "little"),
        "pLoadSaveData": int.from_bytes(data[0x24:0x28], "little"),
        "pCarStats": int.from_bytes(data[0x28:0x2c], "little"),
        "pBoatStats": int.from_bytes(data[0x2c:0x30], "little"),
        "pCameras": int.from_bytes(data[0x30:0x34], "little"),
        "pPaths": int.from_bytes(data[0x34:0x38], "little"),
        "carDef": [int.from_bytes(data[0x38:0x3C], "little"), 
                   int.from_bytes(data[0x3c:0x40], "little"),
                   int.from_bytes(data[0x40:0x44], "little"),
                   int.from_bytes(data[0x44:0x48], "little"),
                   int.from_bytes(data[0x48:0x4c], "little"),
                   int.from_bytes(data[0x4c:0x50], "little"),
                   int.from_bytes(data[0x50:0x54], "little"),
                   int.from_bytes(data[0x54:0x58], "little"),
                   int.from_bytes(data[0x58:0x5c], "little"),
                   int.from_bytes(data[0x5c:0x60], "little"),
                   int.from_bytes(data[0x60:0x64], "little"),
                   int.from_bytes(data[0x64:0x68], "little"),
                   int.from_bytes(data[0x68:0x6c], "little"),
                   int.from_bytes(data[0x6c:0x70], "little"),
                   int.from_bytes(data[0x70:0x74], "little"),
                   int.from_bytes(data[0x74:0x78], "little"),
                   int.from_bytes(data[0x78:0x7c], "little"),
                   int.from_bytes(data[0x7c:0x80], "little"),
                   int.from_bytes(data[0x80:0x84], "little")],
        "boatDef": [int.from_bytes(data[0x84:0x88], "little"),
                    int.from_bytes(data[0x88:0x8C], "little"), 
                    int.from_bytes(data[0x8c:0x90], "little"),
                    int.from_bytes(data[0x90:0x94], "little"),
                    int.from_bytes(data[0x94:0x98], "little"),
                    int.from_bytes(data[0x98:0x9c], "little"),
                    int.from_bytes(data[0x9c:0xa0], "little"),
                    int.from_bytes(data[0xa0:0xa4], "little"),
                    int.from_bytes(data[0xa4:0xa8], "little"),
                    int.from_bytes(data[0xa8:0xac], "little"),
                    int.from_bytes(data[0xac:0xb0], "little"),
                    int.from_bytes(data[0xb0:0xb4], "little"),
                    int.from_bytes(data[0xb4:0xb8], "little"),
                    int.from_bytes(data[0xb8:0xbc], "little"),
                    int.from_bytes(data[0xbc:0xc0], "little"),
                    int.from_bytes(data[0xc0:0xc4], "little"),
                    int.from_bytes(data[0xc4:0xc8], "little"),
                    int.from_bytes(data[0xc8:0xcc], "little"),
                    int.from_bytes(data[0xcc:0xd0], "little")],
        "pCups": [int.from_bytes(data[0xd0:0xd4], "little"),
                  int.from_bytes(data[0xd4:0xd8], "little"),
                  int.from_bytes(data[0xd8:0xdc], "little"),
                  int.from_bytes(data[0xdc:0xe0], "little"),
                  int.from_bytes(data[0xe0:0xe4], "little"),
                  int.from_bytes(data[0xe4:0xe8], "little"),
                  int.from_bytes(data[0xe8:0xec], "little"),
                  int.from_bytes(data[0xec:0xf0], "little")],
        "magicNumber": int.from_bytes(data[0xf0:0xf4], "little"),
        "pOptionsMenu": int.from_bytes(data[0xf4:0xf8], "little"),
        "ppConfigText": int.from_bytes(data[0xf8:0xfc], "little"),
        "pExtraLevelData": int.from_bytes(data[0xfc:0x100], "little"),
        "pRaceGridLineup": int.from_bytes(data[0x100:0x104], "little"),
        "pGetReadyToRace": int.from_bytes(data[0x104:0x108], "little"),
        "pLoadingTrackEditor": int.from_bytes(data[0x108:0x10c], "little"),
        "ppCredits": int.from_bytes(data[0x10c:0x110], "little"),
        "pTestText": int.from_bytes(data[0x110:0x114], "little"),
        "pSomeSprite": int.from_bytes(data[0x114:0x118], "little"),
        "pTrackEditorHelpData": int.from_bytes(data[0x118:0x11c], "little"),
        "pQuestionMarkROB": int.from_bytes(data[0x11c:0x120], "little"),
        "pLogoGraphic": [int.from_bytes(data[0x120:0x124], "little"),
                         int.from_bytes(data[0x124:0x128], "little"),
                         int.from_bytes(data[0x128:0x12c], "little"),
                         int.from_bytes(data[0x12c:0x130], "little")],
        "pHeadLightGlowTex": int.from_bytes(data[0x130:0x134], "little"),
        "pHeadLightFlareTex": int.from_bytes(data[0x134:0x138], "little")
    }
    #print(level_data)
    return level_data

def get__sLevelData(in_data, offset):
    data = in_data[offset:offset + 0x64]
    level_data = {
        "pALFData": get_lsParent(in_data, int.from_bytes(data[0x0:0x4], "little") - ANIM_TEX_END_OFFSET), # working on this
        "pTSOData": int.from_bytes(data[0x4:0x8], "little"),
        "pAnimData": int.from_bytes(data[0x8:0xc], "little"),
        "pVISData": int.from_bytes(data[0xc:0x10], "little"),
        "pSVF": int.from_bytes(data[0x10:0x14], "little"),
        "pAColGrid": int.from_bytes(data[0x14:0x18], "little"),
        "pAColGridInt": int.from_bytes(data[0x18:0x1c], "little"),
        "pCameras": int.from_bytes(data[0x1c:0x20], "little"),
        "pPaths": int.from_bytes(data[0x20:0x24], "little"),
        "pSFXData": int.from_bytes(data[0x24:0x28], "little"),
        "pMVARList": int.from_bytes(data[0x28:0x2c], "little"),
        "pGeneralText": int.from_bytes(data[0x2c:0x30], "little"),
        "pStartData":int.from_bytes(data[0x30:0x34], "little"),
        "pPickupTable": int.from_bytes(data[0x34:0x38], "little"),
        "pPickupPosData": int.from_bytes(data[0x38:0x3c], "little"),
        "pAINode": int.from_bytes(data[0x3c:0x40], "little"),
        "pHudRes": int.from_bytes(data[0x40:0x44], "little"),
        "pUIGroup": int.from_bytes(data[0x44:0x48], "little"),
        "pVFXData": int.from_bytes(data[0x48:0x4c], "little"),
        "pSkyVista": int.from_bytes(data[0x4c:0x50], "little"),
        "pToSkyVista": int.from_bytes(data[0x50:0x54], "little"),
        "pTBoxData": int.from_bytes(data[0x54:0x58], "little"),
        "pTextList": int.from_bytes(data[0x58:0x5c], "little"),
        "pSplineOrgMats": int.from_bytes(data[0x5c:0x60], "little"),
        "pEnvMap": int.from_bytes(data[0x60:0x64], "little")
    }
    #print(level_data)
    return level_data

def get_lsParent(in_data, offset):
    data = in_data[offset: offset + 0x74]
    ls_parent = {
        "shape": get_sRdrVUShape(in_data, offset), # working on this
        "minX": int.from_bytes(data[0x58:0x5c], "little", signed="True"),
        "minZ": int.from_bytes(data[0x5c:0x60], "little", signed="True"),
        "xCells": int.from_bytes(data[0x60:0x64], "little", signed="True"),
        "zCells": int.from_bytes(data[0x64:0x68], "little", signed="True"),
        "cellSize": int.from_bytes(data[0x68:0x6c], "little", signed="True"),
        "overlap": int.from_bytes(data[0x6c:0x70], "little", signed="True"),
        "offsetArray": [int.from_bytes(data[0x70:0x74], "little")]
    }
    #print(ls_parent)
    return ls_parent
    
def get_sRdrVUShape(in_data, offset):
    data = in_data[offset:offset + 0x58]
    rdr_vu_shape = {
        "version": struct.unpack("<f", data[0x0:0x4])[0],
        "rdrFlags": int.from_bytes(data[0x4:0x8], "little"),
        "mat": get__sMat33(data[0x8:0x2c]),
        "pos": get__sVec3(data[0x2c:0x38]),
        "numTex": int.from_bytes(data[0x38:0x3c], "little", signed="True"),
        "numTri": int.from_bytes(data[0x3c:0x40], "little", signed="True"),
        "radius": struct.unpack("<f", data[0x40:0x44])[0],
        "pTex": [get__sGfxTexture(in_data, int.from_bytes(in_data[int.from_bytes(data[0x44:0x48], "little") - ANIM_TEX_END_OFFSET + 4 * i:int.from_bytes(data[0x44:0x48], "little") - ANIM_TEX_END_OFFSET + 4 * i + 4], "little") - ANIM_TEX_END_OFFSET) for i in range(int.from_bytes(data[0x38:0x3c], "little", signed="True"))], # working on this
        "pTri": int.from_bytes(data[0x48:0x4c], "little"),
        "numFixups": int.from_bytes(data[0x4c:0x50], "little"),
        "pTexFixList": int.from_bytes(data[0x50:0x54], "little"),
        "pAlpha": int.from_bytes(data[0x54:0x58], "little")
    }
    #print(rdr_vu_shape)
    return rdr_vu_shape
    
def get__sMat33(data):
    mat_33 = {
        "Xx": struct.unpack("<f", data[0x0:0x4])[0],
        "Xy": struct.unpack("<f", data[0x4:0x8])[0],
        "Xz": struct.unpack("<f", data[0x8:0xc])[0],
        "Yx": struct.unpack("<f", data[0xc:0x10])[0],
        "Yy": struct.unpack("<f", data[0x10:0x14])[0],
        "Yz": struct.unpack("<f", data[0x14:0x18])[0],
        "Zx": struct.unpack("<f", data[0x18:0x1c])[0],
        "Zy": struct.unpack("<f", data[0x1c:0x20])[0],
        "Zz": struct.unpack("<f", data[0x20:0x24])[0],
    }
    #print(mat_33)
    return mat_33

def get__sVec3(data):
    vec_3 = {
        "x": struct.unpack("<f", data[0x0:0x4])[0],
        "y": struct.unpack("<f", data[0x4:0x8])[0],
        "z": struct.unpack("<f", data[0x8:0xc])[0],
    }
    #print(vec_3)
    return vec_3
    
def get__sGfxTexture(in_data, offset):
    data = in_data[offset:offset + 0x4c]
    gfx_texture = {
        "flags": int.from_bytes(data[0x0:0x4], "little"),
        "frames": int.from_bytes(data[0x4:0x8], "little"),
        "wd": int.from_bytes(data[0x8:0xc], "little", signed="True"),
        "ht": int.from_bytes(data[0xc:0x10], "little", signed="True"),
        "fmt": int.from_bytes(data[0x10:0x14], "little", signed="True"),
        "clutVramAddr": int.from_bytes(data[0x14:0x18], "little", signed="True"),
        "pClut": int.from_bytes(data[0x18:0x1c], "little") - ANIM_TEX_END_OFFSET, #change to char (this is a pointer)
        "miptbp1L": int.from_bytes(data[0x1c:0x20], "little"),
        "miptbp1H": int.from_bytes(data[0x20:0x24], "little"),
        "miptbp2L": int.from_bytes(data[0x24:0x28], "little"),
        "miptbp2H": int.from_bytes(data[0x28:0x2c], "little"),
        "idxList": [int.from_bytes(data[0x2c:0x30], "little", signed="True"),
                    int.from_bytes(data[0x30:0x34], "little", signed="True"),
                    int.from_bytes(data[0x34:0x38], "little", signed="True"),
                    int.from_bytes(data[0x38:0x3c], "little", signed="True"),
                    int.from_bytes(data[0x3c:0x40], "little", signed="True"),
                    int.from_bytes(data[0x40:0x44], "little", signed="True"),
                    int.from_bytes(data[0x44:0x48], "little", signed="True")],
        "pBitmapList": int.from_bytes(data[0x48:0x4c], "little") - ANIM_TEX_END_OFFSET #change to char (this is a pointer)
    }
    #print(gfx_texture)
    return gfx_texture

if __name__ == "__main__":
    main()