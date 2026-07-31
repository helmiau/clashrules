# Proxy Checker Scripts

## Overview
Automated proxy checking and filtering for the `mheidari98-proxy` provider list.

## Workflow
GitHub Actions runs daily at 00:00 UTC to:
1. Check provider URLs in `nodes.md`
2. Scrape proxies from live providers
3. Filter dead proxies via v2rayChecker
4. Save filtered proxies to `all`, `ss`, `vmess`, `vless`, `trojan`

## Files
- `check_proxies.py` - Main script for proxy checking and filtering
- `requirements.txt` - Python dependencies

## Setup
Dependencies are installed via GitHub Actions workflow. For local testing:
```bash
pip install -r requirements.txt
pip install git+https://github.com/mheidari98/proxyUtil@main
```

## Provider Flag System
Each proxy is tagged with source flag for easy identification:
- Format: `proxy_url#[flag]`
- Example: `ss://...#[v2rayfree]`
- Flag = first 8 chars of repository name or domain

## Notes
- v2rayChecker integration is optional (falls back to all proxies if not found)
- TAG rotation is preserved from original `main.py` for provider diversity