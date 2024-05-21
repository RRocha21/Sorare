
from sorare import logger

from graphqlclient import GraphQLClient
from python_graphql_client import GraphqlClient

import json

AllCardsFromUser = """
query AllCardsFromUser($slug: String!, $cursor: String) {
    user(slug: $slug) {
        paginatedCards(after: $cursor) {
            nodes {
                slug
            }
            pageInfo {
                endCursor
            }
        }
    }
}
"""

GetFootballCardsPricesInfo = """
query GetFootballCardsPricesInfo($playerSlug: [String!], $rarity: [Rarity!], $age: Int!, $cursor: String) {
    allCards (playerSlugs : $playerSlug, rarities:$rarity, age:$age, owned:true, after: $cursor) {
        nodes {
            liveSingleSaleOffer {
				receiverSide {
                    wei
                    fiat {
                        eur
                    }
                }
            }
            notContractOwners {
                amounts {
                    eur
                }
                price
                from
            }
        }
        pageInfo {
            endCursor
        }
    }
}
"""

GetFootballCardsDetails = """
query GetFootballCardsDetails($slug: [String!]){
	allCards(slugs: $slug) {
        nodes{
            age
            rarity
            player {
                displayName
                slug
                age
            }
        }
    }
}
"""


class Graphql:
    base_url = 'https://api.sorare.com/federation/graphql'

    def __init__(self):
        self.client = GraphqlClient(endpoint=self.base_url)
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.session.close()
        pass
        
    async def get_user_cards(self, slug, jwt_token):
        headers = {
            'Authorization': f'Bearer {jwt_token}'
            
        }   
        cursor = None
        cards = []
        try:
            while True:
                data = await self.client.execute_async(
                    query=AllCardsFromUser,
                    variables={
                        'slug': slug,
                        'cursor': cursor
                    },
                    headers={
                        'APIKEY': 'e7009de7a37e4ca327900f488e4e9c3ec8d104725e8b442e6decd8a52c6495b4090e2b7d9fb7c25fff81848af46d6ccb58fbb728351f2bb479f3c3e323dsr128'
                    }
                )
                cursor = data['data']['user']['paginatedCards']['pageInfo']['endCursor']
                for card in data['data']['user']['paginatedCards']['nodes']:
                    cards.append(card['slug'])
                if not cursor:
                    break
            return cards
        except Exception as e:
            logger.error(f'Failed to get user cards: {e}')
            raise e
        
    async def get_cards_details(self, slug):
        try:
            logger.info(f'Getting cards details for: {slug}')
            data = await self.client.execute_async(
                query=GetFootballCardsDetails,
                variables={
                    'slug': slug
                },
                headers={
                    'APIKEY': 'e7009de7a37e4ca327900f488e4e9c3ec8d104725e8b442e6decd8a52c6495b4090e2b7d9fb7c25fff81848af46d6ccb58fbb728351f2bb479f3c3e323dsr128'
                }
            )
            data = data['data']['allCards']['nodes']
            if not data:
                return None
            card_age = data[0]['age']
            rarity = data[0]['rarity']
            display_name = data[0]['player']['displayName']
            player_slug = data[0]['player']['slug']
            real_age = data[0]['player']['age']

            details = {
                'card_age': card_age,
                'real_age': real_age,
                'rarity': rarity,
                'display_name': display_name,
                'player_slug': player_slug
            }
            return details
        except Exception as e:
            logger.error(f'Failed to get cards details: {e}')
            raise e
    
    async def get_cards_prices_info(self, player_slug, rarity, age):
        cursor = None
        cards = []
        min_price = None
        last_sale_min_price = None
        last_sale_date = None
        try:
            if rarity != 'common':
                while True:
                    data = await self.client.execute_async(
                        query=GetFootballCardsPricesInfo,
                        variables={
                            'playerSlug': [player_slug],
                            'rarity': [rarity],
                            'age': age,
                            'cursor': cursor
                        },
                        headers={
                            'APIKEY': 'e7009de7a37e4ca327900f488e4e9c3ec8d104725e8b442e6decd8a52c6495b4090e2b7d9fb7c25fff81848af46d6ccb58fbb728351f2bb479f3c3e323dsr128'
                        }
                    )
                    cursor = data['data']['allCards']['pageInfo']['endCursor']
                    for card in data['data']['allCards']['nodes']:
                        if card['liveSingleSaleOffer']:
                            if not min_price:
                                min_price = card['liveSingleSaleOffer']['receiverSide']['fiat']['eur']
                            else:
                                if min_price > card['liveSingleSaleOffer']['receiverSide']['fiat']['eur']:
                                    min_price = card['liveSingleSaleOffer']['receiverSide']['fiat']['eur']
                        if card['notContractOwners']:
                            for owner in card['notContractOwners']:
                                if owner['amounts']:
                                    if not last_sale_min_price:
                                        last_sale_min_price = owner['amounts']['eur']
                                        last_sale_date = owner['from']
                                    else:
                                        if last_sale_date < owner['from']:
                                            last_sale_min_price = owner['amounts']['eur']
                                            last_sale_date = owner['from']
                    if not cursor:
                        break
            if last_sale_min_price:
                last_sale_min_price = last_sale_min_price / 100
            return {
                'min_price': min_price,
                'last_sale_min_price': last_sale_min_price,
                'last_sale_date': last_sale_date
            }
        except Exception as e:
            logger.error(f'Failed to get cards prices info: {e}')
            raise e