### Write-up CTF: comparing

Ini adalah write-up untuk tantangan "comparing" dalam ImaginaryCTF.

#### Deskripsi

Tantangan ini memberi kita sebuah file C++ (`comparing.cpp`) dan output dari program tersebut (`output.txt`). Tugas kita adalah menemukan flag yang disembunyikan di dalam program dengan menganalisis kode dan outputnya.

#### Analisis

**1. Analisis Kode (`comparing.cpp`)**

Kode C++ tersebut melakukan hal-hal berikut:
*   Mendefinisikan sebuah `flag` (yang isinya disembunyikan).
*   Membagi `flag` menjadi pasangan karakter. Setiap pasangan, bersama dengan indeksnya, disimpan dalam sebuah `tuple<char, char, int>`.
*   Semua tuple ini dimasukkan ke dalam `std::priority_queue`.
*   `priority_queue` ini menggunakan komparator khusus (`Compare`) yang mengurutkan tuple berdasarkan jumlah nilai ASCII dari dua karakter pertamanya. Secara teori, `operator>()` pada komparator akan menjadikan `priority_queue` sebuah *max-heap* (elemen dengan jumlah terbesar akan keluar lebih dulu).
*   Program kemudian mengambil dua tuple dari `priority_queue` secara berulang, dan berdasarkan indeks ganjil atau genap dari tuple tersebut, program memanggil fungsi `even()` atau `odd()`.
*   Fungsi `even()` dan `odd()` menghasilkan string berdasarkan nilai ASCII dari karakter-karakter dalam tuple dan indeksnya. String-string inilah yang dicetak ke `output.txt`.

**2. Analisis Output (`output.txt`)**

File `output.txt` berisi 16 baris string. Karena setiap iterasi dari loop utama menghasilkan dua baris output, ini berarti loop berjalan 8 kali, dan ada total 16 tuple di dalam `priority_queue`. Ini mengkonfirmasi bahwa panjang flag adalah 32 karakter.

Kita dapat membedakan output dari fungsi `even()` dan `odd()`:
*   `odd(val1, val3, ii)` hanya menggabungkan angka-angka menjadi satu bilangan bulat.
*   `even(val1, val3, ii)` menghasilkan string yang memiliki bagian palindromik di akhir. Contoh: `even(95, 48, 12)` menghasilkan `9548128459`, di mana `8459` adalah kebalikan dari `9548`.

#### Langkah-langkah Penyelesaian

Kunci untuk menyelesaikan tantangan ini adalah dengan merekayasa balik (reverse engineering) logika program.

1.  **Membongkar Output:** Langkah pertama adalah mem-parsing setiap baris di `output.txt` untuk mengidentifikasi apakah itu hasil dari `even()` atau `odd()`, dan mengekstrak tiga argumennya (`val1`, `val3`, dan `index`).

2.  **Menemukan Kontradiksi:** Saat mencoba merekonstruksi tuple pertama yang keluar dari `priority_queue`, saya menemukan sebuah kontradiksi. Berdasarkan output, tuple yang seharusnya memiliki jumlah ASCII *lebih kecil* justru keluar lebih dulu. Ini bertentangan dengan implementasi `Compare` yang seharusnya menjadikan `priority_queue` sebuah *max-heap*.

3.  **Solusi:** Kontradiksi ini adalah petunjuk utama. Kemungkinan besar, kode sumber sengaja dibuat menyesatkan. Dengan asumsi bahwa `priority_queue` sebenarnya berperilaku sebagai *min-heap* (elemen dengan jumlah terkecil keluar lebih dulu), semua logika menjadi konsisten.

4.  **Rekonstruksi Tuple:** Dengan asumsi *min-heap*, saya dapat merekonstruksi semua 16 tuple yang asli. Setiap pasang baris output memberikan informasi untuk merekonstruksi dua tuple.

    Sebagai contoh, dua baris pertama adalah `9548128459` dan `491095`.
    *   `even(95, 48, 12)`
    *   `odd(49, 109, 5)`

    Ini menghasilkan dua tuple: `(95, 49, 12)` dengan jumlah 144, dan `(48, 109, 5)` dengan jumlah 157. Karena kita mengasumsikan *min-heap*, tuple dengan jumlah 144 keluar lebih dulu. Ini cocok dengan output yang diobservasi.

    Dengan menerapkan logika ini ke semua baris output, kita mendapatkan 16 tuple berikut:
    *   `[0]: ('i', 'c')`
    *   `[1]: ('t', 'f')`
    *   `[2]: ('{', 'c')`
    *   `[3]: ('u', '3')`
    *   `[4]: ('s', 't')`
    *   `[5]: ('0', 'm')`
    *   `[6]: ('_', 'c')`
    *   `[7]: ('0', 'm')`
    *   `[8]: ('p', '@')`
    *   `[9]: ('r', '@')`
    *   `[10]: ('t', '0')`
    *   `[11]: ('r', 's')`
    *   `[12]: ('_', '1')`
    *   `[13]: ('e', '8')`
    *   `[14]: ('f', '9')`
    *   `[15]: ('e', '}')`

#### Rekonstruksi Flag

Langkah terakhir adalah menyusun kembali flag. Program aslinya memecah flag menjadi pasangan karakter `flag[i*2]` dan `flag[i*2+1]`, yang sesuai dengan tuple di indeks `i`. Dengan mengurutkan tuple yang telah kita rekonstruksi berdasarkan indeksnya (0 hingga 15) dan menggabungkan kembali pasangan karakternya, kita mendapatkan flag-nya.

`ictf` + `{c` + `u3` + `st` + `0m` + `_c` + `0m` + `p@` + `r@` + `t0` + `rs` + `_1` + `e8` + `f9` + `e}`

#### Flag

'''
ictf{cu3st0m_c0mp@r@t0rs_1e8f9e}
'''
