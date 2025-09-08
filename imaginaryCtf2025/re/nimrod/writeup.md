# Nimrod — Inti Solusi

- Tujuan: ambil flag dari binary Nim `nimrod`.
- Inti: bandingkan input yang dienkripsi XOR-LCG dengan ciphertext di binary; lakukan dekripsi balik untuk memperoleh flag.

Langkah singkat:
- Ciphertext: Nim string pada offset `0x116E8` (format: 8 byte header [len, cap/rc] + `len` byte data). Panjang (`len`) di sini adalah 34.
- Keystream (LCG):
  - `seed0 = 0x13371337`
  - per byte: `seed = (seed*0x19660D + 0x3C6EF35F) & 0xFFFFFFFF`
  - `ks = (seed >> 16) & 0xFF`
  - Dekripsi: `plain[i] = cipher[i] ^ ks`

Skrip solusi (ringkas):
```python
def lcg_next(s):
    return (s*0x19660D + 0x3C6EF35F) & 0xFFFFFFFF

with open('nimrod','rb') as f:
    f.seek(0x116E8)
    length = int.from_bytes(f.read(4),'little')
    f.read(4)  # header sisa
    enc = f.read(length)

s = 0x13371337
pt = bytes((b ^ ((s:=lcg_next(s))>>16 & 0xFF)) for b in enc)
print(pt.decode())
```

Hasil:
- Flag: `ictf{a_mighty_hunter_bfc16cce9dc8}`
- Verifikasi: `printf "%s\n" "ictf{a_mighty_hunter_bfc16cce9dc8}" | ./nimrod` → “Correct!”.
