import os
import struct
import sys
import zlib

TEX = 0
LEN_OFFSET = 0

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
    global TEX
    TEX = uncompressed_tex    
    
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
    
    global LEN_OFFSET    
    LEN_OFFSET = len(uncompressed_anim_tex)
    print(0x1FF0000 - LEN_OFFSET)
        
    if file_index == 98:
        level_data = get_fe_level_data(uncompressed_anim_tex)
    else:
        level_data = get__sLevelData(uncompressed_anim_tex, LEN_OFFSET - 0x70)

HANDLES_END = 0x9876F0
TEX_END = 0x1050000
TEX_END_OFFSET = 0xE5C000
ANIM_TEX_END = 0x1FF0000
ANIM_TEX_END_OFFSET = ANIM_TEX_END - LEN_OFFSET
def get_fe_level_data(in_anim_tex):
    data = in_anim_tex[-0x140:]
    level_data = {
        "pLvl": get__sLevelData(in_anim_tex, int.from_bytes(data[0x0:0x4], "little") - ANIM_TEX_END_OFFSET), # WIP
        #"pBorderSet": int.from_bytes(data[0x4:0x8], "little"),
        #"pColourSet": int.from_bytes(data[0x8:0xc], "little"),
        #"pFixedFont": int.from_bytes(data[0xc:0x10], "little"),
        #"pPropFont": int.from_bytes(data[0x10:0x14], "little"),
        #"pScreen": int.from_bytes(data[0x14:0x18], "little"),
        #"pUIGroup": int.from_bytes(data[0x18:0x1c], "little"),
        #"pGamePropFont": int.from_bytes(data[0x1c:0x20], "little"),
        # TODO: list
        "pSFXData": get__sfxResource(in_anim_tex, int.from_bytes(data[0x20:0x24], "little") - ANIM_TEX_END_OFFSET), # WIP, broken?
        #"pLoadSaveData": int.from_bytes(data[0x24:0x28], "little"),
        "pCarStats": get_sCarBoatStats_list(in_anim_tex, int.from_bytes(data[0x28:0x2c], "little") - ANIM_TEX_END_OFFSET), #WIP
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
        #"pCups": [int.from_bytes(data[0xd0:0xd4], "little"),
        #          int.from_bytes(data[0xd4:0xd8], "little"),
        #          int.from_bytes(data[0xd8:0xdc], "little"),
        #          int.from_bytes(data[0xdc:0xe0], "little"),
        #          int.from_bytes(data[0xe0:0xe4], "little"),
        #          int.from_bytes(data[0xe4:0xe8], "little"),
        #          int.from_bytes(data[0xe8:0xec], "little"),
        #          int.from_bytes(data[0xec:0xf0], "little")],
        #"magicNumber": int.from_bytes(data[0xf0:0xf4], "little"),
        #"pOptionsMenu": int.from_bytes(data[0xf4:0xf8], "little"),
        #"ppConfigText": int.from_bytes(data[0xf8:0xfc], "little"),
        #"pExtraLevelData": int.from_bytes(data[0xfc:0x100], "little"),
        #"pRaceGridLineup": int.from_bytes(data[0x100:0x104], "little"),
        #"pGetReadyToRace": int.from_bytes(data[0x104:0x108], "little"),
        #"pLoadingTrackEditor": int.from_bytes(data[0x108:0x10c], "little"),
        #"ppCredits": int.from_bytes(data[0x10c:0x110], "little"),
        #"pTestText": int.from_bytes(data[0x110:0x114], "little"),
        #"pSomeSprite": int.from_bytes(data[0x114:0x118], "little"),
        #"pTrackEditorHelpData": int.from_bytes(data[0x118:0x11c], "little"),
        #"pQuestionMarkROB": int.from_bytes(data[0x11c:0x120], "little"),
        #"pLogoGraphic": [int.from_bytes(data[0x120:0x124], "little"),
        #                 int.from_bytes(data[0x124:0x128], "little"),
        #                 int.from_bytes(data[0x128:0x12c], "little"),
        #                 int.from_bytes(data[0x12c:0x130], "little")],
        #"pHeadLightGlowTex": int.from_bytes(data[0x130:0x134], "little"),
        #"pHeadLightFlareTex": int.from_bytes(data[0x134:0x138], "little")
    }
    #print(level_data["pCarStats"])
    return level_data

