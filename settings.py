from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from db import db_get_settings, db_save_settings, db_save_dark_theme

router = APIRouter()


class DarkThemeSettings(BaseModel):
    darkTheme: bool


class MainSettings(BaseModel):
    darkTheme: bool
    initLoadLastNMinutes: int
    mainPrompt: str


@router.get('/', tags=['Settings'])
async def send_settings():
    settings = db_get_settings()
    return JSONResponse(content=settings)


@router.post('/main', tags=['Settings'])
async def save_settings(settings: MainSettings):
    db_save_settings(settings.dict())
    return JSONResponse(content=settings.dict())


@router.post('/theme', tags=['Settings'])
async def save_settings(settings: DarkThemeSettings):
    db_save_dark_theme(settings.darkTheme)
