from fastapi import APIRouter, HTTPException, Form

from fastapi.responses import StreamingResponse
import json


from db import db_get_everything, db_get_sentences_only, db_get_settings, db_delete_all_sentences, db_update_sentence_by_id, db_delete_sentence_by_id

clients = []

record_thread = None
transcribe_thread = None


router = APIRouter()


@router.get('/show_everything', tags=['Debug'])
def show_everything():
    return db_get_everything()


@router.get('/show_sentences', tags=['Debug'])
def show_sentences():
    return db_get_sentences_only()


@router.post('/edit_sentence', tags=['Debug'])
def edit_sentence(id: int = Form(...), sentence: str = Form(...)):
    try:
        db_update_sentence_by_id(id, sentence)
        return {'message': 'Record updated successfully'}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/download_sentences', tags=['Debug'])
def download_sentences_as_json():
    sentences = json.dumps(db_get_sentences_only(), ensure_ascii=False, indent=4)
    from io import BytesIO
    temp_file = BytesIO(sentences.encode('utf-8'))
    return StreamingResponse(temp_file, media_type='application/octet-stream', headers={'Content-Disposition': 'attachment; filename="data.txt"'})


@router.delete('/delete_sentences', tags=['Debug'])
def delete_sentences():
    db_delete_all_sentences()


@router.delete('/delete_one_sentence', tags=['Debug'])
def delete_one_sentence(id: int = Form(...)):
    db_delete_sentence_by_id(id)


@router.get('/show_settings', tags=['Debug'])
def show_sentences():
    return db_get_settings()