def get_sCarBoatStats_list(in_data, offset):
    car_boat_stats_list = []
    for i in range(19):
        data = int.from_bytes(in_data[offset:offset + 0x4], "little") - ANIM_TEX_END_OFFSET
        #print(data)
        car_boat_stats = get_sCarBoatStats(in_data, data)
        offset = offset + 0x4
        car_boat_stats_list.append(car_boat_stats)
    return car_boat_stats_list
    
def get_sCarBoatStats(in_data, offset):
    data = in_data[offset:offset + 0x50]
    car_boat_stats = {
    #TODO: fix pTextGroup, pCarBoatStatList
        #"pTextGroup": get_sTextGroup_list(in_data, int.from_bytes(data[0x0:0x4], "little") - ANIM_TEX_END_OFFSET, 19), # WIP, fix
        #"pCarBoatStatList": [get_pCarBoatStat(in_data, int.from_bytes(data[0x4:0x8], "little") - ANIM_TEX_END_OFFSET), # WIP
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x8:0xc], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0xc:0x10], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x10:0x14], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x14:0x18], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x18:0x1c], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x1c:0x20], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x20:0x24], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x24:0x28], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x28:0x2c], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x2c:0x30], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x30:0x34], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x34:0x38], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x38:0x3c], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x3c:0x40], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x40:0x44], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x44:0x48], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x48:0x4c], "little") - ANIM_TEX_END_OFFSET),
        #                     get_pCarBoatStat(in_data, int.from_bytes(data[0x4c:0x50], "little") - ANIM_TEX_END_OFFSET)]
    }
    return car_boat_stats
    
def get_pCarBoatStat(in_data, offset):
    data = in_data[offset:offset + 0x4]
    car_boat_stat = {
        "speed": int.from_bytes(data[0x0:0x1], "little"),
        "accel": int.from_bytes(data[0x1:0x2], "little"),
        "mass": int.from_bytes(data[0x2:0x3], "little"),
        "pad": int.from_bytes(data[0x3:0x4], "little")
    }
    return car_boat_stat
    
def get_sTextGroup_list(in_data, offset, num):
    text_group_list = []
    for i in range(num):
        data = int.from_bytes(in_data[offset:offset + 0x4], "little") - ANIM_TEX_END_OFFSET
        text_group = get_sTextGroup(in_data, data)
        offset = offset + 4
        text_group_list.append(text_group)
    return text_group_list
    
def get_sTextGroup(in_data, offset):
    data = in_data[offset:offset + 0x10]
    #print(data)
    text_group = {
        "pText": [get_char(in_data, int.from_bytes(data[0x0:0x4], "little") - ANIM_TEX_END_OFFSET),
                  get_char(in_data, int.from_bytes(data[0x4:0x8], "little") - ANIM_TEX_END_OFFSET),
                  get_char(in_data, int.from_bytes(data[0x8:0xc], "little") - ANIM_TEX_END_OFFSET),
                  get_char(in_data, int.from_bytes(data[0xc:0x10], "little") - ANIM_TEX_END_OFFSET)]
    }
    return text_group
    
def get_char(in_data, offset):
    return int.from_bytes(in_data[offset:offset + 0x1], "little", signed=True)

