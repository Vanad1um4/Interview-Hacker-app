from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio

from ya_stt.ya_stt import stt_start_recording, stt_stop_recording, stt_get_results
from db import db_save_result_to_db, db_get_last_sentences_only
# from utils import write_to_file

clients = []
record_thread = None
transcribe_thread = None
recognition_in_progress = False

router = APIRouter()


@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)

            print('Received command:', command.get('action'))
            if command['action'] == 'start':
                await start_recognition()
            elif command['action'] == 'stop':
                await stop_recognition()
            elif command['action'] == 'get_results':
                await send_saved_results(websocket)

    except WebSocketDisconnect:
        clients.remove(websocket)


async def start_recognition():
    global record_thread, transcribe_thread, recognition_in_progress

    if recognition_in_progress:
        return

    record_thread, transcribe_thread = stt_start_recording()
    asyncio.create_task(transcribe_audio(record_thread, transcribe_thread))
    recognition_in_progress = True


async def stop_recognition():
    global record_thread, transcribe_thread, recognition_in_progress

    if record_thread and transcribe_thread:
        stt_stop_recording(record_thread, transcribe_thread)
        record_thread = None
        transcribe_thread = None

    recognition_in_progress = False


async def send_saved_results(websocket: WebSocket):
    sentences = db_get_last_sentences_only(last_N_minutes=30)
    print('sentences:', sentences)
    await websocket.send_json({'all_sentences': sentences})


async def transcribe_audio(record_thread, transcribe_thread):
    while record_thread.is_alive() and transcribe_thread.is_alive():
        sentence_dict = stt_get_results()
        ts, data = sentence_dict.popitem() if sentence_dict else (None, None)
        if ts and data and 'sentence' in data and data['words']:
            db_save_result_to_db(ts, data)
            for client in clients:
                await client.send_json({'sentence': {ts: data['sentence']}})
        await asyncio.sleep(0.1)
