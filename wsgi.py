import os
import time
from dotenv import load_dotenv
import json
from flask import Flask
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
import colorama
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

app = Flask(__name__)

load_dotenv()

# init the colorama module
colorama.init()

GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET
YELLOW = colorama.Fore.YELLOW

# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()

total_urls_visited = 0

# Cargar las credenciales desde la variable de entorno
creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
if creds_json:
    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
else:
    creds = None

# Seteamos el archivo de Google Sheets que queremos usar
spreadsheet_id = '1hjehocc3bdHS68jDQ7rHlZrMHhDT5_bQyd1ZRRpqAl4'
sheet_name = 'Sheet1'

sheets_api = build('sheets', 'v4', credentials=creds)

@app.route('/')
def hello_world():
    # Leer el dato de prueba de la hoja de cálculo
    result = sheets_api.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f'{sheet_name}!A1:A2').execute()
    test_data = result['values']
    agregar_hola_a_google_sheets()
    return f'Hola Mundo! El dato de prueba es: {test_data}'

def agregar_hola_a_google_sheets():
    # Leer todas las celdas en la columna A hasta la fila 1000 (ajusta este valor según sea necesario)
    result = sheets_api.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f'{sheet_name}!A1:A1000'
    ).execute()

    values = result.get('values', [])

    # Encontrar la primera celda vacía en la columna A
    row = 1
    for value in values:
        if not value or not value[0].strip():
            break
        row += 1

    # Escribir "Hola" en la primera celda vacía de la columna A
    body = {
        'range': f'{sheet_name}!A{row}',
        'majorDimension': 'ROWS',
        'values': [['Hola']]
    }
    sheets_api.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f'{sheet_name}!A{row}',
        valueInputOption='RAW',
        body=body
    ).execute()


@app.route('/scrap')
def scrap():
    crawl("https://www.google.com/", 5)
    return f'Aqui hago el scraping'


def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_website_links(url):
    """
    Returns all URLs that is found on `url` in which it belongs to the same website
    """
    # all URLs of `url`
    urls = set()
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    domain_name = urlparse(url).netloc
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            # href empty tag
            continue
        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            # not a valid URL
            continue
        if href in internal_urls:
            # already in the set
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                print(f"{GRAY}[!] External link: {href}{RESET}")
                external_urls.add(href)
            continue
        if href.endswith(('.jpg', '.png', '.pdf')):
            # ignore links that end with .jpg or .png
            continue
        if href.startswith(('tel:', 'mailto:')):
            # ignore tel: and mailto: links
            continue 
        print(f"{GREEN}[*] Internal link: {href}{RESET}")
        urls.add(href)
        internal_urls.add(href)
    return urls


def crawl(url, max_urls=5):
    """
    Crawls a web page and extracts all links.
    You'll find all links in `external_urls` and `internal_urls` global set variables.
    params:
        max_urls (int): number of max urls to crawl, default is 30.
    """
    global total_urls_visited
    total_urls_visited += 1
    print(f"{YELLOW}[*] Crawling: {url}{RESET}")
    links = get_all_website_links(url)
    for link in links:
        if total_urls_visited > max_urls:
            print(f"{YELLOW}[*] Terminado!{RESET}")
            break
        print("Esperando 2 segundos...")
        time.sleep(2)  # Espera 2 segundos antes de continuar      
        crawl(link, max_urls=max_urls)


if __name__ == '__main__':
    app.run()