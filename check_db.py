import sqlite3

db_path = '/home/ethan/docker/nginx_config/data/database.sqlite'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Check a sample host (e.g., ID 8)
    cursor.execute("SELECT id, forward_host, ssl_forced, hsts_enabled FROM proxy_host WHERE id >= 8")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
