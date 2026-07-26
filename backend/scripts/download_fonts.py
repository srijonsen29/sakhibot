import urllib.request, os

os.makedirs("fonts", exist_ok=True)

FONTS = {
    "NotoSans-Regular.ttf":
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
    "NotoSansDevanagari-Regular.ttf":
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
    "NotoSansBengali-Regular.ttf":
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansBengali/NotoSansBengali-Regular.ttf",
    "NotoSansTamil-Regular.ttf":
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf",
    "NotoSansTelugu-Regular.ttf":
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf",
    "NotoSansGujarati-Regular.ttf":
        "https://github.com/notofonts/noto-fonts/raw/main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Regular.ttf",
}

for filename, url in FONTS.items():
    path = os.path.join("fonts", filename)
    if os.path.exists(path):
        print(f"Already exists: {filename}")
        continue
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, path)
        print(f"  Saved: {path}")
    except Exception as e:
        print(f"  Failed: {e}")

print("\nDone. Fonts in backend/fonts/")