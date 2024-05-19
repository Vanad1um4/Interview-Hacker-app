import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import json
import asyncio
from ya_stt.ya_stt import start_recording, stop_recording, get_results

from settings import APP_IP, APP_PORT

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db():
    conn = sqlite3.connect("main.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sentences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        words TEXT NOT NULL,
        sentence TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


init_db()

clients = []

record_thread = None
transcribe_thread = None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)

            if command["action"] == "start":
                await start_recognition()
            elif command["action"] == "stop":
                await stop_recognition()
            elif command["action"] == "get_results":
                await send_saved_results(websocket)

    except WebSocketDisconnect:
        clients.remove(websocket)


async def start_recognition():
    global record_thread, transcribe_thread
    record_thread, transcribe_thread = start_recording()
    asyncio.create_task(transcribe_audio(record_thread, transcribe_thread))


async def stop_recognition():
    global record_thread, transcribe_thread
    if record_thread and transcribe_thread:
        stop_recording(record_thread, transcribe_thread)
        record_thread = None
        transcribe_thread = None


async def send_saved_results(websocket: WebSocket):
    conn = sqlite3.connect("main.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sentences")
    rows = cursor.fetchall()
    results = [
        {"id": row[0], "timestamp": row[1], "words": json.loads(row[2]), "sentence": row[3]}
        for row in rows
    ]
    await websocket.send_json(results)
    conn.close()


async def transcribe_audio(record_thread, transcribe_thread):
    while record_thread.is_alive() and transcribe_thread.is_alive():
        result = get_results()
        print(result)
        # if 'words' in result and 'sentence' in result:
        #     await save_and_send_result(result)
        await asyncio.sleep(0.1)


async def save_and_send_result(result):
    conn = sqlite3.connect("main.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sentences (words, sentence) VALUES (?, ?)",
                   (json.dumps(result["words"]), result["sentence"]))
    conn.commit()
    conn.close()

    for client in clients:
        await client.send_json(result)


@app.get('/', response_class=FileResponse, tags=['Site'])
async def serve_angular_app():
    return FileResponse('front-src/index.html')

app.mount('/', StaticFiles(directory='front-src', html=True))

if __name__ == '__main__':
    uvicorn.run(app, host=f'{APP_IP}', port=APP_PORT)
