### Index Shadowrocket Wiki
  - [Contoh config yang didukung oleh Shadowrocket.conf](#wiki-config-fileconf-pada-shadowrocket-ios)
  - [Config Adblock via Shadowrocket](#adblock-via-shadowrocket)

### Wiki Config file.conf pada Shadowrocket iOS

Dokumen ini berisi beberapa contoh penulisan file.conf yang terdapat pada bagian **Shadowrocket - Config - Local Files - default.conf**.

Rule koneksi bawaan:
```
PROXY 
DIRECT 
REJECT
```

- Contoh isi **`file.list`**
```
DOMAIN-KEYWORD,112wan
DOMAIN-SUFFIX,112wan
URL-REGEX,^https?:\/\/\w+\.cloudfront\.net\/banner
IP-CIDR,0.0.0.1/32,no-resolve
USER-AGENT,cloudd*,DIRECT 
```

- Contoh penulisan barisan rule provider/set dari file yang sudah ada di hosting GitHub terletak dibawah barisan **``[Rule]``**
```
[Rule]
# Advertising
RULE-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising.list,REJECT
DOMAIN-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Advertising/Advertising_Domain.list,REJECT

# Global
RULE-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/release/rule/Loon/Proxy/Proxy.list,PROXY
DOMAIN-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/Proxy/Proxy_Domain.list,PROXY

# China 中国直连
RULE-SET,https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Loon/China/China.list,DIRECT
```

- Penulisan baris akhir barisan **``[Rule]``**
```
GEOIP,CN,DIRECT
FINAL,PROXY
```

- Contoh penulisan barisan **``[Host]``**
```
[Host]
*testflight.apple.com = server:8.8.4.4
*.qq.com = server:119.28.28.28
*.tencent.com = server:119.28.28.28
*.weixin.com = server:119.28.28.28
*.bilibili.com = server:119.29.29.29
hdslb.com = server:119.29.29.29
*.163.com = server:119.29.29.29
*.126.com = server:119.29.29.29
*.126.net = server:119.29.29.29
*.127.net = server:119.29.29.29
*.netease.com = server:119.29.29.29
*.mi.com = server:119.29.29.29
*.xiaomi.com = server:119.29.29.29
*.pcbeta.com = 120.52.19.113
mtalk.google.com = 108.177.125.188
dl.google.com = server:119.29.29.29
dl.l.google.com = server:119.29.29.29
```

- Contoh penulisan barisan **``[URL Rewrite]``**
```
[URL Rewrite]
# Redirect Google Search Service
^https?:\/\/(www.)?(g|google)\.cn https://www.google.com 302

# Redirect Google Maps Service
^https?:\/\/(ditu|maps).google\.cn https://maps.google.com 302

# Redirect HTTP to HTTPS
^https?:\/\/(www.)?taobao\.com\/ https://taobao.com/ 302
^https?:\/\/(www.)?jd\.com\/ https://www.jd.com/ 302
^https?:\/\/(www.)?mi\.com\/ https://www.mi.com/ 302
^https?:\/\/you\.163\.com\/ https://you.163.com/ 302
^https?:\/\/(www.)?suning\.com\/ https://suning.com/ 302
^https?:\/\/(www.)?yhd\.com\/ https://yhd.com/ 302
```

### AdBlock via Shadowrocket
Cara import:
  1. Buka **``Shadowrocket``**.
  2. Pilih tab **``Config``** dibawah (yang gambar folder).
  3. Lihat **``Remote Files``**
  4. Tekan **``Add Configuration``**
  5. Masukkan URL ini:
      ``https://github.com/helmiau/clashrules/raw/main/shadowrocket/adsbagong.conf``
  6. Lalu tekan tombol **``Download``**
  7. Lalu lihat bagian **``Local Files``**, tekan tulisan **``adsbagong.conf``**, lalu pilih **``Use Config``**.
  8. Kembali ke halaman awal Shadowrocket, yaitu tab **``Home``**.
  9. Pilih **``Global Routing``** ke **``Config``**
  10. Lalu aktifkan Shadowrocketnya dengan menekan tombol On/Off disebelah tulisan **Not Connected** di halaman awal Shadowrocket.

Tambahan untuk mengubah koneksi langsung dengan VPN di **``Local Servers``** pada halaman **``Home``** Shadowrocket.
  - Jika ingin menggunakan koneksi VPN, silahkan ikuti langkah berikut
      1. Pergi ke tab **``Config``** - **``Local Files``**
      2. Tekan ikon **``(i)``** disebelah kanan tulisan **``adsbagong.conf``**.
      3. Pilih **``Replace Policy``**.
      4. Tekan ikon **``(i)``** disebelah kolom **``Find``**, lalu cari **``DIRECT``**.
      5. Setelah itu, Tekan ikon **``(i)``** disebelah kolom **``Replace``**, lalu cari **``LOCAL SERVERS``**.
      6. Tekan **``DONE``**, lalu tunggu beberapa saat.
      7. Config selesai diubah.
  - Jika ingin kembali menggunakan koneksi langsung alias tanpa VPN, silahkan ikuti langkah berikut:
      1. Ikuti langkah diatas sampai selesai.
      2. Hanya saja, ubah kolom **``Find``** (pada pilihan **``Replace Policy``**) ke **``LOCAL SERVERS``**.
      3. Lalu ubah kolom **``Replace``** ke **``DIRECT``**.
      4. Selesai.
  
