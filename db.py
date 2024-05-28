import sqlite3
import time


def db_init():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            sentence TEXT NOT NULL
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            dark_theme BOOLEAN NOT NULL DEFAULT 0,
            init_load_last_n_minutes INTEGER NOT NULL DEFAULT 10,
            main_prompt TEXT NOT NULL DEFAULT ''
        )''')

    cursor.execute('''
        INSERT INTO settings (dark_theme, init_load_last_n_minutes, main_prompt)
        SELECT 0, 30, ''
        WHERE NOT EXISTS (SELECT 1 FROM settings)''')

    conn.commit()
    conn.close()


db_init()


def db_save_result_to_db(ts, data):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    cursor.execute('SELECT 1 FROM sentences WHERE timestamp = ?', (ts,))
    exists = cursor.fetchone()

    if exists:
        sql = '''
            UPDATE sentences
            SET sentence = ?
            WHERE timestamp = ?'''
        cursor.execute(sql, (data['sentence'], ts))
    else:
        sql = '''
            INSERT INTO sentences (timestamp, sentence)
            VALUES (?, ?)'''
        cursor.execute(sql, (ts, data['sentence']))

    conn.commit()
    conn.close()


def db_get_everything():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, timestamp, sentence FROM sentences')
    rows = cursor.fetchall()
    results = [{'id': row[0], 'timestamp': row[1], 'sentence': row[2]} for row in rows]
    conn.close()

    return results


def db_get_sentences_only():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, sentence FROM sentences')
    rows = cursor.fetchall()
    results = {row[0]: row[1] for row in rows}
    conn.close()

    return results


def db_get_last_sentences(last_minutes):
    current_time = time.time() * 1000
    time_threshold = current_time - (last_minutes * 60 * 1000)

    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, sentence FROM sentences WHERE timestamp >= ?', (time_threshold,))
    rows = cursor.fetchall()
    results = {row[0]: row[1] for row in rows}
    conn.close()

    return results


def db_update_sentence_by_id(record_id, new_sentence):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    sql = '''
        UPDATE sentences
        SET sentence = ?
        WHERE id = ?'''
    cursor.execute(sql, (new_sentence, record_id))
    conn.commit()
    conn.close()


def db_delete_all_sentences():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sentences')
    conn.commit()
    conn.close()


def db_delete_sentence_by_id(record_id):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    sql = '''
        DELETE FROM sentences
        WHERE id = ?'''
    cursor.execute(sql, (record_id,))
    conn.commit()
    conn.close()


def db_get_settings():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('SELECT dark_theme, init_load_last_n_minutes, main_prompt FROM settings LIMIT 1')
    row = cursor.fetchone()
    settings = {
        'darkTheme': bool(row[0]),
        'initLoadLastNMinutes': row[1],
        'mainPrompt': row[2]
    }
    conn.close()

    return settings


def db_save_dark_theme(dark_theme):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    sql = '''
        UPDATE settings
        SET dark_theme = ?'''
    cursor.execute(sql, (dark_theme,))
    conn.commit()
    conn.close()


def db_save_settings(settings):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    sql = '''
        UPDATE settings
        SET dark_theme = ?, init_load_last_n_minutes = ?, main_prompt = ?'''
    cursor.execute(sql, (settings['darkTheme'], settings['initLoadLastNMinutes'], settings['mainPrompt']))
    conn.commit()
    conn.close()
