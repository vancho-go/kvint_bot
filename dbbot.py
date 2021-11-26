import sqlite3
import config
import os

def init_db():
    if not os.path.exists(config.dbbot_file):
        conn = sqlite3.connect(config.dbbot_file)
        cur = conn.cursor()
        cur.execute('CREATE TABLE kvint_bot(userid INT PRIMARY KEY, state TEXT, size TEXT, pay_type TEXT)')
        conn.commit()
        conn.close()

def get_current_state(userid):
    conn = sqlite3.connect(config.dbbot_file)
    cur = conn.cursor()
    try:
        return str(cur.execute(f'SELECT state FROM kvint_bot WHERE userid={userid}').fetchone())[2:-3]
    except:
        return 'S_ENTER_SIZE'
    finally:
        conn.close()

def get_size(userid):
    conn = sqlite3.connect(config.dbbot_file)
    cur = conn.cursor()
    try:
        return list(cur.execute(f'SELECT size FROM kvint_bot WHERE userid={userid}').fetchone())[0]
    except:
        pass
    finally:
        conn.close()

def get_pay_type(userid):
    conn = sqlite3.connect(config.dbbot_file)
    cur = conn.cursor()
    try:
        return list(cur.execute(f'SELECT pay_type FROM kvint_bot WHERE userid={userid}').fetchone())[0]
    except:
        pass
    finally:
        conn.close()

def set_state(userid, state):
    conn = sqlite3.connect(config.dbbot_file)
    cur = conn.cursor()
    try:
        cur.execute(f'INSERT INTO kvint_bot VALUES({userid}, "{state}", "null", "null")')
    except:
        cur.execute(f'UPDATE kvint_bot SET state="{state}" WHERE userid={userid}')
    conn.commit()
    conn.close()

def set_size(userid, size):
    conn = sqlite3.connect(config.dbbot_file)
    cur = conn.cursor()
    cur.execute(f'UPDATE kvint_bot SET size="{size}" WHERE userid={userid}')
    conn.commit()
    conn.close()

def set_pay_type(userid, pay_type):
    conn = sqlite3.connect(config.dbbot_file)
    cur = conn.cursor()
    cur.execute(f'UPDATE kvint_bot SET pay_type="{pay_type}" WHERE userid={userid}')
    conn.commit()
    conn.close()


init_db()

#a = get_current_size_and_pay_type(281093430)
#set_data(123, 'PAY', 'BIG')

#a = get_current_state(123)
#print(a)