def get__sLevelData(in_data, offset):
    ANIM_TEX_END_OFFSET = ANIM_TEX_END - LEN_OFFSET
    print(ANIM_TEX_END_OFFSET)
    data = in_data[offset:offset + 0x64]
    level_data = {
        "pALFData": get_lsParent(in_data, int.from_bytes(data[0x0:0x4], "little") - ANIM_TEX_END_OFFSET),
        "pTSOData": get__sTSOHeader(in_data, int.from_bytes(data[0x4:0x8], "little") - ANIM_TEX_END_OFFSET),
        "pAnimData": get_animFile(in_data, int.from_bytes(data[0x8:0xc], "little") - ANIM_TEX_END_OFFSET),
        "pVISData": get__sVISHdr(in_data, int.from_bytes(data[0xc:0x10], "little") - ANIM_TEX_END_OFFSET),
        "pSVF": get_svfHeader(in_data, int.from_bytes(data[0x10:0x14], "little") - ANIM_TEX_END_OFFSET),
        "pAColGrid": get__sColGridPSX(in_data, int.from_bytes(data[0x14:0x18], "little") - ANIM_TEX_END_OFFSET),
        #"pAColGridInt": get__sColGridPSX(in_data, int.from_bytes(data[0x18:0x1c], "little") - ANIM_TEX_END_OFFSET),
        "pCameras": get__sCamData(in_data, int.from_bytes(data[0x1c:0x20], "little") - ANIM_TEX_END_OFFSET),
        "pPaths": int.from_bytes(data[0x20:0x24], "little") - ANIM_TEX_END_OFFSET,
        # TODO: list
        "pSFXData": get__sfxResource(in_data, int.from_bytes(data[0x24:0x28], "little") - ANIM_TEX_END_OFFSET),
        #"pMVARList": int.from_bytes(data[0x28:0x2c], "little") - ANIM_TEX_END_OFFSET,
        #"pGeneralText": int.from_bytes(data[0x2c:0x30], "little"),
        "pStartData": get_sStartData(in_data, int.from_bytes(data[0x30:0x34], "little") - ANIM_TEX_END_OFFSET),
        #"pPickupTable": int.from_bytes(data[0x34:0x38], "little"),
        "pPickupPosData": get__sPickupRes(in_data, int.from_bytes(data[0x38:0x3c], "little") - ANIM_TEX_END_OFFSET), # WIP
        "pAINode": get_ai_node_list(in_data, int.from_bytes(data[0x3c:0x40], "little") - ANIM_TEX_END_OFFSET), # WIP
        #"pHudRes": int.from_bytes(data[0x40:0x44], "little"),
        #"pUIGroup": int.from_bytes(data[0x44:0x48], "little"),
        # TODO: Commented for speed while testing, need to figure out size?
        #"pVFXData": get__sVfxRes(in_data, int.from_bytes(data[0x48:0x4c], "little") - ANIM_TEX_END_OFFSET), # WIP
        "pSkyVista": get_uchar(in_data, int.from_bytes(data[0x4c:0x50], "little") - ANIM_TEX_END_OFFSET), # could be a list
        "pToSkyVista": get_uchar(in_data, int.from_bytes(data[0x50:0x54], "little") - ANIM_TEX_END_OFFSET), # could be a list
        #"pTBoxData": int.from_bytes(data[0x54:0x58], "little"),
        #"pTextList": int.from_bytes(data[0x58:0x5c], "little"),
        # TODO: implement and test with game level, frontend has none
        #"pSplineOrgMats": int.from_bytes(data[0x5c:0x60], "little"),
        "pEnvMap": get__sGfxTexture(in_data, int.from_bytes(data[0x60:0x64], "little") - ANIM_TEX_END_OFFSET)
    }
    #print(level_data)
    level_data["pPaths"] = get__sCameraPath_list(in_data, level_data["pPaths"], level_data["pCameras"]["numCams"])
    #level_data["pMVARList"] = get_sMenuItemVar_list(in_data, level_data["pMVARList"], 1) # unknown how menu items
    print(level_data["pEnvMap"])
    return level_data

