#!/usr/bin/env python3
"""
Proxy tester using sing-box Clash API.
- Start sing-box once with all proxies in urltest group
- Query delay per proxy via /proxies/{tag}/delay endpoint
- Much faster than spawning sing-box per proxy
"""

import json
import logging
import os
import subprocess
import tempfile
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SINGBOX = os.environ.get("SINGBOX_BIN", "sing-box")
TEST_URL = os.environ.get("PROXY_TEST_URL", "https://www.gstatic.com/generate_204")
TEST_TIMEOUT = int(os.environ.get("PROXY_TEST_TIMEOUT", "8000"))  # ms
MAX_WORKERS = int(os.environ.get("PROXY_TEST_WORKERS", "20"))
CLASH_API_PORT = int(os.environ.get("CLASH_API_PORT", "9090"))


def share_to_outbound(link: str) -> dict[str, Any] | None:
    """Convert ss/vmess/vless/trojan share link to sing-box outbound."""
    link = link.strip()
    if not link or link.startswith("#"):
        return None
    try:
        if link.startswith("ss://"):
            return _ss_to_outbound(link)
        if link.startswith("vmess://"):
            return _vmess_to_outbound(link)
        if link.startswith("vless://"):
            return _vless_to_outbound(link)
        if link.startswith("trojan://"):
            return _trojan_to_outbound(link)
    except Exception as e:
        logging.debug("parse fail %s: %s", link[:40], e)
    return None


def _b64decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _ss_to_outbound(link: str) -> dict[str, Any] | None:
    raw = link[5:]
    if "#" in raw:
        raw = raw.split("#", 1)[0]
    method = password = host = None
    port = 0
    if "@" in raw:
        userinfo, server = raw.rsplit("@", 1)
        try:
            userinfo = _b64decode(userinfo).decode()
        except Exception:
            userinfo = urllib.parse.unquote(userinfo)
        if ":" not in userinfo or ":" not in server:
            return None
        method, password = userinfo.split(":", 1)
        host, port_s = server.rsplit(":", 1)
        port = int(port_s)
    else:
        decoded = _b64decode(raw).decode()
        if "@" not in decoded:
            return None
        userinfo, server = decoded.rsplit("@", 1)
        method, password = userinfo.split(":", 1)
        host, port_s = server.rsplit(":", 1)
        port = int(port_s)
    if not all([method, password, host, port]):
        return None
    return {
        "type": "shadowsocks",
        "tag": "proxy",
        "server": host,
        "server_port": port,
        "method": method,
        "password": password,
    }


def _vmess_to_outbound(link: str) -> dict[str, Any] | None:
    raw = link[8:]
    if "#" in raw:
        raw = raw.split("#", 1)[0]
    conf = json.loads(_b64decode(raw).decode())
    host = conf.get("add") or conf.get("host")
    port = int(conf.get("port", 0))
    uuid = conf.get("id")
    if not host or not port or not uuid:
        return None
    network = conf.get("net") or conf.get("network") or "tcp"
    tls_enabled = str(conf.get("tls", "")).lower() in ("tls", "true", "1")
    outbound: dict[str, Any] = {
        "type": "vmess",
        "tag": "proxy",
        "server": host,
        "server_port": port,
        "uuid": uuid,
        "security": conf.get("scy") or conf.get("security") or "auto",
        "alter_id": int(conf.get("aid", 0)),
    }
    if network == "ws":
        outbound["transport"] = {
            "type": "ws",
            "path": conf.get("path") or "/",
            "headers": {"Host": conf.get("host") or host},
        }
    elif network == "grpc":
        outbound["transport"] = {
            "type": "grpc",
            "service_name": conf.get("path") or conf.get("serviceName") or "",
        }
    if tls_enabled:
        outbound["tls"] = {
            "enabled": True,
            "server_name": conf.get("sni") or conf.get("host") or host,
            "insecure": True,
        }
    return outbound


def _vless_to_outbound(link: str) -> dict[str, Any] | None:
    u = urllib.parse.urlparse(link)
    if not u.hostname or not u.port or not u.username:
        return None
    q = dict(urllib.parse.parse_qsl(u.query))
    outbound: dict[str, Any] = {
        "type": "vless",
        "tag": "proxy",
        "server": u.hostname,
        "server_port": u.port,
        "uuid": urllib.parse.unquote(u.username),
    }
    flow = q.get("flow")
    if flow:
        outbound["flow"] = flow
    network = q.get("type") or q.get("network") or "tcp"
    if network == "ws":
        outbound["transport"] = {
            "type": "ws",
            "path": q.get("path") or "/",
            "headers": {"Host": q.get("host") or u.hostname},
        }
    elif network == "grpc":
        outbound["transport"] = {
            "type": "grpc",
            "service_name": q.get("serviceName") or q.get("path") or "",
        }
    security = q.get("security") or ""
    if security in ("tls", "reality"):
        tls: dict[str, Any] = {
            "enabled": True,
            "server_name": q.get("sni") or u.hostname,
            "insecure": True,
        }
        if security == "reality":
            tls["reality"] = {
                "enabled": True,
                "public_key": q.get("pbk") or "",
                "short_id": q.get("sid") or "",
            }
            tls["utls"] = {"enabled": True, "fingerprint": q.get("fp") or "chrome"}
        outbound["tls"] = tls
    return outbound


