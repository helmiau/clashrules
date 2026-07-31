# elsubs - Proxy Subscription Files

This repository contains auto-generated proxy subscription files updated daily via GitHub Actions. These files only include **active (alive) proxy servers** after filtering.

## 📁 Output File Structure

| File | Description | Format |
|------|-------------|--------|
| `all` | All protocols (SS, VMess, VLESS, Trojan) | Plain text (one link per line) |
| `ss` | Shadowsocks only | `ss://...` |
| `vmess` | VMess only | `vmess://...` |
| `vless` | VLESS only | `vless://...` |
| `trojan` | Trojan only | `trojan://...` |

Each server includes a **flag ID** (e.g., `#[abc12345]`) for easy provider source identification.

## 🔄 Automatic Updates

- **Schedule**: Daily at 00:00 UTC
- **Manual**: Trigger via GitHub Actions → "Proxy Generator" → "Run workflow"
- **Process**: 
  1. Clone provider list from `mheidari98-proxy`
  2. Scrape all proxy links from 20+ providers
  3. Test connectivity via sing-box Clash API (20 concurrent workers)
  4. Save only alive servers to output files
  5. Auto-commit & push

## 📱 Supported Apps

### Full App List (VLESS, Trojan, Shadowsocks Cloudflare)

| App | Platform | Download |
|-----|----------|----------|
| **V2rayNG** ⭐ | Android | [GitHub Releases](https://github.com/2dust/v2rayNG/releases) |
| **V2flyNG** | Android | [GitHub Releases](https://github.com/2dust/v2flyNG/releases) |
| **GatchaNG** (Recommended for Shadowsocks) | Android | [GitHub Releases](https://github.com/djoeni/pitureienge/releases) |
| **XrayPB** | Android | [Play Store](https://play.google.com/store/apps/details?id=com.sihiver.xraypb) |
| **Http Custom** | Android | [Play Store](https://play.google.com/store/apps/details?id=xyz.easypro.httpcustom) |
| **Http Injector** | Android | [Play Store](https://play.google.com/store/apps/details?id=com.evozi.injector) |
| **Npv Tunnel 104** | Android | [APKPure](https://m.apkpure.com/npv-tunnel-v2ray-ssh/com.napsternetlabs.napsternetv/download/104.0) |
| **Kentang Clash** | Android | [v7a](https://github.com/bitzblack/Kentang-Clash/raw/refs/heads/main/KENTANG-CLASH-2.5.0-armeabi-v7a-release%20(3).apk) / [v8a](https://github.com/bitzblack/Kentang-Clash/raw/refs/heads/main/KENTANG-CLASH-2.5.0-arm64-v8a-release.apk) |
| **Hiddify** ⭐ | Android/Windows/macOS/Linux | [GitHub Releases](https://github.com/hiddify/hiddify-next/releases) |
| **FiClash** ⭐ | Android/Windows/macOS/Linux | [GitHub Releases](https://github.com/chen08209/FlClash/releases) |
| **Clash Meta for Android (CMFA)** ⭐ | Android | [GitHub Releases](https://github.com/MetaCubeX/ClashMetaForAndroid/releases) |
| **Karing** ⭐ | Android/iOS/macOS/Windows | [GitHub Releases](https://github.com/KaringX/karing/releases) |
| **Surfboard** | iOS | [GitHub Releases](https://github.com/getsurfboard/surfboard/releases) |
| **Nekobox** ⭐ | Android/iOS/macOS/Windows | [GitHub Releases](https://github.com/MatsuriDayo/NekoBoxForAndroid/releases) |
| **Exclave** | Android | [GitHub Releases](https://github.com/dyhkwong/Exclave/releases) |
| **Husi** | Android | [GitHub Releases](https://github.com/xchacha20-poly1305/husi/releases) |
| **Singbox** ⭐ | Android/iOS/macOS/Windows/Linux | [GitHub Releases](https://github.com/SagerNet/sing-box/releases) |
| **Dark Tunnel** | Android | [Play Store](https://play.google.com/store/apps/details?id=net.darktunnel.app) |
| **LxBox** | Android | [GitHub Releases](https://github.com/Leadaxe/LxBox/releases) |

> 💡 **Hint**: ⭐ = Recommended (Android): [ClashMetaForAndroid](https://github.com/MetaCubeX/ClashMetaForAndroid/releases) · [FlClash](https://github.com/chen08209/FlClash/releases) `(clash-verge/1.6.6)` · [NekoBox](https://github.com/MatsuriDayo/NekoBoxForAndroid) · [sing-box](https://github.com/SagerNet/sing-box/releases) · [Hiddify-Next](https://github.com/hiddify/hiddify-next/releases) · [v2rayNG](https://github.com/2dust/v2rayNG/releases) · [Karing](https://github.com/KaringX/karing/releases/)

## 🚀 How to Use

### Raw GitHub URLs
```
https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/all
https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/ss
https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/vmess
https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/vless
https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/trojan
```

### Import into App
1. Open your preferred app (e.g. v2rayNG, ClashMetaForAndroid)
2. Choose "Import from URL"
3. Paste the raw URL for the desired protocol
4. Update / Refresh profile

### Example for Clash Meta / sing-box (Profile YAML)
```yaml
proxies:
  - name: "elsubs-all"
    type: http
    url: "https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/all"
    interval: 86400  # daily update
```

## ⚙️ Technical Details

- **Tester**: sing-box v1.13+ with Clash API (`external_controller: 127.0.0.1:9090`)
- **Test URL**: `https://www.gstatic.com/generate_204`
- **Timeout**: 8 seconds per proxy
- **Concurrency**: 20 parallel workers
- **Providers**: 20+ sources from `mheidari98-proxy` (`nodes.md`)

## 📝 Notes

- `all` mixes all protocols — best for multi-protocol apps
- Per-protocol files (`ss`, `vmess`, `vless`, `trojan`) for apps that need a specific format
- Dead servers are removed from output files and from provider `nodes.md`
- Flag IDs (`#[xxxxxxxx]`) help track each server's provider source

## 📲 QR Code Import

Click each button to reveal the QR code, then scan with your app to import.

<details>
<summary><b>QR Code — All Protocols</b></summary>
<br>

![QR: all](https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/all)

</details>

<details>
<summary><b>QR Code — Shadowsocks (ss)</b></summary>
<br>

![QR: ss](https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/ss)

</details>

<details>
<summary><b>QR Code — VMess</b></summary>
<br>

![QR: vmess](https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/vmess)

</details>

<details>
<summary><b>QR Code — VLESS</b></summary>
<br>

![QR: vless](https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/vless)

</details>

<details>
<summary><b>QR Code — Trojan</b></summary>
<br>

![QR: trojan](https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://raw.githubusercontent.com/helmiau/clashrules/main/elsubs/trojan)

</details>

---

**Generated by**: [GitHub Actions Proxy Generator](https://github.com/helmiau/clashrules/actions/workflows/proxy-generator.yml)  
**Last Updated**: Automatically daily at 00:00 UTC