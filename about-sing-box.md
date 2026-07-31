# Install sing-box + Test Proxy via CLI (URL Test tanpa UI)

Pendekatan yang benar secara teknis: sing-box tidak punya command tunggal `sing-box test <link>`, tapi punya **Clash API** (`experimental.clash_api`) yang expose endpoint `/proxies/{tag}/delay` — ini persis mekanisme "URL Test" yang dipakai dashboard Clash/NekoBox, tapi bisa dipanggil murni via `curl`. Jadi alurnya: install → buat config berisi proxy + urltest outbound + clash_api → jalankan sing-box → query delay via curl.

## 1. Install sing-box

```bash
# Install via script resmi SagerNet (auto-detect arch, install ke /usr/local/bin atau via apt repo)
bash <(curl -fsSL https://sing-box.app/install.sh)

# Cek versi
sing-box version
```

Alternatif manual (kalau mau pin versi tertentu / tanpa systemd service):

```bash
ARCH=$(dpkg --print-architecture)  # amd64 / arm64
VER=$(curl -s https://api.github.com/repos/SagerNet/sing-box/releases/latest | grep tag_name | cut -d '"' -f4 | sed 's/v//')

curl -LO "https://github.com/SagerNet/sing-box/releases/download/v${VER}/sing-box-${VER}-linux-${ARCH}.tar.gz"
tar -xzf sing-box-${VER}-linux-${ARCH}.tar.gz
sudo install -m 755 sing-box-${VER}-linux-${ARCH}/sing-box /usr/local/bin/sing-box
sing-box version
```

## 2. Buat config test (`urltest.json`)

Ganti bagian outbound sesuai proxy yang mau dicek (contoh menyertakan keempat protokol: vmess, vless, trojan, shadowsocks). Kunci pentingnya ada di `experimental.clash_api` (buka port controller lokal) dan outbound `urltest` yang membungkus semua proxy.

```bash
cat > urltest.json << 'EOF'
{
  "log": { "level": "info", "timestamp": true },
  "experimental": {
    "clash_api": {
      "external_controller": "127.0.0.1:9090",
      "default_mode": "rule"
    }
  },
  "outbounds": [
    {
      "type": "vmess",
      "tag": "proxy-vmess",
      "server": "SERVER_VMESS",
      "server_port": 443,
      "uuid": "UUID_DISINI",
      "security": "auto",
      "tls": { "enabled": true, "server_name": "SERVER_VMESS" }
    },
    {
      "type": "vless",
      "tag": "proxy-vless",
      "server": "SERVER_VLESS",
      "server_port": 443,
      "uuid": "UUID_DISINI",
      "tls": { "enabled": true, "server_name": "SERVER_VLESS" }
    },
    {
      "type": "trojan",
      "tag": "proxy-trojan",
      "server": "SERVER_TROJAN",
      "server_port": 443,
      "password": "PASSWORD_DISINI",
      "tls": { "enabled": true, "server_name": "SERVER_TROJAN" }
    },
    {
      "type": "shadowsocks",
      "tag": "proxy-ss",
      "server": "SERVER_SS",
      "server_port": 8388,
      "method": "aes-256-gcm",
      "password": "PASSWORD_DISINI"
    },
    {
      "type": "urltest",
      "tag": "auto-test",
      "outbounds": ["proxy-vmess", "proxy-vless", "proxy-trojan", "proxy-ss"],
      "url": "https://www.gstatic.com/generate_204",
      "interval": "1m",
      "tolerance": 50
    },
    { "type": "direct", "tag": "direct" }
  ],
  "route": {
    "final": "auto-test"
  }
}
EOF
```

Validasi syntax config sebelum jalan (ini fungsi `check` bawaan sing-box):

```bash
sing-box check -c urltest.json
```

## 3. Jalankan sing-box (background)

```bash
nohup sing-box run -c urltest.json > sing-box.log 2>&1 &
sleep 2   # kasih waktu init clash_api
```

## 4. Cek reachability tiap proxy via CLI (curl ke Clash API)

Ini bagian intinya — query delay per-tag, tanpa UI apa pun:

```bash
for tag in proxy-vmess proxy-vless proxy-trojan proxy-ss; do
  echo "== $tag =="
  curl -s "http://127.0.0.1:9090/proxies/${tag}/delay?url=https://www.gstatic.com/generate_204&timeout=5000"
  echo
done
```

**Cara baca hasilnya:**

| Response | Arti |
|---|---|
| `{"delay":123}` | Reachable, latency 123ms |
| `{"message":"context deadline exceeded"}` atau error connection | Tidak reachable / timeout |
| HTTP 404 dari curl | Tag salah / proxy belum ke-load, cek `sing-box.log` |

Untuk lihat proxy mana yang otomatis dipilih sing-box sebagai tercepat (dari grup `urltest`):

```bash
curl -s http://127.0.0.1:9090/proxies/auto-test | python3 -m json.tool
```

## 5. Bersihkan setelah selesai test

```bash
pkill -f "sing-box run -c urltest.json"
```

---

**Catatan:**
- `generate_204` (Google) dipakai karena ringan dan return cepat; kalau server target Google diblokir di jaringanmu, ganti `url` ke endpoint lain (mis. `https://cp.cloudflare.com`).
- Kalau mau one-shot tanpa `interval` auto-refresh, tetap pakai config ini — endpoint `/delay` trigger test on-demand terlepas dari interval background.
- Untuk integrasi ke installer/script otomatis di homelab kamu, bagian for-loop di atas bisa langsung dijadikan fungsi bash yang return exit code (0 = reachable, 1 = tidak) — kalau mau saya bantu susun jadi script lengkap dengan parsing JSON pakai `jq`, tinggal bilang.