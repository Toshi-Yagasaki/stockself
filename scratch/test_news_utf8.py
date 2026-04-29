import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json

def get_titles(query):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ja&gl=JP&ceid=JP:ja"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read()
    root = ET.fromstring(html)
    return [item.find('title').text for item in root.findall('.//item')[:5]]

results = {
    'quotes': get_titles('"キヤノン" 株価'),
    'code': get_titles('7751 株価'),
    'both': get_titles('7751 キヤノン 株価')
}

with open('scratch/test_news_utf8.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
