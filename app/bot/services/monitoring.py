import asyncio
import time
from typing import cast, Any

import httpx
import psutil
from loguru import logger


class ProcessorMonitoring:
    async def get_data_processor(
           self,
           node: dict[str, str | int],
           sensor_id: str
    ) -> str:
        data = await asyncio.to_thread(self._fetch_data_processor, node, sensor_id)
        return self._formatter_data(data)

    def _find_sensor(
        self, node: dict[str, str | int], sensor_id: str
    ) -> dict[str, str | int] | None:
        if node.get("SensorId") == sensor_id:
            return node

        children = cast(list[dict[str, str | int]], node.get("Children", []))
        for child in children:
            result = self._find_sensor(child, sensor_id)
            if result is not None:
                return result

        return None

    def _fetch_data_processor(
        self,
        node: dict[str, int | str],
        sensor_id: str,
        interval: int = 1
    ) -> dict[str, str | int]:
        time.sleep(interval)
        workload2 = psutil.cpu_percent()

        count_logical_cores = psutil.cpu_count()
        count_cores = psutil.cpu_count(logical=False)

        freq_cores = psutil.cpu_freq(percpu=True)
        average_speed = [mgz.current for mgz in freq_cores]

        freq_avg = sum(average_speed) / len(average_speed) if average_speed else 0.0

        temperature_node = self._find_sensor(node, sensor_id)
        if temperature_node is None:
            temperature = "Неопределена"
        else:
            temperature = str(temperature_node["Value"]).replace(",", ".").split()[0]

        return {
            "cpu_percent": f"{workload2}%",
            "cores_physical": count_cores or 0,
            "cores_logical": count_logical_cores,
            "freq_current": f"{freq_avg:.0f}MGz",
            "temperature": temperature,
        }

    def _formatter_data(self, data: dict[str, str | int]) -> str:
        lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━"]
        lines.append("🖥️  ПРОЦЕССОР")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")

        lines.append(f"⚡ Загруженность CPU: {data.get('cpu_percent')}")
        lines.append(f"🧩 Физических ядер: {data.get('cores_physical')}")
        lines.append(f"🧵 Логических ядер: {data.get('cores_logical')}")
        lines.append(f"📊 Частота: {data.get('freq_current')}")

        temp = data.get("temperature")
        if temp == "Неопределена":
            lines.append("🌡️ Температура: недоступна")
        else:
            lines.append(f"🌡️ Температура: {temp}°C")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        return "\n".join(lines)


