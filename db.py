import sqlite3
import json
import time


def db_init():
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    sql = '''
        CREATE TABLE IF NOT EXISTS sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            words TEXT NOT NULL,
            sentence TEXT NOT NULL
        )'''
    cursor.execute(sql)
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
