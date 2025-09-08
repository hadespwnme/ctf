# Write-up Tantangan "Stacked" - ImaginaryCTF

## Kategori: Reverse Engineering

### Deskripsi Singkat

Tantangan ini memberikan kita sebuah binary ELF 64-bit bernama `chal.out` dan sebuah string heksadesimal yang "kacau": `94 7 d4 64 7 54 63 24 ad 98 45 72 35`. Nama tantangan "stacked" dan deskripsi yang menyebutkan "Return Oriented Programming" pada awalnya mengarahkan pada eksploitasi berbasis ROP, namun ternyata ini adalah sebuah *red herring* (petunjuk yang menyesatkan). Solusi sebenarnya terletak pada pembalikan (reversing) serangkaian transformasi yang diterapkan pada flag.

### Analisis Awal

1.  **Inspeksi File**:
    Perintah `file chal.out` menunjukkan bahwa ini adalah binary ELF 64-bit yang tidak di-strip, yang berarti nama-nama fungsi kemungkinan besar masih utuh, mempermudah analisis.

2.  **Menjalankan Binary**:
    Setelah memberikan izin eksekusi (`chmod +x chal.out`), menjalankan `./chal.out` menghasilkan string heksadesimal yang berbeda dari yang diberikan di deskripsi tantangan. Ini mengindikasikan bahwa program mengubah data input (atau data yang sudah ada) dan string yang diberikan adalah hasil dari transformasi pada flag yang sebenarnya.

3.  **Disassembly**:
    Menggunakan `objdump -d -M intel chal.out`, kita dapat melihat kode assembly dari program. Analisis pada fungsi `main` menunjukkan serangkaian panjang pemanggilan fungsi-fungsi lain tanpa adanya input dari pengguna.

### Fungsi-fungsi Transformasi

Ada beberapa fungsi kunci yang dipanggil berulang kali di `main`:

*   `_Z3eorh`: Melakukan operasi `XOR` pada sebuah karakter dengan `0x69`.
*   `_Z3rtrh`: Melakukan rotasi bit ke kanan (rotate right) sebanyak 1 bit pada sebuah karakter.
*   `_Z3offh`: Menambahkan `0xf` ke sebuah karakter.
*   `_Z3inch`: Menyimpan karakter yang telah diubah ke dalam sebuah buffer global bernama `flag`.

### Logika Enkripsi

Fungsi `main` pada dasarnya adalah sebuah "unrolled loop" raksasa. Untuk setiap karakter dari flag, program melakukan urutan transformasi yang spesifik dengan memanggil fungsi-fungsi di atas dalam urutan tertentu, dan kemudian menyimpannya kembali.

Setiap karakter dari flag dienkripsi secara independen dengan rantai transformasi yang unik. Tugas kita adalah mencari tahu urutan transformasi untuk setiap karakter dan kemudian membalikkannya.

### Membalikkan Proses Enkripsi

Untuk mendapatkan flag asli, kita perlu membalikkan setiap operasi transformasi:

*   **`_Z3eorh` (XOR)**: Invers dari `XOR` dengan `0x69` adalah `XOR` lagi dengan `0x69`.
*   **`_Z3rtrh` (Rotate Right)**: Invers dari rotasi kanan 1 bit adalah rotasi kiri (left rotate) 1 bit.
*   **`_Z3offh` (Add)**: Invers dari penambahan `0xf` adalah pengurangan `0xf`.

Saya membuat sebuah skrip Python untuk melakukan hal berikut:
1.  Membaca output dari `objdump` untuk mengekstrak urutan pemanggilan fungsi (rantai transformasi) untuk setiap karakter.
2.  Mengimplementasikan fungsi-fungsi invers dari transformasi di atas.
3.  Mengambil string heksadesimal yang diberikan (`94 7 d4 64 7 54 63 24 ad 98 45 72 35`), mengubahnya menjadi array byte.
4.  Untuk setiap byte, terapkan fungsi transformasi invers sesuai dengan urutan yang telah diekstrak, namun **dalam urutan terbalik**.

Berikut adalah kode Python yang digunakan:

```python
import re

def reverse_eorh(c):
    return c ^ 0x69

def reverse_rtrh(c):
    # Invers dari rotasi kanan adalah rotasi kiri
    return ((c << 1) & 0xff) | (c >> 7)

def reverse_offh(c):
    return (c - 0xf) & 0xff

def get_transformations():
    # Fungsi ini mem-parse output objdump untuk mendapatkan rantai transformasi
    with open("chal.out.objdump", "r") as f:
        objdump = f.read()

    main_section = re.search(r"<main>:\n(.*?)\n\n", objdump, re.DOTALL).group(1)
    calls = re.findall(r"call\s+.*<(.*)>", main_section)

    transformations = []
    current_char_transformations = []
    for call in calls:
        if call == "_Z3inch":
            transformations.append(current_char_transformations)
            current_char_transformations = []
        elif call.startswith("_Z"):
            current_char_transformations.append(call)
    return transformations

def reverse_transformations(garbled_hex, transformations):
    garbled_bytes = [int(x, 16) for x in garbled_hex.split()]
    flag = ""
    for i in range(len(garbled_bytes)):
        char_code = garbled_bytes[i]
        # Terapkan transformasi dalam urutan terbalik
        for transform in reversed(transformations[i]):
            if transform == "_Z3eorh":
                char_code = reverse_eorh(char_code)
            elif transform == "_Z3rtrh":
                char_code = reverse_rtrh(char_code)
            elif transform == "_Z3offh":
                char_code = reverse_offh(char_code)
        flag += chr(char_code)
    return flag

# String hex dari tantangan
garbled_hex = "94 7 d4 64 7 54 63 24 ad 98 45 72 35"

# Ekstrak transformasi dan balikkan
transformations = get_transformations()
transformations = transformations[:13] # Hanya 13 byte pertama yang relevan

flag = reverse_transformations(garbled_hex, transformations)
print(flag)
```

### Mendapatkan Flag

Setelah menjalankan skrip di atas, output yang didapat adalah flag dari tantangan ini.

**Flag**: `1n54n3_5k1ll2`

### Kesimpulan

Tantangan "Stacked" adalah contoh klasik dari tantangan reverse engineering di mana petunjuk awal bisa jadi menyesatkan. Kunci untuk menyelesaikannya adalah analisis yang cermat pada alur kerja program dan logika enkripsi yang digunakan, bukan pada eksploitasi memori seperti yang disiratkan oleh nama dan deskripsi tantangan.
