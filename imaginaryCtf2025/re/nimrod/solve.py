#!/usr/bin/env python3

def lcg_next(seed: int) -> int:
    return (seed * 0x19660D + 0x3C6EF35F) & 0xFFFFFFFF


def decrypt_flag_from_binary(path: str, offset: int) -> str:
    with open(path, "rb") as f:
        f.seek(offset)
        header = f.read(8)
        if len(header) != 8:
            raise RuntimeError("Failed to read Nim string header")
        length = int.from_bytes(header[:4], "little")
        # Nim stores 8 bytes header, then `length` bytes of data
        enc = f.read(length)
        if len(enc) != length:
            raise RuntimeError("Failed to read encrypted flag bytes")

    seed = 0x13371337
    out = bytearray()
    for b in enc:
        seed = lcg_next(seed)
        keystream_byte = (seed >> 16) & 0xFF
        out.append(b ^ keystream_byte)

    return out.decode("utf-8")


if __name__ == "__main__":
    flag = decrypt_flag_from_binary("nimrod", 0x116E8)
    print(flag)
