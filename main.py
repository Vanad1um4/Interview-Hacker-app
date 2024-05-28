from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import time

from db import db_save_result_to_db, db_get_last_sentences, db_get_settings
from ya_stt.ya_stt import stt_start_recording, stt_stop_recording, stt_get_results
from chatgpt import get_openai_response
from utils import write_to_file

clients = []
record_thread = None
transcribe_thread = None
recognition_in_progress = False

router = APIRouter()


async def send_to_all_clients_via_ws(data):
    for client in clients:
        await client.send_json(data)


async def transcribe_audio(record_thread, transcribe_thread):
    while record_thread.is_alive() and transcribe_thread.is_alive():
        sentence_dict = stt_get_results()
        ts, data = sentence_dict.popitem() if sentence_dict else (None, None)

        if ts and data and 'sentence' in data and data['words']:  # filtering out empty results
            db_save_result_to_db(ts, data)
            await send_to_all_clients_via_ws({'recognition': {ts: data['sentence']}})

        await asyncio.sleep(0.1)


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


@router.get('/start', tags=['Main'])
async def start_recognition():
    global record_thread, transcribe_thread, recognition_in_progress

    if recognition_in_progress == True:
        return JSONResponse(content={'Recognition status': 'Already in progress'})

    record_thread, transcribe_thread = stt_start_recording()
    asyncio.create_task(transcribe_audio(record_thread, transcribe_thread))
    recognition_in_progress = True
    return JSONResponse(content={'Recognition status': 'Started successfully'})


@router.get('/stop', tags=['Main'])
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


@router.get('/get_last_sentences', tags=['Main'])
async def get_last_sentences():
    settings = db_get_settings()
    last_minutes = settings.get('initLoadLastNMinutes')
    sentences = db_get_last_sentences(last_minutes)
    return JSONResponse(content={'last_sentences': sentences})


@router.get('/infer/{last_minutes}', tags=['Inference'])
async def infer(last_minutes: int):
    sentences_dict = db_get_last_sentences(last_minutes)

    if not sentences_dict:
        await send_to_all_clients_via_ws({'inference': {'status': 'no start'}})
        return

    settings = db_get_settings()
    prompt = settings.get('mainPrompt')
    sentences = ' '.join(sentences_dict.values())

    try:
        await send_to_all_clients_via_ws({'inference': {'status': 'start'}})

        async for chunk in get_openai_response(prompt, sentences):
            if chunk:
                await send_to_all_clients_via_ws({'inference': {'data': chunk}})

        await send_to_all_clients_via_ws({'inference': {'status': 'end'}})
    except Exception as e:
        write_to_file('errors.log', f'{int(time.time())}: Ошибка генерации: {str(e)}', add=True)