def get__sVfxRes(in_data, offset):
    data = in_data[offset:offset + 0x8c]
    vfx_res = {
        "vfxTex": [get__sGfxTexture(in_data, int.from_bytes(data[0x0:0x4], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x4:0x8], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x8:0xc], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0xc:0x10], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x10:0x14], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x14:0x18], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x18:0x1c], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x1c:0x20], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x20:0x24], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x24:0x28], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x28:0x2c], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x2c:0x30], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x30:0x34], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x34:0x38], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x38:0x3c], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x3c:0x40], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x40:0x44], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x44:0x48], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x48:0x4c], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x4c:0x50], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x50:0x54], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x54:0x58], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x58:0x5c], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x5c:0x60], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x60:0x64], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x64:0x68], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x68:0x6c], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x6c:0x70], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x70:0x74], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x74:0x78], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x78:0x7c], "little") - ANIM_TEX_END_OFFSET),
                   get__sGfxTexture(in_data, int.from_bytes(data[0x7c:0x80], "little") - ANIM_TEX_END_OFFSET)],
        "pWEbouncy": get__sRendObjHead(in_data, offset) #could be a list?
    }
    #print(vfx_res)
    return vfx_res

#TODO: get this finished when testing with something other than frontend, could be a graph
def get_ai_node_list(in_data, offset):
    if offset <= 0:
        return None
    ai_node_list = []
    last_node_pos = 0
    #while(True):
    return 0

#TODO: get this finished when testing with something other than frontend
def get__sPickupRes(in_data, offset):
    data = in_data[offset:offset + 0x8]
    pickup_res = {
        "pRendObjHead": get__sRendObjHead_list(in_data, int.from_bytes(data[0x0:0x4], "little") - ANIM_TEX_END_OFFSET, int.from_bytes(data[0x4:0x8], "little")),
        "numPickups": int.from_bytes(data[0x4:0x8], "little")
    }
    #print(pickup_res)
    return pickup_res
 
#TODO: get this finished when testing with something other than frontend
def get__sRendObjHead_list(in_data, offset, num):
    rend_obj_list = []
    for i in range(num):
        try:
            data = in_data[offset:offset + 0x74]
            rend_obj = get__sRendObjHead(in_data, offset)
            offset = offset + 0x74
            rend_obj_list.append(rend_obj)
        except:
            break
    #print(rend_obj_list)
    return 0
    
def get__sRendObjHead(in_data, offset):
    data = in_data[offset:offset + 0x74]
    rend_obj_data = {
        #TODO: fix srdrvushape
        "shape": get_sRdrVUShape(in_data, offset),
        "flags": int.from_bytes(data[0x58:0x5a], "little", signed=True),
        "radius": int.from_bytes(data[0x5a:0x5c], "little", signed=True),
        "numVertices": int.from_bytes(data[0x5c:0x5d], "little"),
        "numPolygons": int.from_bytes(data[0x5d:0x5e], "little"),
        "uOffset": int.from_bytes(data[0x5e:0x5f], "little"),
        "vOffset": int.from_bytes(data[0x5f:0x60], "little"),
        "envMap": get__sGfxTexture(in_data, int.from_bytes(data[0x60:0x64], "little") - ANIM_TEX_END_OFFSET),
        "r": int.from_bytes(data[0x64:0x65], "little"),
        "g": int.from_bytes(data[0x65:0x66], "little"),
        "b": int.from_bytes(data[0x66:0x67], "little"),
        "invBrightness": int.from_bytes(data[0x67:0x68], "little"),
        "minX": int.from_bytes(data[0x68:0x6a], "little"),
        "minY": int.from_bytes(data[0x6a:0x6c], "little"),
        "minZ": int.from_bytes(data[0x6c:0x6e], "little"),
        "maxX": int.from_bytes(data[0x6e:0x70], "little"),
        "maxY": int.from_bytes(data[0x70:0x72], "little"),
        "maxZ": int.from_bytes(data[0x72:0x74], "little")
    }
    #print(rend_obj_data)
    return rend_obj_data

