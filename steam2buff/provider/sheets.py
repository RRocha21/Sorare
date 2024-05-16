from aiohttp import ClientSession 
import json

class Sheets:
    base_url = 'http://192.168.3.31:8000'

    def __init__(self, request_interval):
        self.session = ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get_steam_links(self):
        url = f'{self.base_url}/steam_links'
        async with self.session.get(url, timeout=30) as response:
            try:
                if response is None or response.status != 200:
                    return None

                data = await response.json()
                return data
            except json.JSONDecodeError as e:
                return None
