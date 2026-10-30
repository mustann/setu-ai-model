import re

with open("ui/app.js", "r", encoding="utf-8") as f:
    js_content = f.read()

with open("ui/index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

js_ids = re.findall(r'document\.getElementById\("([^"]+)"\)', js_content)
html_ids = set(re.findall(r'id="([^"]+)"', html_content))

missing = [i for i in set(js_ids) if i not in html_ids]
print("Total IDs checked in app.js:", len(set(js_ids)))
print("IDs missing in index.html:", missing)

# Check all elements in html
print("\nHTML IDs related to confidence/severity:")
for hid in sorted(html_ids):
    if "conf" in hid.lower() or "sev" in hid.lower() or "badg" in hid.lower():
        print(" ", hid)
