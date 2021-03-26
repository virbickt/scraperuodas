from distutils.core import setup

setup(
    name='scraperuodas',
    version='1.0',
    packages=['scraperuodas'],
    url='https://github.com/virbickt/scraperuodas',
    license='MIT License',
    author='Teofilius Virbickas',
    author_email='tvirbickas@gmail.com',
    description='Automatic data collection tool specifically design to collect data from aruodas.lt',
    install_requires=[
        'requests',
        'bs4',
        'pandas',
        'fake_useragent'
    ]
)
