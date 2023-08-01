import os
import sys
import zlib

def main():

    file_index = int(sys.argv[1])
    file_path = "BB/" + str(file_index // 10) + "/" + str(file_index % 10) + ".BBK"
    file_path_decompressed = "BBDecomp/" + str(file_index // 10) + "/" + str(file_index % 10) + "/"
    if not os.path.exists(file_path_decompressed):
        os.makedirs(file_path_decompressed)

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
                print(sfx_info)
                sfx_info_list.append(sfx_info)
                hasAllZeros = False
                break
    
    current_sfx_offset = 0
    for s in sfx_info_list:
        current_sfx_offset = current_sfx_offset + s["size"]
        adp = uncompressed_sfx[current_sfx_offset - s["size"]:current_sfx_offset]
        with open(file_path_decompressed + str(s["resource_id"]) + ".adp", mode="wb") as o:
            o.write(adp)
        with open(file_path_decompressed + str(s["resource_id"]) + ".adp.txth", mode="w") as o:
            o.write("codec = PSX\n")
            if s["multi"] == 2048:
                o.write("sample_rate = 22050\n")
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
    
    #with open(file_path_decompressed + "SFX.BBK", mode="wb") as o:
        #o.write(uncompressed_sfx)
     
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
    with open(file_path_decompressed + "MISC.BBK", mode="wb") as o:
        o.write(uncompressed_misc)

if __name__ == "__main__":
    main()