class Memory:
    async def get_memory_usage(self) -> str:
        return await asyncio.to_thread(self._formatted_data_memory)

    def _fetch_data_memory(self) -> dict[str, str]:
        virtual_memory = psutil.virtual_memory()
        return {
            "Всего": f"{virtual_memory.total / (1024**3):.2f} ГБ",
            "Используется": f"{virtual_memory.used / (1024**3):.2f} ГБ",
            "Свободно": f"{virtual_memory.available / (1024**3):.2f} ГБ",
            "Процент использования": f"{virtual_memory.percent}%",
        }

    def _formatted_data_memory(self) -> str:
        data = self._fetch_data_memory()

        lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━"]
        lines.append("💾  ПАМЯТЬ")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")

        lines.append(f"📦 Всего: {data.get('Всего')}")
        lines.append(f"📥 Используется: {data.get('Используется')}")
        lines.append(f"📤 Свободно: {data.get('Свободно')}")
        lines.append(f"📊 Загрузка: {data.get('Процент использования')}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)


class Disk:
    def get_info_disk(self) -> str:
        data = self._fetch_data_about_disk()
        return self._formatter_info_disk(data)

    def _formatter_info_disk(self, data_disk: list[dict[str, str]]) -> str:
        if not data_disk:
            return "❌ Диски не найдены"

        lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━"]
        lines.append("💿  ДИСКИ")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")

        for i, value in enumerate(data_disk, start=1):
            lines.append(f"📁 Раздел #{i}: {value['mountpoint']}")
            lines.append(f"💠 Объём: {value['Общий объём диска']}")
            lines.append(f"📥 Используется: {value['Используется']}")
            lines.append(f"📤 Свободно: {value['Свободно']}")
            lines.append(f"📊 Занято: {value['Занято']}")

            if i < len(data_disk):
                lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    def _fetch_data_about_disk(self) -> list[dict[str, str]]:
        disk_part = psutil.disk_partitions()
        info_about_disk = []

        for data in disk_part:
            if data.fstype in ("tmpfs", "devtmpfs", "squashfs", "overlay"):
                continue
            try:
                result = psutil.disk_usage(data.mountpoint)
                info_about_disk.append(
                    {
                        "mountpoint": data.mountpoint,
                        "Общий объём диска": f"{result.total / (1024**3):.2f} GB",
                        "Свободно": f"{result.free / (1024**3):.2f} GB",
                        "Занято": f"{result.percent}%",
                        "Используется": f"{result.used / (1024**3):.2f} GB",
                    }
                )
            except (PermissionError, FileNotFoundError, OSError, psutil.Error) as error:
                logger.error(f"Возникла ошибка: {error}")
                continue

        return info_about_disk


class Network:
    async def get_info_network(self) -> str:
        return await asyncio.to_thread(self._formatter_data)

    def _fetch_data_network(self, interval: int = 10) -> dict[str, int | float]:
        data_network = psutil.net_io_counters()

        bytes_sent1 = data_network.bytes_sent
        bytes_recv1 = data_network.bytes_recv
        packets_sent1 = data_network.packets_sent
        packets_recv1 = data_network.packets_recv
        time_1 = time.monotonic()
        time.sleep(interval)

        new_data_network = psutil.net_io_counters()
        bytes_sent2 = new_data_network.bytes_sent
        bytes_recv2 = new_data_network.bytes_recv
        packets_sent2 = new_data_network.packets_sent
        packets_recv2 = new_data_network.packets_recv

        time_2 = time.monotonic()

        delta_sent = bytes_sent2 - bytes_sent1
        delta_recv = bytes_recv2 - bytes_recv1

        delta_packets_sent = packets_sent2 - packets_sent1
        delta_packets_recv = packets_recv2 - packets_recv1

        real_interval = time_2 - time_1

        speed_sent = delta_sent / real_interval
        speed_recv = delta_recv / real_interval
        speed_packets_sent = delta_packets_sent / real_interval
        speed_packets_recv = delta_packets_recv / real_interval

        return {
            "bytes_sent": delta_sent,
            "bytes_recv": delta_recv,
            "speed_sent": speed_sent,
            "speed_recv": speed_recv,
            "packets_sent": delta_packets_sent,
            "packets_recv": delta_packets_recv,
            "speed_packets_sent": speed_packets_sent,
            "speed_packets_recv": speed_packets_recv,
        }

    def _formatter_data(self) -> str:
        data = self._fetch_data_network()

        bytes_sent = self._human_bytes(data.get("bytes_sent", 0))
        bytes_recv = self._human_bytes(data.get("bytes_recv", 0))
        speed_sent = self._human_speed(data.get("speed_sent", 0))
        speed_recv = self._human_speed(data.get("speed_recv", 0))
        packets_sent = data.get("packets_sent", 0)
        packets_recv = data.get("packets_recv", 0)

        lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━"]
        lines.append("🌐  СЕТЬ")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")

        lines.append(f"📤 Отправлено: {bytes_sent}")
        lines.append(f"📥 Получено: {bytes_recv}")
        lines.append(f"⬆️ Скорость ↑: {speed_sent}")
        lines.append(f"⬇️ Скорость ↓: {speed_recv}")
        lines.append(f"📦 Пакетов отправлено: {packets_sent}")
        lines.append(f"📦 Пакетов получено: {packets_recv}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    @staticmethod
    def _human_bytes(num: int | float) -> str:
        for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
            if abs(num) < 1024.0:
                return f"{num:.2f} {unit}"
            num /= 1024.0
        return f"{num:.2f} ПБ"

    @staticmethod
    def _human_speed(num: int | float) -> str:
        for unit in ("Б/с", "КБ/с", "МБ/с", "ГБ/с"):
            if abs(num) < 1024.0:
                return f"{num:.2f} {unit}"
            num /= 1024.0
        return f"{num:.2f} ТБ/с"


async def send_request(client: httpx.AsyncClient, method: str, url: str) -> dict[str, Any]:
    response = await client.request(method, url)
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
