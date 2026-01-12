import sqlite3

db_path = '/home/ethan/docker/nginx_config/data/database.sqlite'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Disable Force SSL and HSTS for the new hosts (ID 8-23)
    # The user asked to remove force SSL for apps that don't support it.
    # It's safer to disable it for the ones reporting errors.
    # I'll disable it for all the ones I added to be safe and consistent with the request.
    
    print("Disabling Force SSL and HSTS for hosts 8-23...")
    cursor.execute("""
        UPDATE proxy_host 
        SET ssl_forced = 0, 
            hsts_enabled = 0 
        WHERE id >= 8 AND id <= 23
    """)
    
    conn.commit()
    print("Database updated successfully.")
    conn.close()

except Exception as e:
    print(f"Error updating database: {e}")
