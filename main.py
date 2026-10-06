import asyncio

import httpx

async def send_request(client: httpx.AsyncClient, method: str, url: str):
    response = await client.request(method, url)
    return response.json()

def find_sensor(node: dict, sensor_id: str):
    if node.get("SensorId") == sensor_id:
        return node

    for child in node.get("Children", []):
        result = find_sensor(child, sensor_id)
        if result is not None:
            return result

    return None

async def main() -> None:
    url: str = 'http://localhost:8085/data.json'

    async with httpx.AsyncClient() as client:
        result_send = await send_request(client, "GET", url)
        root = result_send
        node = find_sensor(root, "/intelcpu/0/temperature/8")
        if node:
            temperature = node.get('Value').replace(",", ".").split()[0]
            print(f"Температура CPU: {temperature}°C")

if __name__ == "__main__":
    asyncio.run(main())