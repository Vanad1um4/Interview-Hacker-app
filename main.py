from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import json
import asyncio

from ya_stt.ya_stt import stt_start_recording, stt_stop_recording, stt_get_results
from db import db_save_result_to_db, db_get_last_sentences, db_get_settings

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
            data = await websocket.receive_json()

            if data.get('request') == 'PING':
                await websocket.send_json({'response': 'PONG'})
            else:
                pass

    except WebSocketDisconnect:
        print('Client disconnected')
        clients.remove(websocket)


@router.get('/start')
async def start_recognition():
    global record_thread, transcribe_thread, recognition_in_progress

    if recognition_in_progress == True:
        return JSONResponse(content={'Recognition status': 'Already in progress'})

    record_thread, transcribe_thread = stt_start_recording()
    asyncio.create_task(transcribe_audio(record_thread, transcribe_thread))
    recognition_in_progress = True
    return JSONResponse(content={'Recognition status': 'Started successfully'})


@router.get('/stop')
async def stop_recognition():
    global record_thread, transcribe_thread, recognition_in_progress

    if recognition_in_progress == False:
        return JSONResponse(content={'Recognition status': 'Already stopped'})

    if record_thread and transcribe_thread:
        stt_stop_recording(record_thread, transcribe_thread)
        record_thread = None
        transcribe_thread = None

    recognition_in_progress = False
    return JSONResponse(content={'Recognition status': 'Stopped successfully'})


@router.get('/get_last_sentences')
async def get_last_sentences():
    settings = db_get_settings()
    last_N_minutes = settings.get('initLoadLastNMinutes') or 30
    sentences = db_get_last_sentences(last_N_minutes=last_N_minutes)
    return JSONResponse(content={'last_sentences': sentences})


async def transcribe_audio(record_thread, transcribe_thread):
    while record_thread.is_alive() and transcribe_thread.is_alive():
        sentence_dict = stt_get_results()
        ts, data = sentence_dict.popitem() if sentence_dict else (None, None)

        if ts and data and 'sentence' in data and data['words']:  # not saving empty results
            db_save_result_to_db(ts, data)

            for client in clients:
                await client.send_json({'sentence': {ts: data['sentence']}})

        await asyncio.sleep(0.1)
