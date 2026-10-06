import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import httpx
from loguru import logger

from app.bot.services.monitoring import (
    ProcessorMonitoring,
    Disk,
    Memory,
    Network,
    send_request
)

dp = Dispatcher()


@logger.catch
@dp.message(Command("start"))
async def any_message(message: Message):
    await message.answer("Привет!\nЯ бот для мониторинга твоего пк")

@logger.catch
@dp.message(Command("cpu"))
async def get_metrics_processor(message: Message):
    processor_obj = ProcessorMonitoring()
    async with httpx.AsyncClient() as client:
        try:
            root = await send_request(client, "GET", "http://localhost:8085/data.json")
            processor = ProcessorMonitoring()
            result = await processor.get_data_processor(root, "/intelcpu/0/temperature/8")
        except httpx.ConnectError as error:
            logger.error(f"Не удалось установить соединение: {error}")
            raise

    await message.answer(result)

@logger.catch
@dp.message(Command("disk"))
async def get_metrics_disk(message: Message):
    disk_obj = Disk()
    await message.answer(disk_obj.get_info_disk())

@logger.catch
@dp.message(Command("memory"))
async def get_metrics_memory(message: Message):
    memory_obj = Memory()
    await message.answer(await memory_obj.get_memory_usage())

@logger.catch
@dp.message(Command("network"))
async def get_metrics_network(message: Message):
    network_obj = Network()
    await message.answer(await network_obj.get_info_network())
