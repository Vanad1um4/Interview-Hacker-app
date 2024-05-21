from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json


from db import db_get_everything, db_get_sentences_only, db_save_result_to_db

clients = []

record_thread = None
transcribe_thread = None


router = APIRouter()


@router.post('/show_everything', tags=['Debug'])
def show_everything():
    return db_get_everything()


@router.post('/show_sentences', tags=['Debug'])
def show_sentences():
    return db_get_sentences_only()


@router.post('/download_sentences', tags=['Debug'])
def download_sentences_as_json():
    sentences = json.dumps(db_get_sentences_only(), ensure_ascii=False, indent=4)
    from io import BytesIO
    temp_file = BytesIO(sentences.encode('utf-8'))
    return StreamingResponse(temp_file, media_type='application/octet-stream', headers={'Content-Disposition': 'attachment; filename="example.txt"'})
