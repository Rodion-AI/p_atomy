# импорт библиотек
from fastapi import FastAPI     # библиотека FastAPI
from pydantic import BaseModel  # модуль для объявления структуры данных
from ai import Chunk        # модуль для работы с OpenAI

# создаем объект приложения FastAPI
app = FastAPI()

# создадим объект для работы с OpenAI
chunk = Chunk()

# класс с типами данных для метода api/get_answer
class ModelAnswer(BaseModel):
    text: str

# функция, которая будет обрабатывать запрос по пути "/"
# полный путь запроса http://127.0.0.1:8000/
@app.get('/')
def root(): 
    return {'message': 'Hello FastAPI'}

# функция, которая обрабатывает запрос по пути "/about"
@app.get('/about')
def about():
    return {'message': 'Телеграмм бот для компании Atomy'}

# функция обработки post запроса + декоратор  (асинхронная)
@app.post('/api/get_answer_async')
async def get_answer_async(question: ModelAnswer):
    answer = await chunk.get_answer_async(query = question.text)
    return {'message': answer}     

