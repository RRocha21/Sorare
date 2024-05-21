from sorare import logger

import gspread
from oauth2client.service_account import ServiceAccountCredentials

class Sheets:

    def __init__(self, credentials=None, file_name=None, sheet_id=None, sheet_name=None):
        if credentials is None and file is None and sheet_id is None and sheet_name is None:
            request_kwargs = {}


        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials_account = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)

        try:
            client = gspread.authorize(credentials_account)
            self.sheet_id = sheet_id
            self.sheet_name = sheet_name
            self.file_name = file_name
            self.client = client
        except:
            logger.error('Failed to connect to Google Sheets!')
            exit(1)


    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.error('Exit Sheets')
    
    async def insert_one(self, data, sheet_name=None):
        try:
            sheet = self.client.open(self.file_name).worksheet(sheet_name)
            ## transform data to list  
            dataList = [data[key] for key in data]
            sheet.append_row(dataList)
        except Exception as e:
            logger.error(f'Failed to insert data to Google Sheets: {e}')
            raise e
    
    async def get_all(self, sheet_name=None):
        try:
            sheet = self.client.open(self.file_name).worksheet(sheet_name)
            data = sheet.get_all_records(expected_headers=['Display Name', 'Player Slug', 'Rarity', 'Card Age', 'Real Age', 'Min Price', 'Last Sale Price', 'Last Sale Date', 'Updated At'])
            formatted_data = []
            for row in data:
                format_data = {
                    'display_name': row['Display Name'],
                    'player_slug': row['Player Slug'],
                    'rarity': row['Rarity'],
                    'card_age': row['Card Age'],
                    'real_age': row['Real Age'],
                    'min_price': row['Min Price'],
                    'last_sale_min_price': row['Last Sale Price'],
                    'last_sale_date': row['Last Sale Date'],
                    'updatedAt': row['Updated At'],
                }
                formatted_data.append(format_data)
            return formatted_data
            
        
        except Exception as e:
            logger.error(f'Failed to get data from Google Sheets: {e}')
            raise e
    
    async def update_one(self, data, player_slug, rarity, card_age, sheet_name=None):
        try:
            sheet = self.client.open(self.file_name).worksheet(sheet_name)
    
            # Find the first occurrence of the specified data
            values = sheet.get_all_values() 
            i = 0
            for row, value in enumerate(values):
                i += 1
                if str(value[1]) == str(player_slug) and str(value[2]) == str(rarity) and int(value[3]) == int(card_age):
                    break
                
            row = i

            sheet.update_cell(row, 6, data['min_price'])
            sheet.update_cell(row, 8, data['last_sale_min_price'])
            sheet.update_cell(row, 10, data['last_sale_date'])
            sheet.update_cell(row, 7, data['1_d_min_price'])
            sheet.update_cell(row, 9, data['1_d_last_sale_min_price'])
            sheet.update_cell(row, 11, data['updatedAt'])
        except Exception as e:
            logger.error(f'Failed to update data to Google Sheets: {e}')
            raise e