def get_sStartData (in_data, offset):
    data = in_data[offset:offset + 0x40]
    start_data = {
        "startPos": [get_SVECTOR(data[0x0:0x8], 0),
                      get_SVECTOR(data[0x8:0x10], 0),
                      get_SVECTOR(data[0x10:0x18], 0),
                      get_SVECTOR(data[0x18:0x20], 0),
                      get_SVECTOR(data[0x20:0x28], 0),
                      get_SVECTOR(data[0x28:0x30], 0),
                      get_SVECTOR(data[0x30:0x38], 0),
                      get_SVECTOR(data[0x38:0x40], 0)]
    }
    #print(start_data)
    return start_data

def get_sMenuItemVar_list(in_data, offset, num):
    menu_item_var_list = []
    for i in range(num):
        data = int.from_bytes(in_data[offset:offset + 0x4], "little") - ANIM_TEX_END_OFFSET
        menu_item_var = get__sMenuItemVar(in_data, data)
        offset = offset + 0x4
        menu_item_var_list.append(menu_item_var)
    #print(menu_item_var_list)
    return menu_item_var_list
    
def get__sMenuItemVar(in_data, offset):
    data = in_data[offset:offset + 0x8]
    menu_item_var = {
        "pTextGroup": int.from_bytes(data[0x0:0x4], "little"), # not going to fix, just a pointer for now
        "tagMVar": int.from_bytes(data[0x4:0x8], "little", signed = True),
        "pFeedbackVar": int.from_bytes(data[0x8:0xc], "little"),
        "value": int.from_bytes(data[0xc:0x10], "little", signed = True),
        "minValue": int.from_bytes(data[0x10:0x14], "little", signed = True),
        "maxValue": int.from_bytes(data[0x14:0x18], "little", signed = True),
        "flags": int.from_bytes(data[0x18:0x1a], "little", signed = True),
        "field7_0x1a": int.from_bytes(data[0x1a:0x1b], "little"), # undefined (???)
        "field8_0x1b": int.from_bytes(data[0x1b:0x1c], "little"), # undefined (???)
    }
    #print(menu_item_var)
    return menu_item_var 
    
def get__sfxResource(in_data, offset):
    data = in_data[offset:offset + 0x24]
    sfx_resource = {
        "noVags": int.from_bytes(data[0x0:0x4], "little", signed=True),
        "dataset": int.from_bytes(data[0x4:0x8], "little", signed=True),
        "sfxData": get__sSfxResourceBlock(data[0x8:0x24])
    }
    #print(sfx_resource)
    return sfx_resource
    
def get__sSfxResourceBlock(data):
    sfx_resource_block = {
        "pos": get_vec32_(data[0x0:0xc]),
        "range": int.from_bytes(data[0xc:0x10], "little", signed=True),
        "type": int.from_bytes(data[0x10:0x14], "little", signed=True),
        "randInterval": int.from_bytes(data[0x14:0x16], "little"),
        "pitchVariance": int.from_bytes(data[0x16:0x18], "little"),
        "vag": int.from_bytes(data[0x18:0x1c], "little") #void** (???)
    }
    #print(sfx_resource_block)
    return sfx_resource_block
    
def get_vec32_(data):
    vec32 = {
        "x": int.from_bytes(data[0x0:0x4], "little", signed=True),
        "y": int.from_bytes(data[0x4:0x8], "little", signed=True),
        "z": int.from_bytes(data[0x8:0xc], "little", signed=True)
    }
    #print(vec32)
    return vec32
    
def get__sCameraPath_list(in_data, offset, num):
    camera_path_list = []
    for i in range(num):
        data = int.from_bytes(in_data[offset:offset + 0x4], "little") - ANIM_TEX_END_OFFSET
        camera_path = get__sCameraPath(in_data, data)
        offset = offset + 0x4
        camera_path_list.append(camera_path)
    #print(camera_path_list)
    return camera_path_list
    
def get__sCameraPath(in_data, offset):
    data = in_data[offset:offset + 0x8]
    camera_path = {
        "pathLength": int.from_bytes(data[0x0:0x1], "little"),
        "pathGroup": int.from_bytes(data[0x1:0x2], "little"),
        "pathSpeed": int.from_bytes(data[0x2:0x4], "little", signed = True),
        "pathIdTag": int.from_bytes(data[0x4:0x8], "little"),
    }
    #print(camera_path)
    return camera_path   

