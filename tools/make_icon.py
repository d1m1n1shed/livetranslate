"""Generate assets/icon.png and assets/icon.ico (run with the project venv)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 1024
OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = r"C:\Windows\Fonts\YuGothB.ttc"


def gradient(c1, c2):
    img = Image.new("RGB", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * S)
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
    return img


def main() -> None:
    OUT.mkdir(exist_ok=True)
    # pastel pink -> sky background in a rounded square
    bg = gradient((255, 160, 200), (130, 200, 255))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), 230, fill=255)
    icon = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    icon.paste(bg, (0, 0), mask)

    # soft shadow + white speech bubble
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((150, 190, 880, 760), 200, fill=(80, 60, 140, 90))
    icon.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)), (0, 14))
    d = ImageDraw.Draw(icon)
    d.rounded_rectangle((140, 160, 884, 720), 200, fill="white")
    d.polygon([(300, 690), (250, 880), (470, 700)], fill="white")  # bubble tail

    # kanji "訳" (translate)
    f = ImageFont.truetype(FONT, 470)
    d.text((512, 405), "訳", font=f, fill=(255, 112, 150), anchor="mm")

    # cute face under the kanji line: blush cheeks + tiny smile
    for cx in (330, 694):
        d.ellipse((cx - 46, 640 - 26, cx + 46, 640 + 26), fill=(255, 190, 205))
    d.arc((462, 625, 562, 690), 20, 160, fill=(255, 112, 150), width=14)

    # sparkles
    for cx, cy, r in ((820, 180, 56), (190, 140, 36), (860, 800, 40)):
        d.polygon([(cx, cy - r), (cx + r * .3, cy - r * .3), (cx + r, cy), (cx + r * .3, cy + r * .3),
                   (cx, cy + r), (cx - r * .3, cy + r * .3), (cx - r, cy), (cx - r * .3, cy - r * .3)],
                  fill=(255, 245, 160))

    icon.resize((512, 512), Image.LANCZOS).save(OUT / "icon.png")
    icon.save(OUT / "icon.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])


if __name__ == "__main__":
    main()
