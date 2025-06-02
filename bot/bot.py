import os
import logging
from PIL import Image, ImageDraw, ImageFont
import requests
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# import TinyTag

import subprocess

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "8014238558:AAGe_3zNyi2PyicACP-rPeHmCKmXWTFuAsA"
SALUTE_SPEECH_API_KEY = "ODRlOGJmZGUtM2U2Ni00MWJkLWJkNTQtMWNkNzFlZWIwNzA0OjU1MjA3ZTU3LTljNjktNGY0MS1iMDhlLTNmODI2ZDA5ZjE5Yw=="
SALUTE_SPEECH_URL = "https://smartspeech.sber.ru/rest/v1/speech:recognize"
MODEL_NAME = "deepseek-ai/Perception-LM-1B"  # Или другая версия модели
CACHE_DIR = "./model_cache"
TEMP_IMAGE_DIR = "./temp_images"
FONT_PATH = "./arial.ttf"  # Путь к файлу шрифта для подписей
QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation"
QWEN_API_KEY = ""



# Создание директорий, если их нет
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

# Инициализация модели и токенизатора
# try:
#     tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
#     model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     model.to(device)
#     logger.info("Модель загружена успешно")
# except Exception as e:
#     logger.error(f"Ошибка при загрузке модели: {e}")
#     raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "Привет! Я бот с моделью Perception-LM-1B.\n\n"
        "Отправьте мне изображение и текстовый запрос, и я:\n"
        "1. Сгенерирую текстовый ответ на ваш запрос\n"
        "2. Создам изображение с текстовой подписью\n\n"
        "Просто отправьте мне фото и текст (можно в одном сообщении или раздельно)."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_text = update.message.text
    context.user_data['text_query'] = user_text
    await update.message.reply_text("Текст запроса сохранён. Теперь отправьте изображение.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик изображений"""
    # Получаем файл изображения
    photo_file = await update.message.photo[-1].get_file()
    image_path = os.path.join(TEMP_IMAGE_DIR, f"temp_{update.update_id}.jpg")
    await photo_file.download_to_drive(image_path)
    
    # Сохраняем путь к изображению в user_data
    context.user_data['image_path'] = image_path
    
    # Проверяем, есть ли текстовый запрос
    if 'text_query' in context.user_data:
        await process_request(update, context)
    else:
        await update.message.reply_text("Axax. Изображение получено. Теперь отправьте текстовый запрос.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    try:
        # Получаем голосовое сообщение
        voice_file = await update.message.voice.get_file()
        
        # Скачиваем файл
        voice_path = f"voice_{update.update_id}.ogg"
        await voice_file.download_to_drive(voice_path)
        
        # Преобразуем в текст
        await update.message.reply_text("Обрабатываю ваше сообщение...")
        text = await speech_to_text(voice_path)
        
        # Отправляем результат
        await update.message.reply_text(f"Текст запроса сохранён. Распознанный текст:\n\n{text}")

        context.user_data['text_query'] = text

        # Удаляем временный файл
        os.remove(voice_path)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке голоса: {e}")
        await update.message.reply_text(f"Произошла ошибка при обработке голосового сообщения: {e}")

async def speech_to_text(audio_path: str) -> str:
    """Преобразование голоса в текст с помощью Salute Speech"""
    headers = {
        "Authorization": f"Bearer {SALUTE_ACCESS_TOKEN}",
        "Content-Type": "audio/ogg;codecs=opus"
    }
    
    with open(audio_path, 'rb') as audio_file:
        response = requests.post(
            SALUTE_SPEECH_URL,
            headers=headers,
            data=audio_file,
            verify=False
        )
    
    if response.status_code == 200:
        return response.json().get('result', 'Текст не распознан')
    else:
        err = f"Ошибка Salute Speech API: {response.status_code} - {response.text}"
        logger.error(err)
        raise Exception(f"Ошибка при распознавании речи: {err}")

async def process_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка запроса (изображение + текст)"""
    try:
        image_path = context.user_data['image_path']
        text_query = context.user_data['text_query']

        subprocess.run(["cp", image_path, "im.jpg"])
        
        # Загружаем изображение
        
        # Отправляем уведомление о начале обработки
        await update.message.reply_text("Обрабатываю ваш запрос...")
        
        # Генерируем текстовый ответ (здесь должна быть логика работы с вашей моделью)
        text_response = generate_text_response("im.jpg", text_query)

        # Отправляем результаты пользователю
        await update.message.reply_text(f"Текстовый ответ:\n\n{text_response}")
         
        # # Создаем изображение с подписью
        # output_image_path = os.path.join(TEMP_IMAGE_DIR, f"output_{update.update_id}.jpg")
        # create_image_with_caption(image, text_response, output_image_path)
        
       
        # with open(output_image_path, 'rb') as photo:
        #     await update.message.reply_photo(photo=InputFile(photo))
        
        # # Удаляем временные файлы
        # os.remove(output_image_path)
        os.remove(image_path)
        
        # Очищаем user_data
        context.user_data.pop('image_path', None)
        context.user_data.pop('text_query', None)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        await update.message.reply_text(f"Произошла ошибка при обработке вашего запроса: {e}.")

def generate_text_response(image_path, text_query: str) -> str:
    """
    Генерация текстового ответа на основе изображения и запроса
    """

    print(text_query, image_path)
    #cmd = ['python', '../apps/plm/generate.py', '--ckpt', '/media/intern/HDD-2TB/plmodel/Perception-LM-1B', '--media_type', 'image', '--media_path', f'"{image_path}"', '--question', f'"{text_query}"']
    cmd = ['python', '../apps/plm/generate.py', 
           '--ckpt', '/media/intern/HDD-2TB/plmodel/Perception-LM-1B', 
           '--media_type', 'image', 
           '--media_path', f'{image_path}',
           '--question', f'"{text_query}"']
    result = subprocess.run(cmd, capture_output = True, text = True)
    return result.stdout + result.stderr



async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления {update}: {context.error}")
    if update.message:
        await update.message.reply_text(f"Произошла ошибка. Пожалуйста, попробуйте еще раз.{update}: {context.error}")

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_error_handler(error_handler)
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    response_text = {"access_token":"eyJjdHkiOiJqd3QiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUlNBLU9BRVAtMjU2In0.JHjYuauPa_wHCcyeOnxDczNdpiMU9H5hP_qQdi4ZQEF1MNRaX3STfMSxpqPjOeFAB7ASOGLNgaCp46dxVngrpUUCM3TK_tc2tuiZpwQOe22NK25xbspvbdmArzOgIbkTUVI67GKRk2LKs_sWtItI5LtY3kQnu7iJSe_KS_0bJ5SRi8fur-dH9VvWNTRhB4jAZwusPMyFpjHCmrR9B_63Tuqy9x3erRAyurPKKMzISuHeOw969aqXkbP-fpmZ8cqE1IFv6XOCRBl54e9iAWOJPi7obHJhkgjky970cjV6JuHNW-yLjkQWXkMwdiZO1O4eBGzsnUpHHLMbD9v4EhDk1g._0qGFdR7v2q1VEMNoLXPRg.4g34nZgHLf40qC2fG_jAIXy_gG2fp057KdPl2igd9xfeoIvnGS8vEMhWQYXTXvuwAOMMgOaRxzt73vVO2ZXq4BEEIKD-YGPfHkHeEIUEV5_ttl23b2dYN1lbphHJlXlRuCy3w0RdTKQa7wbbz0JqpcxQL7Q4VGrocr4PntGaE2K2AG-lVYkX5HQLSY8f708ql2GtqkogK8cNp-m10nEmpbWSY4ERTNO1W4C96ll10mqUdJjzxjoiD4CSzWqIG-04AeToHE0owXN1c2g25P6P4oO-QBacauCqGveLY7KUBOrIrby34xwk1WTTyRNb2Praejp7UWxdIG7itnymSHRMzBGX4H3yY5R5hCHr3MYkmHcw8adXJsHMJiMshbBLPRQ0d-4wBprKTElhDz_DkLCY_pi1TUCxeH7rKWdJ6ps9DfYAS8zkLs85k2PPNpK7z2cTW16Qk5ibj28MuD4Gm5KL8zFuhIIlEuNhoz8vuFw3KIvoeBwBh7ULvB0W7onJ4MtUuzJEJ37LwRwCH_GVnplrY__TtAzuqVpccErYVvWhQ5pc-MfpxXHK5I9W966iCbuNOlrZmh7pkKxTX7_nL4sI2FYm0IOMmDsiQE8aXO5dWz4D1sAol9H-11bFIiAhW7UzUCk6WamsFwtArm9yBqfFFap368nuDrw_DsUrYsdSQ50_ru4IMMMn7pgHWoP_hcBq1p_y_SrK0naJxVJcDzx5Xqkkn1ffazSUqOa6J_1RVVI.Zg6KgaQJOLyUTpIgr65aFmr77dQ5VEHK-JarbEGy2zg","expires_at":1748250408838}
    SALUTE_ACCESS_TOKEN = response_text["access_token"]
    #SALUTE_SPEECH_API_KEY = "ODRlOGJmZGUtM2U2Ni00MWJkLWJkNTQtMWNkNzFlZWIwNzA0OjU1MjA3ZTU3LTljNjktNGY0MS1iMDhlLTNmODI2ZDA5ZjE5Yw=="

    #url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    #payload={
            #'scope': 'SALUTE_SPEECH_PERS'
            #}
    #headers = {
            #'Content-Type': 'application/x-www-form-urlencoded',
                #'Accept': 'application/json',
                #'RqUID': '61b769b0-32b6-41fc-a1bd-402d09d69813',
                    #'Authorization': f'Basic {SALUTE_SPEECH_API_KEY}'
                    #}

    #response = requests.post(url, headers=headers, data=payload, verify=False)


    main()


# reqs
# pip install python-telegram-bot pillow  transformers requests

# start
# python bot.py
