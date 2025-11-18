import sqlite3

DB = 'backend/db/app.db'

def list_users():
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users")
        rows = cur.fetchall()
        print('users_count=', len(rows))
        for r in rows:
            print(r)
    except Exception as e:
        print('error:', e)
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == '__main__':
    list_users()
