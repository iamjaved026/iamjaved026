import urllib.request
import re
import json

req = urllib.request.Request(
    'https://github.com/users/iamjaved026/contributions',
    headers={'User-Agent': 'Mozilla/5.0'}
)
html = urllib.request.urlopen(req).read().decode('utf-8')

# Regex to match each day cell
pattern = re.compile(
    r'<td[^>]*data-date="([^"]+)"[^>]*id="([^"]+)"[^>]*data-level="([0-4])"',
    re.DOTALL
)
cells = pattern.findall(html)
if not cells:
    # Alternative attribute ordering
    pattern = re.compile(
        r'<td[^>]*id="([^"]+)"[^>]*data-date="([^"]+)"[^>]*data-level="([0-4])"',
        re.DOTALL
    )
    temp = pattern.findall(html)
    cells = [(d, i, l) for (i, d, l) in temp]

tooltips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>(.*?)</tool-tip>', html))

days = []
total_parsed = 0
for date, comp_id, level in cells:
    tip = tooltips.get(comp_id, "").strip()
    cnt_match = re.search(r'([0-9]+)\s+contribution', tip)
    count = int(cnt_match.group(1)) if cnt_match else 0
    total_parsed += count
    days.append({
        "date": date,
        "level": int(level),
        "count": count,
        "tip": tip
    })

print(f"Extracted {len(days)} days, total contributions: {total_parsed}")
active = [d for d in days if d["count"] > 0]
print(f"Active days: {len(active)}")
print("Top active days:", sorted(active, key=lambda x: x["count"], reverse=True)[:5])

with open("d:/Projects/portofilio/github/my/v2/assets/contributions_real.json", "w", encoding="utf-8") as f:
    json.dump({"total": total_parsed, "days": days}, f, indent=2)
print("Saved to contributions_real.json")
