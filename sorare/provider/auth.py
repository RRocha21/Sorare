import asyncio
import re

import json

import random

import urllib.parse

import bcrypt

import aiohttp

from sorare import logger

from graphqlclient import GraphQLClient

from python_graphql_client import GraphqlClient

import asyncio

SignIn = """
mutation SignInMutation($input: signInInput!) {
    signIn(input: $input) {
        currentUser {
            slug
        }
        jwtToken(aud: "%s") {
            token
            expiredAt
        }
        otpSessionChallenge
        errors {
            message
        }
    }
}
""" 

class Auth:
    base_url = 'https://api.sorare.com/api/v1/users'

    def __init__(self, email, password):
        self.email = email
        self.password = password
        
        self.session = aiohttp.ClientSession()
        
        self.client = GraphqlClient(
            endpoint = 'https://api.sorare.com/federation/graphql', 
            headers={
            'APIKEY': 'e7009de7a37e4ca327900f488e4e9c3ec8d104725e8b442e6decd8a52c6495b4090e2b7d9fb7c25fff81848af46d6ccb58fbb728351f2bb479f3c3e323dsr128'
            }
        )
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        pass
        
    async def get_hashed(self):
        url = f'{self.base_url}/{self.email}'
        try:
            async with self.session.get(url) as response:
                data = await response.json()
                salt = data['salt']
                hashed_pwd = bcrypt.hashpw(self.password.encode(), salt.encode())
                return hashed_pwd
                
        except Exception as e:
            logger.error('Failed to get salt: %s', e)
            raise e
        
    async def login(self, hashed_pwd):
        input_variables = {
            'input': {
                'email': self.email,
                'password': hashed_pwd.decode(),
            }
        }
        try:
            response = await self.client.execute_async(query=SignIn, variables=input_variables)
            token = response['data']['signIn']['jwtToken']['token']
            return token
        except Exception as e:
            logger.error(f'Failed to sign in: {e}')
            raise e
        