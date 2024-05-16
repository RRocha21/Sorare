import asyncio
from datetime import datetime

from steam2buff import config, logger
from steam2buff.provider.steam import Steam
from steam2buff.provider.sheets import Sheets
from steam2buff.provider.inspect import Inspect
from steam2buff.provider.rates import Rates
from steam2buff.provider.postgres import Postgres

from urllib.parse import unquote

import time

import json

async def main_loop(steam, sheets, inspect, rates, postgres):    
    await steam.get_proxy_list()

    psql_exchange_rates = await postgres.find_exchange_rate()

    exchange_rates_json = psql_exchange_rates.get('rates')  # Extracting exchange rates dictionary
    last_updated_str = psql_exchange_rates.get('updatedat')        # Extracting last updated timestamp
    last_updated = datetime.strptime(last_updated_str, '%Y-%m-%dT%H:%M:%S.%f')

    exchange_rates = json.loads(exchange_rates_json)
    
    if (datetime.now() - last_updated).total_seconds() > 43200:
        new_exchange_rates = await rates.get_exchanges_rates_from_api()
        psql_rate = {
            'id': 1,
            'rates': new_exchange_rates,
            'updatedAt': datetime.now(),
        }
        await postgres.update_rates(psql_rate)   
        exchange_rates = new_exchange_rates 
    i = 0
    while True:
        
        if i > 1:
            logger.info(f'Iteration {i - 1}:')
            logger.info(f'Total Skins to check: {total}')
            logger.info(f'Total Failure: {count}')
            logger.info(f'Total Time: {end_time - start_time} seconds')
            
        i = 2
        start_time = time.time()
        count = 0;
        total = 0;
        sheets_data = await sheets.get_steam_links()
        
        for _ in range(5):
            for sheet_data in sheets_data:
                total += 1
                steam_link = sheet_data.get('link')
                max_float = sheet_data.get('maxfloat')
                max_price = sheet_data.get('maxprice')
                    
                market_hash = unquote(steam_link.split("/")[-1])

                listings = await steam._web_listings(market_hash)
                
                if listings is None:
                    count += 1
                    continue
                
                check_floats = []
                
                for listing in listings:
                    listing_id = listing['listing_id']
                    asset_id = listing['asset_id']
                    listing_price = listing['final_price']
                    listing_link = listing['market_action_link']
                    currency = listing['currency_id']
                        
                    correct_link = listing_link.replace('%listingid%', str(listing_id)).replace('%assetid%', str(asset_id))
                    # Check if listing is the last one of the listings 

                    if listing_price == 0.0 or listing_price is None or listing_price == 0 or listing_price == '0':
                        correct_price = 0.0
                        currency = 'SOLD'

                    else: 
                        if currency != 'EUR':
                            correct_price = await rates.get_correct_price(exchange_rates, currency, listing_price)
                            if correct_price is None:
                                correct_price = 0.0
                                currency = ''
                            else:
                                currency = 'EUR'
                        else:        
                            correct_price = listing_price 

                    if (correct_price <= max_price):
                        
                        check_floats.append({
                            'listing_id': listing_id,
                            'correct_price': correct_price,
                            'link': steam_link,
                            'currency': currency,
                            'correct_link': correct_link,
                            'max_float': max_float,
                        })
                
                if check_floats:
                    response_inspect = await inspect.inspect_many(check_floats)

                    if response_inspect is None:
                        count += 1
                        continue
                    for item in response_inspect:
                        if item['float_value'] is None:
                            count += 1
                            continue
                        if item['float_value'] <= item['max_float']:
                            item_to_psql = {
                                'id': item['listing_id'],
                                'price': item['correct_price'],
                                'currency': item['currency'],
                                'link': item['link'],
                                'float_value': item['float_value'],
                                'updatedAt': datetime.now(),
                            }
                            await postgres.insert_one(item_to_psql)

        end_time = time.time()      


async def main():
    try:

        while True:
            async with Steam(
                game_appid=config['main']['game_appid'],
                request_interval=config['steam']['request_interval'],
            ) as steam, Sheets(
                request_interval=10,
            ) as sheets, Inspect(
                request_interval = 10,
            ) as inspect, Rates(
                request_interval = 10,
            ) as rates, Postgres(
                request_interval = 10,
            ) as postgres:
                await main_loop(steam, sheets, inspect, rates, postgres)
            
    except KeyboardInterrupt:
        exit('Bye~')


if __name__ == '__main__':
    asyncio.run(main())
