from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='steam2buff',
    version='0.4.1',
    python_requires='>=3.7',
    url='https://github.com/hldh214/steam2buff',
    license='Unlicense',
    description='Yet another steam trade bot w/ buff.163.com',
    long_description=long_description,
    packages=['steam2buff'],
    install_requires=[
        'loguru==0.*',
        'aiohttp==3.*',
        'aiohttp_socks==0.*',
    ],
    author='Jim',
    author_email='hldh214@gmail.com',
)