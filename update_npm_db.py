import sqlite3
import json
from datetime import datetime

db_path = '/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite'

hosts = [
    (8, ["jellyseerr.ethanh.online"], "jellyseerr", 5055),
    (9, ["tubearchivist.ethanh.online"], "tubearchivist", 8002),
    (10, ["stash.ethanh.online"], "stash", 9999),
    (11, ["komga.ethanh.online"], "komga", 25600),
    (12, ["qbittorrent.ethanh.online"], "gluetun", 8080),
    (13, ["prowlarr.ethanh.online"], "gluetun", 9696),
    (14, ["sonarr.ethanh.online"], "sonarr", 8989),
    (15, ["radarr.ethanh.online"], "radarr", 7878),
    (16, ["lidarr.ethanh.online"], "lidarr", 8686),
    (17, ["whisparr.ethanh.online"], "gluetun", 6969),
    (18, ["autobrr.ethanh.online"], "gluetun", 7474),
    (19, ["lazylibrarian.ethanh.online"], "lazylibrarian", 5299),
    (20, ["uptime.ethanh.online"], "uptime-kuma", 3001),
    (21, ["glances.ethanh.online"], "192.168.1.113", 61208),
    (22, ["kopia.ethanh.online"], "kopia_backup", 51515),
    (23, ["dashboard.ethanh.online"], "homepage", 3000),
    (24, ["readarr.ethanh.online"], "readarr", 8787),
    (25, ["audiobookshelf.ethanh.online"], "audiobookshelf", 80),
    (26, ["homebox.ethanh.online"], "homebox", 7745)
]

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for host_id, domains, forward_host, forward_port in hosts:
        # Check if exists
        cursor.execute("SELECT id FROM proxy_host WHERE id = ?", (host_id,))
        exists = cursor.fetchone()

        domain_names_json = json.dumps(domains)
        meta_json = json.dumps({"letsencrypt_agree": False, "dns_challenge": False})
        
        if exists:
            print(f"Updating host {host_id}: {domains[0]} -> {forward_host}:{forward_port}")
            cursor.execute("""
                UPDATE proxy_host 
                SET modified_on = ?, 
                    domain_names = ?, 
                    forward_host = ?, 
                    forward_port = ?, 
                    forward_scheme = 'http',
                    certificate_id = 1, 
                    ssl_forced = 0, 
                    block_exploits = 0,
                    http2_support = 0,
                    hsts_enabled = 0,
                    hsts_subdomains = 0,
                    allow_websocket_upgrade = 0
                WHERE id = ?
            """, (now, domain_names_json, forward_host, forward_port, host_id))
        else:
            print(f"Inserting host {host_id}: {domains[0]} -> {forward_host}:{forward_port}")
            cursor.execute("""
                INSERT INTO proxy_host (
                    id, created_on, modified_on, owner_user_id, is_deleted, 
                    domain_names, forward_host, forward_port, access_list_id, 
                    certificate_id, ssl_forced, caching_enabled, block_exploits, 
                    advanced_config, meta, allow_websocket_upgrade, http2_support, 
                    forward_scheme, enabled, locations, hsts_enabled, hsts_subdomains
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                host_id, now, now, 1, 0, 
                domain_names_json, forward_host, forward_port, 0, 
                1, 0, 0, 0, 
                '', meta_json, 0, 0, 
                'http', 1, '[]', 0, 0
            ))

    conn.commit()
    print("Database updated successfully.")
    conn.close()

except Exception as e:
    print(f"Error updating database: {e}")
