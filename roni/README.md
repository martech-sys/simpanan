# #FindingRONI: 10 video klikbait

Brief: file `Perintah` di root repo. Isinya video 15–30 detik, format 9:16, dengan hook di 3 detik pertama, subtitle, tag @ronimakaroni.id, dan hashtag #PilihRONI #RenyahnyaPASTI.

## Isi folder

| File | Isi |
|---|---|
| `konsep.json` | 10 naskah video: hook, 6 beat subtitle (masing-masing 3 detik), dan caption posting |
| `render.py` | Merender semua konsep menjadi MP4 1080×1920, sekitar 20,5 detik per video |
| `footage/` | Footage RONI (`PEDAS GURIH UPI BDG.mp4`) |
| `hasil/` | Output: `RONI-<id>.mp4` + `RONI-<id>.txt` (caption siap tempel) |

## 10 konsep

| # | Hook | Jenis pancingan |
|---|---|---|
| 01 | TIM GURIH KALAH TELAK DI UPI | Skor asli footage: Pedas 12 vs Gurih 6 |
| 02 | TIM GURIH ITU CUMA TAKUT PEDAS | Debat pedas vs gurih |
| 03 | KELAS TANPA RONI = KELAS GAGAL | Klaim provokatif + tag ketua kelas |
| 04 | MAKARONI MELEMPEM HARUSNYA DILARANG | Hot take tekstur crunchy |
| 05 | DICARI: RONI TERAKHIR DI UPI BANDUNG | Parodi poster "dicari" #FindingRONI |
| 06 | KATANYA ANAK UPI GAK KUAT PEDAS? | Bait-and-switch, dibantah skor 12–6 |
| 07 | 3 TIPE ORANG DITAWARIN RONI | Listicle dari momen di footage |
| 08 | UNPOPULAR OPINION: RONI > KOPI BUAT NUGAS | Unpopular opinion |
| 09 | GAK ADA YANG AMBIL CUMA SATU | "Satu lagi cobain" dari footage + tag temen |
| 10 | YANG NAMANYA RONI KAMU DICARIIN | Gimik nama orang + tag temen bernama Roni |

Yang sudah dicek terhadap brief:
- Setiap video menyebut info produk RONI: crunchy/renyah, rasa PEDAS/GURIH, atau slogan.
- Tidak ada brand lain yang disebut.
- Tidak ada keranjang kuning.
- Tidak ada klaim yang mengubah konteks.
- End card memuat slogan dan @ronimakaroni.id.

## Cara render

```bash
pip install imageio-ffmpeg          # ffmpeg ikut terpasang lewat paket ini
# taruh footage RONI (mp4/mov/jpg/png) di roni/footage/
python3 roni/render.py              # render ke-10 video
python3 roni/render.py 02 07        # render konsep tertentu saja
```

Potongan footage untuk tiap beat dipilih otomatis secara bergilir. **Cek hasilnya**, karena brief minta footage yang sesuai konteks. Kalau potongannya kurang pas, tambahkan `"clip": "namafile.mp4", "mulai": 4.5` pada beat tersebut di `konsep.json`, lalu render ulang.

Footage landscape otomatis dibuat 9:16 dengan latar blur. Foto diberi efek zoom pelan. Audio asli footage dipertahankan. Sebelum posting, tambahkan musik trending dari aplikasi (TikTok/IG), karena lagu berlisensi tidak bisa ditempel dari sini.

Jangan lupa aktifkan label konten berbayar / paid partnership di platform saat posting.
