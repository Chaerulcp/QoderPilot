# Kebijakan Keamanan QoderPilot

## Versi yang didukung

Perbaikan keamanan diterapkan pada versi terbaru di branch utama. Pengguna disarankan selalu
memperbarui source dan dependensi sebelum melaporkan masalah yang sudah diperbaiki.

## Melaporkan kerentanan

Jangan membuka issue publik untuk kerentanan yang belum diperbaiki. Gunakan fitur private
security advisory pada platform repository. Jika fitur tersebut tidak tersedia, hubungi
maintainer melalui kanal privat yang dicantumkan pada profil atau metadata repository.

Sertakan informasi berikut:

- komponen dan versi atau commit yang terdampak;
- platform dan versi Python;
- deskripsi dampak;
- langkah reproduksi minimal;
- proof of concept yang sudah menghapus kredensial dan data pribadi;
- mitigasi sementara jika diketahui.

Jangan mengirim password, PAT aktif, OTP, cookie, token sesi, proxy privat, atau isi lengkap
folder `data/`. Gunakan nilai contoh yang tidak aktif.

Maintainer akan berupaya mengonfirmasi laporan, menilai dampak, menyiapkan perbaikan, dan
mengoordinasikan waktu publikasi. Mohon memberikan waktu yang wajar sebelum mengungkapkan
detail secara publik.

## Data sensitif

Project dapat menyimpan email, password, PAT, proxy, log autentikasi, dan hasil client secara
lokal. File tersebut telah diabaikan Git, tetapi pengguna tetap bertanggung jawab atas izin
filesystem, backup, retensi, dan penghapusannya.

Jika kredensial tidak sengaja terpublikasi:

1. cabut atau rotasi kredensial tersebut segera;
2. hapus data dari repository dan riwayat Git bila diperlukan;
3. periksa log akses untuk aktivitas tidak sah;
4. jangan menganggap penghapusan commit saja sudah membatalkan kredensial.

## Ruang lingkup

Laporan mengenai kebocoran kredensial, command injection, penulisan file di luar target,
pengungkapan data sensitif, atau bypass konfirmasi operasi destruktif termasuk dalam ruang
lingkup keamanan project. Masalah pada layanan pihak ketiga harus dilaporkan kepada penyedia
layanan terkait melalui program keamanan mereka.
