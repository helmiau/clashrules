#!/usr/bin/env python3
"""
Concurrent proxy tester via sing-box.
Share-link → temp config → dial test → keep alive only.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import socket
import subprocess
import tempfile
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SINGBOX = os.environ.get("SINGBOX_BIN", "sing-box")
TEST_URL = os.environ.get("PROXY_TEST_URL", "https://www.gstatic.com/generate_204")
TEST_TIMEOUT = int(os.environ.get("PROXY_TEST_TIMEOUT", "8"))
MAX_WORKERS = int(os.environ.get("PROXY_TEST_WORKERS", "20"))


def _b64decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


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


def _ss_to_outbound(link: str) -> dict[str, Any] | None:
    # ss://BASE64@host:port#tag  OR  ss://method:pass@host:port#tag  OR  ss://BASE64#tag
    raw = link[5:]
    tag = "ss"
    if "#" in raw:
        raw, tag = raw.split("#", 1)
        tag = urllib.parse.unquote(tag) or "ss"
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
        # method:password@host:port
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


def _build_config(outbound: dict[str, Any], mixed_port: int) -> dict[str, Any]:
    return {
        "log": {"level": "error"},
        "inbounds": [
            {
                "type": "mixed",
                "tag": "mixed-in",
                "listen": "127.0.0.1",
                "listen_port": mixed_port,
            }
        ],
        "outbounds": [outbound, {"type": "direct", "tag": "direct"}],
    }


def test_one(link: str) -> str | None:
    """Return link if alive via sing-box, else None."""
    outbound = share_to_outbound(link)
    if not outbound:
        return None
    port = _free_port()
    cfg = _build_config(outbound, port)
    cfg_path = None
    proc = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(cfg, f)
            cfg_path = f.name
        proc = subprocess.Popen(
            [SINGBOX, "run", "-c", cfg_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.4)
        if proc.poll() is not None:
            return None
        # curl through mixed inbound
        r = subprocess.run(
            [
                "curl",
                "-sS",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "--connect-timeout",
                str(TEST_TIMEOUT),
                "--max-time",
                str(TEST_TIMEOUT + 2),
                "-x",
                f"http://127.0.0.1:{port}",
                TEST_URL,
            ],
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT + 5,
        )
        code = (r.stdout or "").strip()
        if code in ("204", "200"):
            return link
        return None
    except Exception:
        return None
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except Exception:
                proc.kill()
        if cfg_path and os.path.exists(cfg_path):
            try:
                os.unlink(cfg_path)
            except OSError:
                pass


def filter_alive(proxy_list: list[str], max_workers: int | None = None) -> list[str]:
    """Test all share links concurrently with sing-box. Keep alive only."""
    if not proxy_list:
        return []
    workers = max_workers or MAX_WORKERS
    # dedupe preserve order
    seen: set[str] = set()
    unique: list[str] = []
    for p in proxy_list:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            unique.append(p)

    logging.info("sing-box test: %d unique proxies, workers=%d", len(unique), workers)
    alive: list[str] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(test_one, p): p for p in unique}
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
    logging.info("sing-box result: %d/%d alive", len(alive), len(unique))
    return alive