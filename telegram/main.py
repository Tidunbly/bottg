import pickle
import logging
from threading import Lock
from typing import Dict
import asyncio
import aiofiles
from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from vectore_store_manager import create_vectorstore
from config import *

# Настройка логгера
logger = logging.getLogger(__name__)

# Инициализация хранилища
store: Dict[str, ChatMessageHistory] = {}
store_lock = Lock()
autosave_task = None

# Инициализация компонентов RAG
vectorstore = create_vectorstore(json_file_path)

chat = GigaChat(
    credentials=cred,
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS",
    model='GigaChat',
    streaming=False,
    max_tokens=100

)

contextualize_q_system_prompt = (
    "Вы — сотрудник службы поддержки. Ваша задача — отвечать на вопросы пользователей, используя информацию из базы знаний. "
    "Если вопрос не относится к технической поддержке, строго ответьте: 'Извините, я могу отвечать только на вопросы, связанные с технической поддержкой.'"
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

retriever = vectorstore.as_retriever(search_kwargs={"k": 1})


history_aware_retriever = create_history_aware_retriever(
    chat, retriever, contextualize_q_prompt
)

question_answer_chain = create_stuff_documents_chain(chat, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)


async def save_store():
    try:
        async with aiofiles.open('chat_history.pkl', 'wb') as f:
            data = await asyncio.to_thread(pickle.dumps, store)
            await f.write(data)
    except Exception as e:
        logger.error(f"Error saving store: {e}")


async def load_store():
    try:
        async with aiofiles.open('chat_history.pkl', 'rb') as f:
            content = await f.read()
            return await asyncio.to_thread(pickle.loads, content)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.error(f"Error loading store: {e}")
        return {}


async def initialize_store():
    global store
    store = await load_store()


async def autosave():
    while True:
        await asyncio.sleep(300)  # Автосохранение каждые 5 минут
        await save_store()


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    with store_lock:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        else:
            messages = store[session_id].messages
            if len(messages) > 3:
                store[session_id].messages = messages[-3:]
        return store[session_id]


async def delete_session_history(session_id: str) -> bool:
    with store_lock:
        if session_id in store:
            del store[session_id]
            await save_store()
            return True
        return False


conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)

gigachat_lock = asyncio.Lock()

async def rag_answer_with_history(question: str, query_id: str) -> str:
    async with gigachat_lock:
        try:
            response = await conversational_rag_chain.ainvoke(
                {"input": question},
                config={"configurable": {"session_id": query_id}}
            )
            return response.get("answer", "Не удалось получить ответ")
        except Exception as e:
            return "Произошла ошибка при обработке запроса"
            print(e)







async def on_startup():
    await initialize_store()
    asyncio.create_task(autosave())



async def on_shutdown():
    await save_store()

