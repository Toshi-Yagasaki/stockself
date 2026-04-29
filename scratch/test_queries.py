import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

def test_query(query):
    print(f"Testing query: {query}")
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ja&gl=JP&ceid=JP:ja"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read()
    root = ET.fromstring(html)
    
    items = root.findall('.//item')
    for item in items[:3]:
        title = item.find('title').text
        print(f"- {title}")
    print()

test_query('"キヤノン" 株価')
test_query('7751 株価')
test_query('7751 ニュース')
