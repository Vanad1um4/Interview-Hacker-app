import sqlite3
import json
import time


def db_init():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            words TEXT NOT NULL,
            sentence TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            dark_theme BOOLEAN NOT NULL DEFAULT 0,
            init_load_last_n_minutes INTEGER NOT NULL DEFAULT 10,
            main_prompt TEXT NOT NULL DEFAULT ''
        )
    ''')

    cursor.execute('''
        INSERT INTO settings (dark_theme, init_load_last_n_minutes, main_prompt)
        SELECT 0, 10, ''
        WHERE NOT EXISTS (SELECT 1 FROM settings)
    ''')

    conn.commit()
    conn.close()


db_init()


db_init()


def db_save_result_to_db(ts, data):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()

    cursor.execute('SELECT 1 FROM sentences WHERE timestamp = ?', (ts,))
    exists = cursor.fetchone()

    if exists:
        sql = '''
            UPDATE sentences
            SET words = ?, sentence = ?
            WHERE timestamp = ?
        '''
        cursor.execute(sql, (json.dumps(data['words'], ensure_ascii=False), data['sentence'], ts))
    else:
        sql = '''
            INSERT INTO sentences (timestamp, words, sentence)
            VALUES (?, ?, ?)
        '''
        cursor.execute(sql, (ts, json.dumps(data['words'], ensure_ascii=False), data['sentence']))

    conn.commit()
    conn.close()


def db_get_everything():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, timestamp, words, sentence FROM sentences')
    rows = cursor.fetchall()
    results = [{'id': row[0], 'timestamp': row[1], 'words': json.loads(row[2]), 'sentence': row[3]} for row in rows]
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


def db_get_last_sentences(last_N_minutes):
    current_time = time.time() * 1000
    time_threshold = current_time - (last_N_minutes * 60 * 1000)

    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, sentence FROM sentences WHERE timestamp >= ?', (time_threshold,))
    rows = cursor.fetchall()
    results = {row[0]: row[1] for row in rows}
    conn.close()

    return results


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
    cursor.execute('''
        UPDATE settings
        SET dark_theme = ?
    ''', (dark_theme,))
    conn.commit()
    conn.close()


def db_save_settings(settings):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE settings
        SET init_load_last_n_minutes = ?, main_prompt = ?
    ''', (settings['initLoadLastNMinutes'], settings['mainPrompt']))
    conn.commit()
    conn.close()
