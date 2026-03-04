# import module
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# load enviroments
load_dotenv()


class Chunk:

    # Инициализация
    def __init__(self):
        self.client = AsyncOpenAI()
        self.base_load()

    # Загрузка базы знаний
    def base_load(self):
        folder_path = "db"
        index_name = "db_from_atomy"

        embeddings = OpenAIEmbeddings()

        self.db = FAISS.load_local(
            folder_path=folder_path,
            embeddings=embeddings,
            index_name=index_name,
            allow_dangerous_deserialization=True,
        )

        self.system = """
        Тебя зовут Лиза. Ты превосходный и дружелюбный нейро-консультант компании Атоми.
        Ты консультируешь строго на основе переданной информации.
        Не приветствуй клиента, ты уже это сделала.
        Дай краткий, точный ответ.
        Не упоминай документ и не добавляй ничего от себя.
        Будь вежливой и можешь использовать эмодзи.
        """

    # Запрос к модели через новую Responses API
    async def request(
        self,
        user_message: str,
        model: str = "gpt-5-mini",
        temperature: float = 0,
    ) -> str:

        try:
            response = await self.client.responses.create(
                model=model,
                temperature=temperature,
                input=[
                    {
                        "role": "system",
                        "content": self.system,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
            )

            return response.output_text

        except Exception as e:
            print(f"Ошибка при запросе в OpenAI: {e}")
            return "Произошла ошибка при обработке запроса. Попробуйте позже."

    # Основной метод для Telegram-бота
    async def get_answer_async(self, query: str) -> str:

        try:
            # Получаем релевантные фрагменты
            docs = self.db.similarity_search(query, k=4)
            message_content = "\n".join([doc.page_content for doc in docs])

            user_prompt = f"""
            Ответь на вопрос клиента.
            Не упоминай документ в ответе.

            Информация для ответа:
            {message_content}

            Вопрос клиента:
            {query}
            """

            answer = await self.request(user_prompt)
            return answer

        except Exception as e:
            print(f"Ошибка при обработке запроса: {e}")
            return "Не удалось получить ответ. Попробуйте позже."