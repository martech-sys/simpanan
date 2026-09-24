# Titik aman: branch `stable-2026-09-24`

Dicatat: 24 September 2026

Branch `stable-2026-09-24` sudah dibuat di GitHub dan menunjuk ke commit `8cac2e0`, yaitu versi yang sedang tayang di produksi saat catatan ini dibuat.

## Kenapa branch, bukan tag

Saya coba buat tag dulu, tapi push-nya ditolak 4 kali dengan pesan `the remote end hung up unexpectedly`. Proxy-nya sehat, jadi penyebabnya adalah kredensial git di session itu: boleh push ke `refs/heads/*`, tapi tidak ke `refs/tags/*`.

Untuk keperluan ini branch justru lebih cocok, karena branch bisa langsung dipakai untuk deploy dan tag tidak.

> Tag lokal `stable-2026-09-24` hanya ada di container session itu, tidak ada di GitHub, dan hilang saat container ditutup. Jangan andalkan tag itu; yang ada di GitHub adalah **branch**-nya.

## Isi versi ini

- Filter Source (Online / Offline / Semua)
- Tab Ladyfit yang datanya diambil dari Google Sheet
- Tooltip saat hover di chart Ladyfit
- Session login 3 jam
- Tabel `stock_sum_new` dan `laporan_penjualan`
- Pembanding di chart dan KPI masih dihitung otomatis (MoM + YoY)

## Cara kembali ke versi ini kalau fitur baru bermasalah

### 1. Paling cepat, tanpa git: Vercel Instant Rollback

Vercel → project → **Deployments** → cari deployment dari **run #84** → **Instant Rollback** / **Promote to Production**.

Selesai dalam hitungan detik dan tidak perlu query ulang ke database.

### 2. Lewat pipeline: workflow `export-data.yml`

Jalankan workflow `export-data.yml` dengan ref `stable-2026-09-24`. Workflow ini menarik data terbaru lalu men-deploy versi lama.

Butuh sekitar 20 menit karena query `stock_sum_new` lambat.
