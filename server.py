import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import main
import debug
import settings

from env import APP_IP, APP_PORT

app = FastAPI()

tags_metadata = [
    {'name': 'Main', 'description': 'Главный модуль'},
    {'name': 'Settings', 'description': 'Модуль настроек'},
    {'name': 'Debug', 'description': 'Дебаг функции'},
]

app = FastAPI(title='Interview Hacker', openapi_tags=tags_metadata)

app.include_router(main.router, prefix='/api/main')
app.include_router(debug.router, prefix='/api/debug')
app.include_router(settings.router, prefix='/api/settings')

app.mount('/', StaticFiles(directory='front-src', html=True), name='static')

if __name__ == '__main__':
    uvicorn.run(app, host=f'{APP_IP}', port=APP_PORT)
