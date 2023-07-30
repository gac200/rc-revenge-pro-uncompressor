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
    SFX_COMPRESSED_SIZE_OFFSET = 0x14EC
    sfx_offset = SFX_COMPRESSED_SIZE_OFFSET + 4
    sfx_compressed_size = contents[SFX_COMPRESSED_SIZE_OFFSET:SFX_COMPRESSED_SIZE_OFFSET + 4]
    sfx_compressed_size = int.from_bytes(sfx_compressed_size, "little")
    sfx_end = sfx_offset + sfx_compressed_size
    
    uncompressed_sfx = zlib.decompress(contents[sfx_offset:sfx_end])
    
    with open(file_path_decompressed + "SFX.BBK", mode="wb") as o:
        o.write(uncompressed_sfx)
    #Each sfx struct is 32 bytes long, more info to follow...
     
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