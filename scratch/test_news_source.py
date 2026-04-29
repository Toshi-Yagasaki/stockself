import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

def test():
    query = "キヤノン 株価"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ja&gl=JP&ceid=JP:ja"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read()
    root = ET.fromstring(html)
    
    items = root.findall('.//item')
    for item in items[:3]:
        title = item.find('title').text
        link = item.find('link').text
        pub_date = item.find('pubDate').text
        source = item.find('source').text if item.find('source') is not None else ""
        print({"title": title, "source": source, "pubDate": pub_date})

test()