def _trojan_to_outbound(link: str) -> dict[str, Any] | None:
    u = urllib.parse.urlparse(link)
    if not u.hostname or not u.port or not u.username:
        return None
    q = dict(urllib.parse.parse_qsl(u.query))
    outbound: dict[str, Any] = {
        "type": "trojan",
        "tag": "proxy",
        "server": u.hostname,
        "server_port": u.port,
        "password": urllib.parse.unquote(u.username),
        "tls": {
            "enabled": True,
            "server_name": q.get("sni") or u.hostname,
            "insecure": True,
        },
    }
    network = q.get("type") or "tcp"
    if network == "ws":
        outbound["transport"] = {
            "type": "ws",
            "path": q.get("path") or "/",
            "headers": {"Host": q.get("host") or u.hostname},
        }
    return outbound


def build_singbox_config(proxy_links: list[str], api_port: int) -> dict[str, Any]:
    """Build sing-box config with all proxies + urltest + clash_api."""
    outbounds = []
    tags = []
    
    for i, link in enumerate(proxy_links):
        outbound = share_to_outbound(link)
        if not outbound:
            continue
        tag = f"proxy-{i}"
        outbound["tag"] = tag
        outbounds.append(outbound)
        tags.append(tag)
    
    if not outbounds:
        return None
    
    # Add urltest outbound
    outbounds.append({
        "type": "urltest",
        "tag": "auto-test",
        "outbounds": tags,
        "url": TEST_URL,
        "interval": "1m",
        "tolerance": 50,
    })
    
    # Add direct
    outbounds.append({"type": "direct", "tag": "direct"})
    
    return {
        "log": {"level": "error"},
        "experimental": {
            "clash_api": {
                "external_controller": f"127.0.0.1:{api_port}",
                "default_mode": "rule",
            }
        },
        "outbounds": outbounds,
        "route": {"final": "auto-test"},
    }


def test_proxies_via_clash_api(proxy_links: list[str], max_workers: int | None = None) -> list[str]:
    """Test all proxies via sing-box Clash API."""
    if not proxy_links:
        return []
    
    workers = max_workers or MAX_WORKERS
    
    # Dedupe
    seen = set()
    unique = []
    for p in proxy_links:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            unique.append(p)
    
    logging.info("sing-box Clash API test: %d unique proxies", len(unique))
    
    # Build config
    config = build_singbox_config(unique, CLASH_API_PORT)
    if not config:
        logging.warning("No valid proxies to test")
        return []
    
    # Write config
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    proc = None
    alive = []
    
    try:
        # Start sing-box
        proc = subprocess.Popen(
            [SINGBOX, "run", "-c", config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        # Wait for Clash API to be ready
        time.sleep(2)
        
        # Check if process is still alive
        if proc.poll() is not None:
            logging.error("sing-box process died early")
            return unique  # fallback
        
        # Query delay for each proxy via Clash API
        def check_one(tag: str, link: str) -> str | None:
            try:
                import urllib.request
                url = f"http://127.0.0.1:{CLASH_API_PORT}/proxies/{tag}/delay?url={urllib.parse.quote(TEST_URL)}&timeout={TEST_TIMEOUT}"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=TEST_TIMEOUT / 1000 + 2) as resp:
                    data = json.loads(resp.read().decode())
                    if "delay" in data and isinstance(data["delay"], int) and data["delay"] >= 0:
                        return link
            except Exception:
                pass
            return None
        
        # Concurrent check
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(check_one, f"proxy-{i}", link): link for i, link in enumerate(unique)}
            done = 0
            for fut in as_completed(futs):
                done += 1
                if done % 50 == 0 or done == len(unique):
                    logging.info("progress %d/%d alive=%d", done, len(unique), len(alive))
                try:
                    res = fut.result()
                    if res:
                        alive.append(res)
                except Exception:
                    pass
        
        logging.info("sing-box Clash API result: %d/%d alive", len(alive), len(unique))
        return alive if alive else unique
        
    except Exception as e:
        logging.error("sing-box Clash API error: %s", e)
        return unique  # fallback
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        if config_path and os.path.exists(config_path):
            try:
                os.unlink(config_path)
            except OSError:
                pass


# Backward compatibility
def filter_alive(proxy_list: list[str], max_workers: int | None = None) -> list[str]:
    """Test all share links via sing-box Clash API. Keep alive only."""
    return test_proxies_via_clash_api(proxy_list, max_workers)