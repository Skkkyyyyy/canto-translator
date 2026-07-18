import requests
import asyncio 
import wikipediaapi
import re 
import pandas as pd 

async def main():
    wiki_wiki = wikipediaapi.Wikipedia(
        user_agent='canto(sally1152005@gmail.com)', 
        language='en',
        extract_format = wikipediaapi.ExtractFormat.WIKI
    )

    page = wiki_wiki.page('Hong Kong slang')
    if page.exists():
        print(page.text)
    else:
        print("Page not found")

    lines = page.splitlines()

asyncio.run(main())
