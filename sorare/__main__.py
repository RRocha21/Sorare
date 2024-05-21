import asyncio
from datetime import datetime

from sorare import config, logger
from sorare.provider.auth import Auth
from sorare.provider.graphql import Graphql
from sorare.provider.sheets import Sheets
from urllib.parse import unquote

import time

import json

def format_date(date):
    return date.strftime('%d/%m/%Y %H:%M:%S')

async def main_loop(auth, sheets, graphql):   
    logger.info('Starting main loop')
    
    hashedpwd = await auth.get_hashed()
    
    jwt_token = await auth.login(hashedpwd)

    cards = await graphql.get_user_cards('kidmanxdx', jwt_token)
    
    sheetsData = await sheets.get_all('Kidmanxdx')
    
    for card in cards:
        details = await graphql.get_cards_details(card)
        if details['rarity'] != 'common':
            prices = await graphql.get_cards_prices_info(details['player_slug'], details['rarity'], details['card_age'])
            foundRow = False
            needsUpdate = False
            
            for sheet in sheetsData:
                
                if str(sheet['player_slug']) == str(details['player_slug']) and str(sheet['rarity']) == str(details['rarity']) and int(sheet['card_age']) == int(details['card_age']):
                    foundRow = True
                    time_of_last_update = int(time.mktime(datetime.strptime(sheet['updatedAt'], "%d/%m/%Y %H:%M:%S").timetuple()))
                    
                    if time_of_last_update < int(time.mktime(datetime.now().timetuple())) - 86400:
                        needsUpdate = True
                    break
            if not needsUpdate and foundRow:
                continue
            
            timestamp_of_last_sale_date = int(time.mktime(datetime.strptime(prices['last_sale_date'], "%Y-%m-%dT%H:%M:%SZ").timetuple()))
            updateAt = int(time.mktime(datetime.now().timetuple()))
            if not foundRow:
                data = {
                    'display_name': details['display_name'],
                    'player_slug': details['player_slug'],
                    'rarity': details['rarity'],
                    'card_age': details['card_age'],
                    'real_age': details['real_age'],
                    'min_price': str(prices['min_price']),
                    '1_d_min_price': 0, # '1_d_min_price': prices['min_price'] / sheet['min_price'] - 1 * 100,
                    'last_sale_min_price': str(prices['last_sale_min_price']),
                    '1_d_last_sale_min_price': 0, # '1_d_last_sale_min_price': prices['last_sale_min_price'] / sheet['last_sale_min_price'] - 1 * 100,
                    'last_sale_date': str(format_date(datetime.fromtimestamp(timestamp_of_last_sale_date))),
                    'updatedAt': str(format_date(datetime.fromtimestamp(updateAt))),
                }
                await sheets.insert_one(data, 'Kidmanxdx')
                await asyncio.sleep(10)
            else:
                if sheet['min_price'] == None or sheet['min_price'] == 'None':
                    d_min_price = 0
                else:
                    d_min_price = (prices['min_price'] / (sheet['min_price']))
                    d_min_price = d_min_price - 1
                    logger.info(f'{d_min_price}')
                    d_min_price = round(d_min_price * 100, 2)
                    
                if sheet['last_sale_min_price'] == None or sheet['last_sale_min_price'] == 'None':
                    d_last_sale_min_price = 0
                else:
                    d_last_sale_min_price = (prices['last_sale_min_price'] / (sheet['last_sale_min_price']) ) 
                    d_last_sale_min_price = d_last_sale_min_price - 1
                    d_last_sale_min_price = round(d_last_sale_min_price * 100, 2)
                data = {
                    'min_price': str(prices['min_price']),
                    'last_sale_min_price': str(prices['last_sale_min_price']),
                    'last_sale_date': format_date(datetime.fromtimestamp(timestamp_of_last_sale_date)),
                    '1_d_min_price': d_min_price,
                    '1_d_last_sale_min_price': d_last_sale_min_price,
                    'updatedAt': format_date(datetime.fromtimestamp(updateAt)),
                }
                await sheets.update_one(data, details['player_slug'], details['rarity'], details['card_age'], 'Kidmanxdx')
                await asyncio.sleep(10)

async def main():
    try:
        while True:
            async with Auth(
                email=config['main']['email'],
                password=config['main']['password'],
            ) as auth, Sheets(
                credentials=config['sheets']['credentials'],
                sheet_id=config['sheets']['sheet_id'],
                sheet_name=config['sheets']['sheet_name'],
                file_name=config['sheets']['file_name'],
            ) as sheets, Graphql() as graphql:
                await main_loop(auth, sheets, graphql)
            
    except KeyboardInterrupt:
        exit('Bye~')


if __name__ == '__main__':
    asyncio.run(main())
