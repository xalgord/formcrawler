import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time

visited_urls = set()
max_depth = 3  # Maximum recursion depth
concurrent_requests = 10  # Number of concurrent requests
crawl_delay = 1  # Delay between requests to avoid overloading the server

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, allow_redirects=True, timeout=10) as response:
                if response.status == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                    return await response.text()
                else:
                    return None
        except Exception as e:
            return None

def get_internal_links(url, html_content):
    internal_links = set()
    soup = BeautifulSoup(html_content, 'html.parser')
    for link in soup.find_all('a', href=True):
        next_url = urljoin(url, link['href'])
        parsed_next_url = urlparse(next_url)
        if parsed_next_url.scheme and parsed_next_url.netloc == urlparse(url).netloc:
            internal_links.add(next_url)
    return internal_links

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

async def crawl(url, depth):
    if depth <= max_depth and url not in visited_urls and is_valid_url(url):
        visited_urls.add(url)
        html_content = await fetch(url)
        if html_content:
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                forms = soup.find_all('form')
                input_texts = soup.find_all('input', {'type': 'text'})
                if forms or input_texts:
                    print("\033[92mForm Found\033[0m:", url)  # Green color for "Form Found" message
                internal_links = get_internal_links(url, html_content)
                await asyncio.gather(*[crawl(link, depth + 1) for link in internal_links])
            except Exception as e:
                print(f"\033[91mError parsing content from URL:\033[0m {url}")  # Red color for error message
                print(f"\033[91mError:\033[0m {e}")
                print(f"\033[93mContent:\033[0m {html_content[:500]}...")  # Yellow color for content preview

async def main():
    urls_file = input("Enter the path to the file containing URLs: ")
    with open(urls_file, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    await asyncio.gather(*[crawl(url, 0) for url in urls if is_valid_url(url)])

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print("\033[94mExecution time:\033[0m", round(time.time() - start_time, 2), "seconds")  # Blue color for execution time
