import asyncio
from aiohttp import ClientSession 
import json

class Inspect:
    base_url = 'http://192.168.3.31:8080/'

    def __init__(self, request_interval):
        self.session = ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def inspect_one(self, link):
        url = f'{self.base_url}?url={link}'
        max_retries = 3  # Number of maximum retries

        for retry in range(max_retries):
            try:
                async with self.session.get(url, timeout=5) as response:
                    if response is None or response.status != 200:
                        return None

                    data = await response.json()
                    if 'iteminfo' not in data:
                        return None
                    else:
                        return data['iteminfo']['floatvalue']
            except asyncio.TimeoutError:
                if retry < max_retries - 1:
                    print(f"Timeout occurred. Retrying ({retry + 1}/{max_retries})...")
                else:
                    print("Maximum retries exceeded. Unable to complete request.")
                    return None
            except json.JSONDecodeError as e:
                return None
            
    async def inspect_many(self, items):
        try: 
            links = [{"link": item['correct_link']} for item in items]

            url = f'{self.base_url}bulk'
            
            async with self.session.post(url, json={"links": links}, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    for item_data in data:
                        item_from_data = data[item_data]
                        if 'floatvalue' in item_from_data:
                            for item in items:
                                if item['listing_id'] == item_from_data['m']:
                                    item['float_value'] = float(item_from_data['floatvalue'])

                    return items
                else:
                    print(f'Failed to inspect many items: {response.status}')
                    return None
        except Exception as e:
            print(f'Failed to inspect many items: {e}')
            return None