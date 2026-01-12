import os

conf_dir = '/home/ethan/docker/nginx_config/data/nginx/proxy_host'

hosts = [
    (8, "jellyseerr.ethanh.online", "jellyseerr", 5055),
    (9, "tubearchivist.ethanh.online", "tubearchivist", 8002),
    (10, "stash.ethanh.online", "stash", 9999),
    (11, "komga.ethanh.online", "komga", 25600),
    (12, "qbittorrent.ethanh.online", "gluetun", 8080),
    (13, "prowlarr.ethanh.online", "gluetun", 9696),
    (14, "sonarr.ethanh.online", "sonarr", 8989),
    (15, "radarr.ethanh.online", "radarr", 7878),
    (16, "lidarr.ethanh.online", "lidarr", 8686),
    (17, "whisparr.ethanh.online", "gluetun", 6969),
    (18, "autobrr.ethanh.online", "gluetun", 7474),
    (19, "lazylibrarian.ethanh.online", "lazylibrarian", 5299),
    (20, "uptime.ethanh.online", "uptime-kuma", 3001),
    (21, "glances.ethanh.online", "192.168.1.113", 61208),
    (22, "kopia.ethanh.online", "kopia_backup", 51515),
    (23, "dashboard.ethanh.online", "homepage", 3000),
    (24, "readarr.ethanh.online", "readarr", 8787),
    (25, "audiobookshelf.ethanh.online", "audiobookshelf", 80)
]

template = """# ------------------------------------------------------------
# {domain}
# ------------------------------------------------------------

server {{
  set $forward_scheme http;
  set $server         "{host}";
  set $port           {port};

  listen 80;
  listen [::]:80;

  listen 443 ssl;
  listen [::]:443 ssl;

  server_name {domain};
  http2 off;

  # Let's Encrypt SSL
  include conf.d/include/letsencrypt-acme-challenge.conf;
  include conf.d/include/ssl-cache.conf;
  include conf.d/include/ssl-ciphers.conf;
  ssl_certificate /etc/letsencrypt/live/npm-1/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/npm-1/privkey.pem;

  # Block Exploits
  include conf.d/include/block-exploits.conf;

  access_log /data/logs/proxy-host-{id}_access.log proxy;
  error_log /data/logs/proxy-host-{id}_error.log warn;

  location / {{
    # Proxy!
    include conf.d/include/proxy.conf;
  }}

  # Custom
  include /data/nginx/custom/server_proxy[.]conf;
}}
"""

for host_id, domain, host, port in hosts:
    file_path = os.path.join(conf_dir, f"{host_id}.conf")
    content = template.format(id=host_id, domain=domain, host=host, port=port)
    
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Generated {file_path}")
    except Exception as e:
        print(f"Error generating {file_path}: {e}")
