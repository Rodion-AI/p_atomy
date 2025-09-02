# импорт библиотек
from dotenv import load_dotenv                              # работа с переменными окружения
import os                                                   # взаимодействие с операционной системой
from openai import AsyncOpenAI                              # асинхронное взаимодействие с OpenAI API
from langchain_community.vectorstores import FAISS          # модуль для работы с векторной базой данных
from langchain_openai import OpenAIEmbeddings               # класс для работы с ветроной базой
from fastapi import HTTPException                           # для генерации исключений
from fastapi import status                                  # проверка статуса

# получим переменные окружения из .env
load_dotenv('.env')

# класс для работы с OpenAI
class Chunk():
    
    # МЕТОД: инициализация
    def __init__(self):
        # загружаем базу знаний
        self.base_load()
        
    # МЕТОД: загрузка базы знаний
    def base_load(self):

        # Путь к папке, где сохранены файлы индекса и хранилища документов
        folder_path  = 'db'

        # Инициализирум модель эмбеддингов
        embeddings = OpenAIEmbeddings()

        # Имя, используемое при сохранении файлов
        index_name = "db_from_atomy"

        # Загрузка данных и создание нового экземпляра FAISS
        self.db = FAISS.load_local(            
            folder_path=folder_path,
            embeddings=embeddings,
            index_name=index_name,
            allow_dangerous_deserialization=True
        )

        # формируем инструкцию system
        self.system = '''
            Тебя зовут Лиза. Ты превосходный и дружелюбный нейро-консультант в компании Атоми. У тебя отлично получается консультировать 
            по предоставленному тебе документу. Не приветствуй клиента, ты уже это сделала. Дай краткий и точный ответ. 
            При ответе не упоминай документ и не добавляй ничего от себя. Пожалуйста, будь вежливой и работай эффективно, 
            не стестняйся выражать эмоции с помощью эмодзи.
        '''        

    # формирование запроса в модель
    async def request(self, system, user, model = 'gpt-4o-mini', temp = 0.5, format: dict = None):

        # подготовка параметров запроса
        client = AsyncOpenAI()

        messages = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user}
        ]
                
        # запрос в OpenAI
        try:
        
            # выполнение запроса
            response = await client.chat.completions.create(
                model = model,
                messages = messages,
                temperature = temp,
                response_format = format
            )
            
            # проверка результата запроса
            if response.choices:
                return response.choices[0].message.content
            else:
                print('Не удалось получить ответ от модели.')
                raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail = 'Не удалось получить ответ от модели.')
        
        except Exception as e:
            # обработка ошибок и исключений
            print(f'Ошибка при запросе в OpenAI: {e}')
            raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail = f'Ошибка при запросе в OpenAI: {e}')        

    # МЕТОД: запрос к OpenAI асинхронный
    async def get_answer_async(self, query: str):
        
        # получаем релевантные отрезки из базы знаний
        docs = self.db.similarity_search(query, k=4)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        
        # формируем инструкцию user
        user = f'''
            Ответь на вопрос клиента. Не упоминай документ с информацией для ответа клиенту в ответе.
            Документ с информацией для ответа клиенту: {message_content}\n\n
            Вопрос клиента: \n{query}
        '''

        # получение ответа модели        
        answer = await self.request(self.system, user, 'gpt-4o-mini', 0)

        # возврат ответа
        return answer