def get__sCamData(in_data, offset):
    data = in_data[offset:offset + 0x4]
    cam_data = {
        "numCams": int.from_bytes(data, "little")
    }
    #print(cam_data)
    return cam_data

def get__sColGridPSX(in_data, offset):
    data = in_data[offset:offset + 0x58]
    col_grid_psx = {
        "min": get__sColWorldVecPSX(data[0x0:0xc]),
        "max": get__sColWorldVecPSX(data[0xc:0x18]),
        "extra": get__sColWorldVecPSX(data[0x18:0x24]),
        "numCellsX": int.from_bytes(data[0x24:0x28], "little", signed = True),
        "numCellsZ": int.from_bytes(data[0x28:0x2c], "little", signed = True),
        "totalCells": int.from_bytes(data[0x2c:0x30], "little", signed = True),
        "numPolys": int.from_bytes(data[0x30:0x34], "little", signed = True),
        "numIds": int.from_bytes(data[0x34:0x38], "little", signed = True),
        "numVectors": int.from_bytes(data[0x38:0x3c], "little", signed = True),
    }
    #print(col_grid_psx)
    return col_grid_psx
    
def get__sColWorldVecPSX(data):
    col_world_psx = {
        "x": struct.unpack("<f", data[0x0:0x4])[0],
        "y": struct.unpack("<f", data[0x4:0x8])[0],
        "z": struct.unpack("<f", data[0x8:0xc])[0]
    }
    #print(col_world_psx)
    return col_world_psx

def get_svfHeader(in_data, offset):
    data = in_data[offset:offset + 0xc]
    svf_header = {
        "vectors": int.from_bytes(data[0x0:0x2], "little"),
        "slices": int.from_bytes(data[0x2:0x4], "little"),
        "anglePerSlice": int.from_bytes(data[0x4:0x6], "little"),
        "pad": int.from_bytes(data[0x6:0x8], "little"),
        "pVectors": get_SVECTOR(in_data, int.from_bytes(data[0x8:0xc], "little") - ANIM_TEX_END_OFFSET)
    }
    #print(svf_header)
    return svf_header
    
def get_SVECTOR(in_data, offset):
    data = in_data[offset:offset + 0x8]
    vector = {
        "vx": int.from_bytes(data[0x0:0x2], "little"),
        "vy": int.from_bytes(data[0x2:0x4], "little"),
        "vz": int.from_bytes(data[0x4:0x6], "little"),
        "pad": int.from_bytes(data[0x6:0x8], "little"),
    }
    #print(vector)
    return vector

def get__sVISHdr(in_data, offset):
    data = in_data[offset:offset + 0x4]
    vis_hdr = {
        "numBoxes": int.from_bytes(data[0x0:0x2], "little"),
        "defaultDepthMesh": int.from_bytes(data[0x2:0x4], "little"),
    }
    #print(vis_hdr)
    return vis_hdr
    
def get_animFile(in_data, offset):
    data = in_data[offset:offset + 0x8]
    anim_file = {
        "linearCount": int.from_bytes(data[0x0:0x2], "little"),
        "spinCount": int.from_bytes(data[0x2:0x4], "little"),
        "swingCount": int.from_bytes(data[0x4:0x6], "little"),
        "bezierCount": int.from_bytes(data[0x6:0x8], "little"),
    }
    #print(anim_file)
    return anim_file
    
def get__sTSOHeader(in_data, offset):
    data = in_data[offset:offset + 0x4]
    tso_header = {
        "numObj": int.from_bytes(data, "little")
    }
    #print(tso_header)
    return tso_header

