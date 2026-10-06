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
        lines = ""

        if data.get("temperature") == "Неопределена":
            lines += "Температура недоступна"
        else:
            lines += f"Загруженность CPU: {data.get('cpu_percent')}\n"
            lines += f"Количество физических ядер: {data.get('cores_physical')}\n"
            lines += f"Количество логических ядер: {data.get('cores_logical')}\n"
            lines += f"Текущая частота работы процессора = {data.get('freq_current')}\n"
            lines += f"Температура процессора: {data.get('temperature')}°C"

        return lines


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
        lines = "--------------------------------\n"
        lines += f"Всего: {data.get('Всего')}\n"
        lines += f"Свободно: {data.get('Свободно')}\n"
        lines += f"Используется: {data.get('Используется')}\n"
        lines += f"Процент использования = {data.get('Процент использования')}\n"
        lines += "--------------------------------\n"
        return lines


class Disk:
    def get_info_disk(self) -> str:
        data = self._fetch_data_about_disk()
        return self._formatter_info_disk(data)

    def _formatter_info_disk(self, data_disk: list[dict[str, str]]) -> str:
        lines = ["-----------------------------"]
        for value in data_disk:
            lines.append(f"Точка монтирования: {value['mountpoint']}")
            lines.append(f"Общий объём диска: {value['Общий объём диска']}")
            lines.append(f"Свободно: {value['Свободно']}")
            lines.append(f"Занято {value['Занято']}")
            lines.append(f"Используется: {value['Используется']}")
        lines.append("----------------------------")

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
        lines = "----------------------------------\n"
        lines += f"Отправленные байты = {data.get('bytes_sent')}\n"
        lines += f"Полученные байты = {data.get('bytes_recv')}\n"
        lines += f"Скорость отправленных данных: {data.get('speed_sent')}\n"
        lines += f"Скорость полученных данных = {data.get('speed_recv')}\n"
        lines += f"Время отправленных пакето: {data.get('packets_sent')}\n"
        lines += f"Время прихода данных = {data.get('packets_recv')}\n"
        lines += f"speed_packets_sent: {data.get('speed_packets_sent')}\n"
        lines += f"speed_packets_recv: {data.get('speed_packets_recv')}\n"
        lines += "----------------------------------\n"
        return lines


async def send_request(client: httpx.AsyncClient, method: str, url: str) -> dict[str, Any]:
    response = await client.request(method, url)
    response.raise_for_status()
    return cast(dict[str, Any], response.json())
