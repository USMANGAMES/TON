import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
import aiohttp
import matplotlib.pyplot as plt
from io import BytesIO
from aiogram.types import BufferedInputFile
from dotenv import load_dotenv
import os

load_dotenv()

# Загружаем токены
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CMC_API_KEY = os.getenv('CMC_API_KEY')
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')



# 🔐 Твои ключи
TELEGRAM_BOT_TOKEN = '8406350509:AAETYDxyUqJiamI3mUcFegns-726ioqf9ig'
CMC_API_KEY = '3ca58bdc-75fc-4df9-9767-16287f7d1201'

COINGECKO_API_KEY = "CG-CrGiNQVuiGemtqNUJFjhoP1F"

# 🤖 Создаём экземпляр бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Глобальная переменная для хранения предыдущей цены
last_ton_price = None

# Получаем курс USD к UZS
async def get_usd_to_uzs():
    url = 'https://open.er-api.com/v6/latest/USD'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            print("Ответ от open.er-api.com:", data)  # Диагностика
            try:
                return data['rates']['UZS']
            except Exception as e:
                print('Ошибка получения курса USD/UZS:', e)
                return None

# Получение цены TON (асинхронно)
async def get_ton_price():
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    params = {'symbol': 'TON', 'convert': 'USD'}
    headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            data = await response.json()
            try:
                price = data['data']['TON']['quote']['USD']['price']
                return round(price, 2)
            except Exception as e:
                print('Ошибка:', e)
                return None

# 📩 Команда /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("👋 Привет! \nНапиши /ton чтобы узнать цену Toncoin (TON)\n/chart чтобы увидеть график. \n/ton_predict - прогноз цены")

# 💰 Команда /ton
@dp.message(Command("ton"))
async def ton_price(message: Message):
    price_usd = await get_ton_price()
    usd_to_uzs = await get_usd_to_uzs()
    if price_usd and usd_to_uzs:
        price_uzs = round(price_usd * usd_to_uzs, 0)
        await message.answer(
            f"💸 Актуальная цена TON:\n"
            f"• {price_usd}$\n"
            f"• {price_uzs} сум\n"
            
        )
    else:
        await message.answer("❌ Не удалось получить цену TON или курс USD/UZS. Попробуй позже.")

# Команда /ton_predict
@dp.message(Command("ton_predict"))
async def ton_predict(message: Message):
    global last_ton_price
    current_price = await get_ton_price()
    if current_price is None:
        await message.answer("❌ Не удалось получить цену TON. Попробуй еще раз.")
        return

    if last_ton_price is None:
        last_ton_price = current_price
        await message.answer("Недостаточно данных для прогноза. Попробуй еще раз.")
        return

    if current_price > last_ton_price:
        predicted = round(current_price * 1.01, 2)
        await message.answer(f"📈 Предполагается рост! Через 5 минут цена может быть около ${predicted}")
    elif current_price < last_ton_price:
        predicted = round(current_price * 0.99, 2)
        await message.answer(f"📉 Возможен спад. Цена может упасть до ${predicted}")
    else:
        predicted = current_price
        await message.answer(f"⚖️ Цена стабильна. Через 5 минут будет примерно ${predicted}")

    last_ton_price = current_price  # Обновляем последнюю цену

@dp.message(Command("chart"))
@dp.message(Command("range"))
async def ton_range(message: Message):
    url = "https://api.coingecko.com/api/v3/coins/the-open-network/market_chart"
    params = {"vs_currency": "usd", "days": "1"}
    headers = {"x-cg-pro-api-key": COINGECKO_API_KEY}  # можно убрать

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Ошибка CoinGecko: {response.status} — {error_text}")
                await message.answer("❌ Не удалось получить данные TON.")
                return
            data = await response.json()

    prices = data.get("prices")
    if not prices:
        await message.answer("❌ Нет данных о цене TON.")
        return

    price_values = [point[1] for point in prices]
    ton_min = round(min(price_values), 2)
    ton_max = round(max(price_values), 2)

    await message.answer(
        f"📊 Диапазон TON за 24 часа:\n"
        f"🔻 Минимум: ${ton_min}\n"
        f"🔺 Максимум: ${ton_max}"
    )


# 🚀 Запуск бота
async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