def get_lsParent(in_data, offset):
    data = in_data[offset:offset + 0x74]
    ls_parent = {
        "shape": get_sRdrVUShape(in_data, offset),
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
        "pTex": int.from_bytes(data[0x44:0x48], "little") - ANIM_TEX_END_OFFSET,
        "pTri": int.from_bytes(data[0x48:0x4c], "little") - ANIM_TEX_END_OFFSET,
        "numFixups": int.from_bytes(data[0x4c:0x50], "little"),
        "pTexFixList": int.from_bytes(data[0x50:0x54], "little") - ANIM_TEX_END_OFFSET,
        "pAlpha": get_sRdrAlphaData(in_data, int.from_bytes(data[0x54:0x58], "little") - ANIM_TEX_END_OFFSET)
    }
    rdr_vu_shape["pTex"] = get__sGfxTexture_list(in_data, rdr_vu_shape["pTex"], rdr_vu_shape["numTex"])
    #print(rdr_vu_shape["numTex"])
    #print(rdr_vu_shape["numTri"])
    rdr_vu_shape["pTri"] = get_uint16_list(in_data, rdr_vu_shape["pTri"], rdr_vu_shape["numTri"])
    rdr_vu_shape["pTexFixList"] = get_uint_list(in_data, rdr_vu_shape["pTexFixList"], rdr_vu_shape["numFixups"])
    #print(rdr_vu_shape)
    return rdr_vu_shape
    
def get_sRdrAlphaData(in_data, offset):
    data = in_data[offset:offset + 0xF0]
    rdr_alpha_data = {
        "numPolys": int.from_bytes(data[0x0:0x4], "little", signed="True"),
        "dummy1": int.from_bytes(data[0x4:0x8], "little", signed="True"),
        "dummy2": int.from_bytes(data[0x8:0xc], "little", signed="True"),
        "dummy3": int.from_bytes(data[0xc:0x10], "little", signed="True"),
        "alphaPolys": [get_sVUTri(data[0x10:0xF0])]
    }
    #print(rdr_alpha_data)
    return rdr_alpha_data
    
def get_sVUTri(data):
    vu_tri = {
        "tex0": int.from_bytes(data[0x0:0x8], "little"),
        "texCount": int.from_bytes(data[0x8:0xc], "little"),
        "pad0": int.from_bytes(data[0xc:0x10], "little"),
        "reg1Value": int.from_bytes(data[0x10:0x18], "little"),
        "reg1Reg": int.from_bytes(data[0x18:0x20], "little"),
        "reg2Value": int.from_bytes(data[0x20:0x28], "little"),
        "reg2Reg": int.from_bytes(data[0x28:0x30], "little"),
        "reg3Value": int.from_bytes(data[0x30:0x38], "little"),
        "reg3Reg": int.from_bytes(data[0x38:0x40], "little"),
        #"nx": struct.unpack("<f", data[0x40:0x44])[0],
        #"ny": struct.unpack("<f", data[0x44:0x48])[0],
        #"nz": struct.unpack("<f", data[0x48:0x4c])[0],
        "backfaceDisable": int.from_bytes(data[0x4c:0x50], "little"),
        "vertex1": [struct.unpack("<f", data[0x50:0x54])[0],
                    struct.unpack("<f", data[0x54:0x58])[0],
                    struct.unpack("<f", data[0x58:0x5c])[0],
                    struct.unpack("<f", data[0x5c:0x60])[0]],
        "vertex2": [struct.unpack("<f", data[0x60:0x64])[0],
                    struct.unpack("<f", data[0x64:0x68])[0],
                    struct.unpack("<f", data[0x68:0x6c])[0],
                    struct.unpack("<f", data[0x6c:0x70])[0]],
        "vertex3": [struct.unpack("<f", data[0x70:0x74])[0],
                    struct.unpack("<f", data[0x74:0x78])[0],
                    struct.unpack("<f", data[0x78:0x7c])[0],
                    struct.unpack("<f", data[0x7c:0x80])[0]],
        "uv1": [struct.unpack("<f", data[0x80:0x84])[0],
                struct.unpack("<f", data[0x84:0x88])[0],
                struct.unpack("<f", data[0x88:0x8c])[0],
                struct.unpack("<f", data[0x8c:0x90])[0]],
        "uv2": [struct.unpack("<f", data[0x90:0x94])[0],
                struct.unpack("<f", data[0x94:0x98])[0],
                struct.unpack("<f", data[0x98:0x9c])[0],
                struct.unpack("<f", data[0x9c:0xa0])[0]],
        "uv3": [struct.unpack("<f", data[0xa0:0xa4])[0],
                struct.unpack("<f", data[0xa4:0xa8])[0],
                struct.unpack("<f", data[0xa8:0xac])[0],
                struct.unpack("<f", data[0xac:0xb0])[0]],
        "rgba1": [int.from_bytes(data[0xb0:0xb4], "little"),
                  int.from_bytes(data[0xb4:0xb8], "little"),
                  int.from_bytes(data[0xb8:0xbc], "little"),
                  int.from_bytes(data[0xbc:0xc0], "little")],
        "rgba2": [int.from_bytes(data[0xc0:0xc4], "little"),
                  int.from_bytes(data[0xc4:0xc8], "little"),
                  int.from_bytes(data[0xc8:0xcc], "little"),
                  int.from_bytes(data[0xcc:0xd0], "little")],
        "rgba3": [int.from_bytes(data[0xd0:0xd4], "little"),
                  int.from_bytes(data[0xd4:0xd8], "little"),
                  int.from_bytes(data[0xd8:0xdc], "little"),
                  int.from_bytes(data[0xdc:0xe0], "little")]
    }
    return vu_tri

