imaginaryCTF – Web: Codenames‑1 (Write‑up)
================================================

Ringkasan
----------------------------------------
- Bug: Path traversal via parameter `language` pada endpoint `POST /create_game`.
- Akibat: Aplikasi dapat membaca file arbitrer di filesystem container. Membaca `/flag.txt` menampilkan flag sebagai kata di papan permainan.
- Flag: `ictf{common_os_path_join_L_b19d35ca}`

Akar Masalah
----------------------------------------
Cuplikan kode (disederhanakan) dari `challenge/app.py`:

```
language = request.form.get('language', None)
if not language or '.' in language:
    language = LANGUAGES[0] if LANGUAGES else None
# ...
wl_path = os.path.join(WORDS_DIR, f"{language}.txt")
with open(wl_path) as wf:
    word_list = [line.strip() for line in wf if line.strip()]
```

- Validasi hanya memblokir karakter `.`.
- Pada Python, `os.path.join('words', '/flag.txt')` mengabaikan prefiks `words` jika argumen kedua adalah path absolut, sehingga menjadi `/flag.txt`.
- Memberi `language=/flag` melewati cek (tidak ada titik), sehingga server membuka file absolut `/flag.txt`.

Eksploitasi Manual (Browser)
----------------------------------------
1. Login/registrasi dua akun (dua sesi, mis. normal + incognito).
2. Pada sesi pertama (Lobby), buat game dengan mengirimkan `language=/flag`:
   - Buka DevTools Console dan jalankan:
     ```
     fetch('/create_game', {
       method: 'POST',
       headers: {'Content-Type': 'application/x-www-form-urlencoded'},
       body: 'language=/flag'
     }).then(r => (location = r.url));
     ```
3. Catat kode game (6 karakter) dari URL yang terbuka.
4. Pada sesi kedua, `Join Game` dengan kode tersebut.
5. Saat kedua klien tersambung, event `start_game` terkirim dan papan tampil; kata yang diulang adalah isi `/flag.txt` → flag.

Eksploitasi Otomatis (Script)
----------------------------------------
- File: `solve_codenames1.py`
- Dependensi: `pip install requests python-socketio websocket-client`
- Jalankan:
  ```
  python3 solve_codenames1.py http://codenames-1.chal.imaginaryctf.org
  ```
- Alur:
  - Register 2 user acak
  - `POST /create_game` dengan `language=/flag`
  - User B `POST /join_game` dengan kode game
  - Dua klien Socket.IO terkoneksi (polling/websocket), menunggu `start_game`
  - Ambil `board` dan cetak flag

Contoh output berhasil:
```
[*] Board sample: ['ictf{common_os_path_join_L_b19d35ca}', ...]
[+] Flag: ictf{common_os_path_join_L_b19d35ca}
```

Perbaikan/Mitigasi
----------------------------------------
- Whitelist: Abaikan input klien dan pilih `language` hanya dari daftar server-side `LANGUAGES`.
- Validasi ketat: Tolak path absolut (`os.path.isabs`), path separator (`/` dan `\`), dan gunakan regex seperti `^[a-z0-9_-]+$`.
- Bangun path aman: `wl = Path(WORDS_DIR) / f"{language}.txt"`; verifikasi `wl.resolve().is_relative_to(Path(WORDS_DIR).resolve())` sebelum membuka.

Catatan Tambahan (Codenames‑2)
----------------------------------------
Pada instance Codenames‑2, ada jalur kebocoran `FLAG_2` via bot + hard mode saat menang. Tantangan ini (codenames‑1) tidak memerlukan bot; cukup path traversal pada pemilihan bahasa.

