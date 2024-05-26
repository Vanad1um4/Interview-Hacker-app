from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from db import db_get_settings, db_save_settings, db_save_dark_theme

router = APIRouter()


@router.get('/')
async def send_settings():
    settings = db_get_settings()
    return JSONResponse(content=settings)


@router.post('/')
async def save_settings(settings: dict = Body(...)):
    try:
        if 'darkTheme' in settings:
            db_save_dark_theme(settings['darkTheme'])
        elif 'initLoadLastNMinutes' in settings and 'mainPrompt' in settings:
            db_save_settings(settings)
        else:
            raise HTTPException(status_code=400, detail="Invalid settings format")
        return JSONResponse(content=settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