def get_uint_list(in_data, offset, num):
    uint_list = []
    for i in range(num):
        data = int.from_bytes(in_data[offset:offset + 0x4], "little")
        offset = offset + 0x4
        uint_list.append(data)
    #print(uint_list)
    return uint_list

def get_uint(in_data, offset):
    return int.from_bytes(in_data[offset:offset + 0x4], "little")

def get_uint16_list(in_data, offset, num):
    uint16_list = []
    for i in range(num):
        data = int.from_bytes(in_data[offset:offset + 0x2], "little")
        #uint16 = get_uint16(in_data, data)
        offset = offset + 0x2
        uint16_list.append(data)
    #print(uint16_list)
    return uint16_list
    
def get_uint16(in_data, offset):
    return int.from_bytes(in_data[offset:offset + 0x2], "little")
    
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
    
def get__sGfxTexture_list(in_data, offset, num):
    gfx_texture_list = []
    for i in range(num):
        data = int.from_bytes(in_data[offset:offset + 0x4], "little") - ANIM_TEX_END_OFFSET
        gfx_texture = get__sGfxTexture(in_data, data)
        offset = offset + 0x4
        gfx_texture_list.append(gfx_texture)
    #print(gfx_texture_list)
    return gfx_texture_list
    
def get__sGfxTexture(in_data, offset):
    data = in_data[offset:offset + 0x4C]
    gfx_texture = {
        "flags": int.from_bytes(data[0x0:0x4], "little"),
        "frames": int.from_bytes(data[0x4:0x8], "little"),
        "wd": int.from_bytes(data[0x8:0xc], "little", signed="True"),
        "ht": int.from_bytes(data[0xc:0x10], "little", signed="True"),
        "fmt": int.from_bytes(data[0x10:0x14], "little", signed="True"),
        "clutVramAddr": int.from_bytes(data[0x14:0x18], "little", signed="True"),
        # fix?
        "pClut": get_uchar(in_data, int.from_bytes(data[0x18:0x1c], "little") - ANIM_TEX_END_OFFSET),
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
        # fix?
        "pBitmapList": get_uchar(in_data, int.from_bytes(data[0x48:0x4c], "little") - ANIM_TEX_END_OFFSET)
    }
    #print(gfx_texture)
    return gfx_texture

def get_uchar(in_data, offset):
    return int.from_bytes(in_data[offset:offset + 0x1], "little")

if __name__ == "__main__":
    main()