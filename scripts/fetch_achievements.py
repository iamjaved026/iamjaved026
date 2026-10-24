import urllib.request
import re

req = urllib.request.Request(
    'https://github.com/iamjaved026',
    headers={'User-Agent': 'Mozilla/5.0'}
)
html = urllib.request.urlopen(req).read().decode('utf-8')
badges = re.findall(r'alt="Achievement:\s*([^"]+)"', html)
print("Badges found on GitHub profile:", badges)

# Also check pinned items or trophies
trophies = re.findall(r'data-hovercard-type="achievement"[^>]*>(.*?)</a>', html, re.DOTALL)
print("Achievement hovercards:", len(trophies))
