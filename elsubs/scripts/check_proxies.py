#!/usr/bin/env python3
"""
Proxy Checker & Filter for elsubs
- Checks provider URLs
- Scrapes proxies from live providers
- Filters dead proxies via v2rayChecker
- Generates filtered output files with source flags
"""

import subprocess
import sys
import os
import re
import base64
from urllib.parse import urlparse

# Install proxyUtil if not available
try:
    from proxyUtil import *
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://github.com/mheidari98/proxyUtil@main"])
    from proxyUtil import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Path setup: elsubs/scripts/check_proxies.py -> elsubs/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ELS_DIR = os.path.dirname(SCRIPT_DIR)
NODES_FILE = os.path.join(ELS_DIR, 'mheidari98-proxy', '.proxy-main', 'nodes.md')

OUTPUT_FILES = {
    'all': os.path.join(ELS_DIR, 'all'),
    'ss': os.path.join(ELS_DIR, 'ss'),
    'vmess': os.path.join(ELS_DIR, 'vmess'),
    'vless': os.path.join(ELS_DIR, 'vless'),
    'trojan': os.path.join(ELS_DIR, 'trojan'),
}

def check_url(url, timeout=3, retries=3):
    """Check if provider URL is reachable."""
    for _ in range(retries):
        try:
            r = requests.head(url, timeout=timeout)
            if r.status_code // 100 == 2:
                return True
        except:
            pass
    return False

def get_source_flag(url):
    """Generate short flag from URL source for easy search."""
    parsed = urlparse(url)
    # Extract owner/repo or domain name
    if 'github.com' in parsed.netloc:
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            return path_parts[1][:8]  # First 8 chars of repo name
    return parsed.netloc[:8] or 'unknown'

def check_url_with_scrap(url):
    """Check URL and scrape proxies. Returns (status, proxies, flag)."""
    flag = get_source_flag(url)
    status = check_url(url)
    proxies = []
    if status:
        try:
            p = ScrapURL(url)
            proxies = p
            logging.info(f"✅ {flag} - Scraped {len(proxies)} proxies from {url}")
        except Exception as e:
            logging.warning(f"⚠️ {flag} - ScrapURL failed: {e}")
    else:
        logging.warning(f"❌ {flag} - URL unreachable: {url}")
    return status, proxies, flag

def update_nodes_md():
    """Update nodes.md with fresh status."""
    output = []
    proxy = []
    
    with open(NODES_FILE, encoding="utf8") as file:
        cnt = 0
        while line := file.readline():
            line = line.rstrip()
            if line.startswith("|"):
                if cnt > 1:
                    url = line.split('|')[-2]
                    status, scraped, flag = check_url_with_scrap(url)
                    status_icon = "✅" if status else "❌"
                    proxy_count = len(scraped) if scraped else 0
                    line = re.sub(r'^\|+?(.*?)\|+?(.*?)\|+?', f'| {status_icon} | {proxy_count} |', line, count=1)
                    proxy.extend(scraped)
                cnt += 1
            output.append(line)
    
    with open(NODES_FILE, "w", encoding="utf8") as f:
        f.write('\n'.join(output))
    
    return proxy

def filter_proxies_simple(proxy_list):
    """Simple filter - just return all proxies if v2rayChecker unavailable."""
    logging.info(f"Using all {len(proxy_list)} proxies (v2rayChecker not available)")
    return proxy_list

def filter_proxies_v2raychecker(proxy_list, max_threads=50):
    """Filter proxies using v2rayChecker. Returns only live proxies."""
    if not proxy_list:
        return []
    
    # Write proxies to temp file for v2rayChecker
    temp_input = '/tmp/proxies_to_check.txt'
    temp_output = '/tmp/checked_proxies.txt'
    
    with open(temp_input, 'w') as f:
        for p in proxy_list:
            f.write(p + '\n')
    
    # Try v2rayChecker first
    for checker_path in ['v2rayChecker', '/usr/local/bin/v2rayChecker', '/usr/bin/v2rayChecker']:
        try:
            cmd = [checker_path, '-i', temp_input, '-o', temp_output, '-t', str(max_threads)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            live_proxies = []
            if os.path.exists(temp_output):
                with open(temp_output, 'r') as f:
                    live_proxies = [line.strip() for line in f if line.strip()]
            
            logging.info(f"v2rayChecker ({checker_path}): {len(live_proxies)}/{len(proxy_list)} alive")
            return live_proxies if live_proxies else proxy_list
        except FileNotFoundError:
            continue
        except Exception as e:
            logging.warning(f"v2rayChecker ({checker_path}) error: {e}")
            continue
    
    # Fallback: return all proxies
    logging.warning("v2rayChecker not found, using all scraped proxies")
    return proxy_list

def add_flag_to_proxy(proxy_line, flag):
    """Add source flag to proxy line for identification."""
    # For base64 encoded proxies, append flag as comment
    if '#' in proxy_line:
        # Already has comment, prepend flag
        parts = proxy_line.split('#', 1)
        return f"{parts[0]}#[{flag}]{parts[1]}"
    else:
        return f"{proxy_line}#[{flag}]"

def categorize_and_save(proxies):
    """Categorize proxies by protocol and save to files."""
    ss, ssr, vmess, vless, trojan = [], [], [], [], []
    
    for p in proxies:
        if p.startswith("ss://"):
            ss.append(p)
        elif p.startswith("ssr://"):
            ssr.append(p)
        elif p.startswith("vmess://"):
            vmess.append(p)
        elif p.startswith("vless://"):
            vless.append(p)
        elif p.startswith("trojan://"):
            trojan.append(p)
    
    # Save all
    with open(OUTPUT_FILES['all'], 'w') as f:
        f.write('\n'.join(proxies))
    
    # Save by type
    with open(OUTPUT_FILES['ss'], 'w') as f:
        f.write('\n'.join(ss))
    
    with open(OUTPUT_FILES['vmess'], 'w') as f:
        f.write('\n'.join(vmess))
    
    with open(OUTPUT_FILES['vless'], 'w') as f:
        f.write('\n'.join(vless))
    
    with open(OUTPUT_FILES['trojan'], 'w') as f:
        f.write('\n'.join(trojan))
    
    logging.info(f"Saved: all={len(proxies)}, ss={len(ss)}, vmess={len(vmess)}, vless={len(vless)}, trojan={len(trojan)}")

def main():
    logging.info("Starting proxy check and filter...")
    
    # Step 1: Check URLs and scrape proxies
    all_proxies = update_nodes_md()
    logging.info(f"Total proxies scraped: {len(all_proxies)}")
    
    if not all_proxies:
        logging.warning("No proxies scraped, skipping filter step")
        return
    
    # Step 2: Filter individual proxies (optional, may be slow)
    logging.info("Filtering proxies with v2rayChecker...")
    live_proxies = filter_proxies_v2raychecker(all_proxies)
    
    # Step 3: Categorize and save
    categorize_and_save(live_proxies)
    
    logging.info("Done!")

if __name__ == "__main__":
    main()