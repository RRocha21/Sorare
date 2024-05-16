from aiohttp import ClientSession

import re
import json

class Postgres:
    base_url = 'http://192.168.3.31:8000'

    csrf_pattern = re.compile(r'name="csrf_token"\s*content="(.+?)"')

    def __init__(self, request_interval):
        self.session = ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def inspect_one(self, link):
        url = f'{self.base_url}?url={link}'
        async with self.session.get(url, timeout=30) as response:
            try:
                if response is None or response.status != 200:
                    return None

                data = await response.json()
                if 'iteminfo' not in data:
                    return None
                else:
                    return data['iteminfo']['floatvalue']
            except json.JSONDecodeError as e:
                return None
        
    async def insert_one(self, document, max_points=25):
        try:
            id = int(document["id"])
            not_rounded_price = document["price"]
            price = round(float(not_rounded_price), 2)
            currency = document["currency"]
            link = document["link"]
            float_value = round(float(document["float_value"]), 5)
            updatedAt = document["updatedAt"].strftime('%Y-%m-%dT%H:%M:%S.%f')
            
            url = f'{self.base_url}/steam2buff'
            
            async with self.session.post(url, params={
                'id': id,
                'price': price,
                'currency': currency,
                'link': link,
                'float_value': float_value,
                'updatedAt': updatedAt
            }) as response:
                response.raise_for_status()
            
        except Exception as e:
            print(f'Failed to insert document into PostgreSQL: {e}')

    async def update_rates(self, document, max_points=50):
        try:
            id = document['id']
            rates = json.dumps(document['rates'])
            updatedAt = document["updatedAt"].strftime('%Y-%m-%dT%H:%M:%S.%f')  # Convert datetime to ISO 8601 formatted string

            url = f'{self.base_url}/exchange_rates'

            async with self.session.post(url, params = {
                'rates': rates,
                'updatedAt': updatedAt
            }) as response:
                response.raise_for_status()
            
        except Exception as e:
            print(f'Failed to insert document into PostgreSQL: {e}')
            
    async def find_exchange_rate(self):
        try:
            id = 1
            
            url = f'{self.base_url}/exchange_rates'
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return data[0]
        except Exception as e:
            print(f'Failed to find exchange rate in PostgreSQL: {e}')
