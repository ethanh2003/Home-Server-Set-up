import sqlite3

db_path = '/home/ethan/docker/nginx_config/data/database.sqlite'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='proxy_host'")
    schema = cursor.fetchone()
    if schema:
        print(schema[0])
    else:
        print("Table 'proxy_host' not found.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
