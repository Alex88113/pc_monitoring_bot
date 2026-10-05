import asyncio

import psutil
import httpx
from loguru import logger

from app.bot.services.monitoring import (
ProcessorMonitoring,
Disk,
Memory,
Network,
send_request
)

class SystemIntegration:
    def __init__(
           self,
           processor: ProcessorMonitoring,
           disk: Disk,
           memory: Memory,
           network: Network,
           url: str
    ) -> None:
        self.processor = processor
        self.disk = disk
        self.memory = memory
        self.network = network
        self.url = url

    async def get_info_about_processor(self) -> str:
        async with httpx.AsyncClient() as client:
            root = await send_request(client, "GET", self.url)
        return await self.processor.get_data_processor(root, "/intelcpu/0/temperature/8")

    async def get_metrics_disk(self) -> str:
        return await asyncio.to_thread(self.disk.get_info_disk)

    async def get_data_memory(self) -> str:
        return await self.memory.get_memory_usage()

    async def get_network_metrics(self) -> str:
        return await self.network.get_info_network()

async def main() -> None:
    url: str = 'http://localhost:8085/data.json'

    processor = ProcessorMonitoring()
    memory = Memory()
    disk = Disk()
    network = Network()

    system_obj = SystemIntegration(
        processor,
        disk,
        memory,
        network,
        url
    )

    logger.debug(await system_obj.get_info_about_processor())
    logger.debug(await system_obj.get_metrics_disk())
    logger.debug(await system_obj.get_data_memory())
    logger.debug(await system_obj.get_network_metrics())

if __name__ == "__main__":
    asyncio.run(main())