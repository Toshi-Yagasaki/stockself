import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json

def get_news(query):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ja&gl=JP&ceid=JP:ja"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read()
        root = ET.fromstring(html)
        items = root.findall('.//item')
        results = []
        for item in items[:5]:
            title = item.find('title').text
            pubDate = item.find('pubDate').text
            results.append({"title": title, "pubDate": pubDate})
        return results
    except Exception as e:
        return str(e)

results = {
    '7267': get_news('7267 本田技研 株価'),
    'when_6m': get_news('7267 本田技研 株価 when:6m'),
    'when_1y': get_news('7267 本田技研 株価 when:1y'),
}

with open('scratch/test_news_when_2.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
