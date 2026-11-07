#!/usr/bin/env python3
"""Render the original 2D storyboard frames for the Mail-Shop tutorial.

The frames are deliberately vector-like and self-contained: no screenshots,
customer data, or third-party artwork is used. Pillow is loaded from the local
build helper when this file is run in the sandbox.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# The build environment keeps optional media tooling outside the repository.
if "/tmp/mail_shop_tools" not in sys.path:
    sys.path.insert(0, "/tmp/mail_shop_tools")

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "scenes"
OUT.mkdir(parents=True, exist_ok=True)

S = 2
W, H = 1280, 720
SW, SH = W * S, H * S

# Design tokens echo the light, indigo Mail-Shop workspace without copying UI
# screenshots. All visible labels are English so the bilingual Bangla voice is
# easy to follow even on a device without a Bengali font.
BG_TOP = "#F9FAFE"
BG_BOTTOM = "#EEF1FF"
INK = "#171A2A"
MUTED = "#68718A"
MUTED_2 = "#8B94AA"
LINE = "#E4E7F0"
WHITE = "#FFFFFF"
BRAND = "#6257D9"
BRAND_DARK = "#4C43B6"
PURPLE = "#8B70F6"
MINT = "#1FA980"
MINT_SOFT = "#E6F7F1"
BLUE = "#3985D8"
BLUE_SOFT = "#E9F3FF"
AMBER = "#D08A18"
AMBER_SOFT = "#FFF3D8"
ROSE = "#D95466"
ROSE_SOFT = "#FFECEF"
LAVENDER = "#F0EEFF"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
REGULAR_PATH = FONT_DIR / "DejaVuSans.ttf"
BOLD_PATH = FONT_DIR / "DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False):
    path = BOLD_PATH if bold else REGULAR_PATH
    return ImageFont.truetype(str(path), size * S)


def sc(v: float) -> int:
    return int(round(v * S))


def xy(box):
    return tuple(sc(v) for v in box)


def make_background(seed: int) -> Image.Image:
    img = Image.new("RGB", (SW, SH), BG_TOP)
    d = ImageDraw.Draw(img)
    top = tuple(int(BG_TOP[i:i + 2], 16) for i in (1, 3, 5))
    bot = tuple(int(BG_BOTTOM[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(SH):
        t = y / max(1, SH - 1)
        c = tuple(int(top[k] * (1 - t) + bot[k] * t) for k in range(3))
        d.line([(0, y), (SW, y)], fill=c)

    # Soft blobs give the flat illustration a little depth.
    glow = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    accents = [
        (1030 + (seed % 3) * 20, -80, 340, "#BBAEFF", 65),
        (110 + (seed % 2) * 28, 610, 270, "#9DE9D1", 32),
        (700, 280 + (seed % 3) * 18, 210, "#B9D9FF", 22),
    ]
    for cx, cy, r, color, alpha in accents:
        gd.ellipse(xy((cx - r, cy - r, cx + r, cy + r)), fill=color + f"{alpha:02X}")
    glow = glow.filter(ImageFilter.GaussianBlur(sc(34)))
    img = Image.alpha_composite(img.convert("RGBA"), glow)
    return img.convert("RGB")


def shadowed_round(img, box, radius=18, fill=WHITE, outline=None, shadow=True, shadow_alpha=28):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x1, y1, x2, y2 = xy(box)
    if shadow:
        ld.rounded_rectangle((x1 + sc(0), y1 + sc(7), x2 + sc(0), y2 + sc(7)), radius=sc(radius), fill=(29, 35, 72, shadow_alpha))
        layer = layer.filter(ImageFilter.GaussianBlur(sc(8)))
        img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((x1, y1, x2, y2), radius=sc(radius), fill=fill, outline=outline, width=sc(1) if outline else 1)
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def rect(d, box, fill, radius=0, outline=None, width=1):
    if radius:
        d.rounded_rectangle(xy(box), radius=sc(radius), fill=fill, outline=outline, width=sc(width) if outline else 1)
    else:
        d.rectangle(xy(box), fill=fill, outline=outline, width=sc(width) if outline else 1)


def ellipse(d, box, fill, outline=None, width=1):
    d.ellipse(xy(box), fill=fill, outline=outline, width=sc(width) if outline else 1)


def line(d, points, fill, width=1, joint="curve"):
    d.line([(sc(x), sc(y)) for x, y in points], fill=fill, width=sc(width), joint=joint)


def polygon(d, points, fill, outline=None, width=1):
    d.polygon([(sc(x), sc(y)) for x, y in points], fill=fill)
    if outline:
        d.line([(sc(x), sc(y)) for x, y in points + [points[0]]], fill=outline, width=sc(width), joint="curve")


def text(img, xy0, value, size=16, fill=INK, bold=False, anchor=None):
    d = ImageDraw.Draw(img)
    d.text((sc(xy0[0]), sc(xy0[1])), value, font=font(size, bold), fill=fill, anchor=anchor)


def text_width(value, size=16, bold=False):
    d = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    box = d.textbbox((0, 0), value, font=font(size, bold))
    return (box[2] - box[0]) / S


def wrap(value, max_width, size=16, bold=False):
    words = value.split()
    rows, row = [], ""
    for word in words:
        candidate = word if not row else row + " " + word
        if text_width(candidate, size, bold) <= max_width or not row:
            row = candidate
        else:
            rows.append(row)
            row = word
    if row:
        rows.append(row)
    return rows


def paragraph(img, xy0, value, max_width, size=15, fill=MUTED, bold=False, leading=7):
    y = xy0[1]
    for row in wrap(value, max_width, size, bold):
        text(img, (xy0[0], y), row, size=size, fill=fill, bold=bold)
        y += size + leading
    return y


def pill(img, box, label, fill=LAVENDER, fg=BRAND_DARK, size=11, dot=None):
    d = ImageDraw.Draw(img)
    rect(d, box, fill, radius=box[3] - box[1])
    x = box[0] + 12
    if dot:
        ellipse(d, (x, box[1] + 9, x + 7, box[1] + 16), dot)
        x += 15
    text(img, (x, box[1] + 7), label, size=size, fill=fg, bold=True)


def icon_check(d, x, y, color=MINT, size=18):
    ellipse(d, (x, y, x + size, y + size), color)
    line(d, [(x + 4, y + size / 2), (x + 8, y + size - 5), (x + size - 4, y + 5)], WHITE, 2)


def icon_lock(d, x, y, color=BRAND, size=24):
    rect(d, (x + 3, y + 10, x + size - 3, y + size), color, radius=4)
    d.arc(xy((x + 6, y, x + size - 6, y + 17)), start=180, end=360, fill=color, width=sc(3))
    ellipse(d, (x + size / 2 - 2, y + 16, x + size / 2 + 2, y + 20), WHITE)


def icon_mail(d, x, y, color=BRAND, width=54, height=40, fill=WHITE):
    rect(d, (x, y, x + width, y + height), fill, radius=9, outline=color, width=2)
    line(d, [(x + 4, y + 6), (x + width / 2, y + height / 2 + 5), (x + width - 4, y + 6)], color, 2)
    line(d, [(x + 5, y + height - 6), (x + width / 2 - 11, y + height / 2 + 3)], color, 2)
    line(d, [(x + width - 5, y + height - 6), (x + width / 2 + 11, y + height / 2 + 3)], color, 2)


def icon_search(d, x, y, color=BRAND, size=28):
    d.ellipse(xy((x, y, x + size - 7, y + size - 7)), outline=color, width=sc(3))
    line(d, [(x + size - 8, y + size - 8), (x + size + 4, y + size + 4)], color, 3)


def icon_key(d, x, y, color=AMBER, size=36):
    d.ellipse(xy((x, y, x + size * .52, y + size * .52)), outline=color, width=sc(4))
    line(d, [(x + size * .42, y + size * .42), (x + size, y + size)], color, 5)
    line(d, [(x + size * .72, y + size * .72), (x + size * .86, y + size * .58)], color, 4)
    line(d, [(x + size * .84, y + size * .84), (x + size, y + size * .68)], color, 4)


def icon_shield(d, x, y, color=MINT, size=46, fill=None):
    polygon(d, [(x + size / 2, y), (x + size, y + 12), (x + size - 4, y + size * .67), (x + size / 2, y + size), (x + 4, y + size * .67), (x, y + 12)], fill or color, outline=color, width=2)
    line(d, [(x + size * .28, y + size * .5), (x + size * .44, y + size * .66), (x + size * .73, y + size * .33)], WHITE, 3)


def icon_settings(d, x, y, color=BRAND, size=36):
    d.ellipse(xy((x + 8, y + 8, x + size - 8, y + size - 8)), outline=color, width=sc(4))
    for a, b in [((x + size / 2, y), (x + size / 2, y + 8)), ((x + size / 2, y + size - 8), (x + size / 2, y + size)), ((x, y + size / 2), (x + 8, y + size / 2)), ((x + size - 8, y + size / 2), (x + size, y + size / 2))]:
        line(d, [a, b], color, 4)
    ellipse(d, (x + size / 2 - 4, y + size / 2 - 4, x + size / 2 + 4, y + size / 2 + 4), color)


def draw_person(img, cx, cy, scale=1.0, shirt=BRAND, pose="wave"):
    d = ImageDraw.Draw(img)
    def q(v): return v * scale
    # soft ground shadow
    ellipse(d, (cx - q(55), cy + q(86), cx + q(55), cy + q(104)), "#D9DCEF")
    # legs
    line(d, [(cx - q(16), cy + q(54)), (cx - q(18), cy + q(94))], INK, max(2, int(q(8))))
    line(d, [(cx + q(16), cy + q(54)), (cx + q(20), cy + q(94))], INK, max(2, int(q(8))))
    line(d, [(cx - q(28), cy + q(94)), (cx - q(6), cy + q(94))], INK, max(2, int(q(7))))
    line(d, [(cx + q(9), cy + q(94)), (cx + q(32), cy + q(94))], INK, max(2, int(q(7))))
    # torso
    rect(d, (cx - q(44), cy - q(4), cx + q(44), cy + q(63)), shirt, radius=int(q(22)))
    # arms / poses
    if pose == "wave":
        line(d, [(cx + q(34), cy + q(8)), (cx + q(78), cy - q(34))], shirt, max(2, int(q(11))))
        line(d, [(cx + q(78), cy - q(34)), (cx + q(87), cy - q(56))], INK, max(2, int(q(6))))
        line(d, [(cx + q(78), cy - q(34)), (cx + q(99), cy - q(40))], INK, max(2, int(q(6))))
        line(d, [(cx + q(78), cy - q(34)), (cx + q(94), cy - q(18))], INK, max(2, int(q(6))))
        line(d, [(cx - q(34), cy + q(10)), (cx - q(74), cy + q(34))], shirt, max(2, int(q(11))))
    elif pose == "point":
        line(d, [(cx - q(34), cy + q(12)), (cx - q(75), cy - q(4))], shirt, max(2, int(q(11))))
        line(d, [(cx - q(75), cy - q(4)), (cx - q(98), cy - q(4))], INK, max(2, int(q(6))))
        line(d, [(cx + q(34), cy + q(12)), (cx + q(62), cy + q(35))], shirt, max(2, int(q(11))))
    else:
        line(d, [(cx - q(35), cy + q(10)), (cx - q(67), cy + q(48))], shirt, max(2, int(q(11))))
        line(d, [(cx + q(35), cy + q(10)), (cx + q(68), cy + q(48))], shirt, max(2, int(q(11))))
    # neck and head
    rect(d, (cx - q(13), cy - q(31), cx + q(13), cy - q(4)), "#F1B991", radius=int(q(7)))
    ellipse(d, (cx - q(42), cy - q(93), cx + q(42), cy - q(14)), "#F1B991")
    # hair cap
    d.pieslice(xy((cx - q(44), cy - q(101), cx + q(44), cy - q(29))), start=180, end=360, fill="#332B55")
    ellipse(d, (cx - q(38), cy - q(83), cx - q(29), cy - q(74)), INK)
    ellipse(d, (cx + q(29), cy - q(83), cx + q(38), cy - q(74)), INK)
    line(d, [(cx - q(16), cy - q(52)), (cx - q(8), cy - q(52))], INK, max(1, int(q(3))))
    line(d, [(cx + q(8), cy - q(52)), (cx + q(16), cy - q(52))], INK, max(1, int(q(3))))
    d.arc(xy((cx - q(14), cy - q(52), cx + q(14), cy - q(31))), start=15, end=165, fill=INK, width=max(1, int(q(3))))


def draw_ui_shell(img, box=(690, 155, 1175, 570), active="Inbox", compact=False):
    x1, y1, x2, y2 = box
    img = shadowed_round(img, box, radius=22, fill=WHITE, outline=LINE, shadow=True, shadow_alpha=24)
    d = ImageDraw.Draw(img)
    # top bar
    rect(d, (x1, y1, x2, y1 + 50), "#FBFCFF", radius=22)
    line(d, [(x1, y1 + 50), (x2, y1 + 50)], LINE, 1)
    ellipse(d, (x1 + 20, y1 + 19, x1 + 28, y1 + 27), BRAND)
    text(img, (x1 + 38, y1 + 15), "Aurelia Mail", size=12, fill=INK, bold=True)
    # sidebar
    line(d, [(x1 + 128, y1 + 50), (x1 + 128, y2)], LINE, 1)
    navs = [("Inbox", BRAND), ("OTP Vault", AMBER), ("Accounts", BLUE), ("Settings", MUTED_2)]
    for i, (label, col) in enumerate(navs):
        yy = y1 + 76 + i * 42
        if label == active:
            rect(d, (x1 + 12, yy - 5, x1 + 116, yy + 26), LAVENDER, radius=10)
        ellipse(d, (x1 + 25, yy + 2, x1 + 35, yy + 12), col)
        text(img, (x1 + 44, yy), label, size=10, fill=BRAND_DARK if label == active else MUTED, bold=label == active)
    # main header
    text(img, (x1 + 153, y1 + 72), active, size=20, fill=INK, bold=True)
    pill(img, (x1 + 153, y1 + 104, x1 + 278, y1 + 128), "SYNCED", fill=MINT_SOFT, fg=MINT, size=9, dot=MINT)
    if active == "Inbox":
        # stats cards
        for i, (lab, num, col) in enumerate([("EMAILS", "28", BRAND), ("UNREAD", "6", BLUE), ("OTP", "4", AMBER)]):
            xx = x1 + 153 + i * 102
            rect(d, (xx, y1 + 151, xx + 88, y1 + 207), "#FAFBFE", radius=12, outline=LINE)
            text(img, (xx + 12, y1 + 163), lab, size=7, fill=MUTED_2, bold=True)
            text(img, (xx + 12, y1 + 181), num, size=19, fill=col, bold=True)
        # rows
        rows = [("Security team", "Your verification code", AMBER), ("Product news", "New features are here", BRAND), ("Alex Morgan", "Let's review the plan", MINT)]
        for i, (sender, subj, col) in enumerate(rows):
            yy = y1 + 235 + i * 58
            ellipse(d, (x1 + 157, yy + 3, x1 + 185, yy + 31), col)
            text(img, (x1 + 195, yy + 3), sender, size=10, fill=INK, bold=True)
            text(img, (x1 + 195, yy + 21), subj, size=9, fill=MUTED)
            line(d, [(x1 + 153, yy + 45), (x2 - 24, yy + 45)], LINE, 1)
    elif active == "OTP Vault":
        rect(d, (x1 + 153, y1 + 151, x2 - 25, y1 + 205), AMBER_SOFT, radius=13)
        icon_key(d, x1 + 174, y1 + 164, AMBER, 30)
        text(img, (x1 + 218, y1 + 161), "LATEST CODE", size=8, fill=AMBER, bold=True)
        text(img, (x1 + 218, y1 + 178), "482 109", size=22, fill=INK, bold=True)
        for i in range(2):
            yy = y1 + 230 + i * 67
            rect(d, (x1 + 153, yy, x2 - 25, yy + 52), "#FBFCFF", radius=11, outline=LINE)
            ellipse(d, (x1 + 169, yy + 13, x1 + 185, yy + 29), AMBER)
            text(img, (x1 + 198, yy + 9), "Security message", size=10, fill=INK, bold=True)
            text(img, (x1 + 198, yy + 27), "Copy OTP", size=9, fill=BRAND_DARK, bold=True)
    elif active == "Accounts":
        rect(d, (x1 + 153, y1 + 151, x2 - 25, y1 + 216), BLUE_SOFT, radius=13)
        ellipse(d, (x1 + 175, y1 + 169, x1 + 205, y1 + 199), BLUE)
        text(img, (x1 + 218, y1 + 164), "WORK INBOX", size=9, fill=BLUE, bold=True)
        text(img, (x1 + 218, y1 + 183), "Connected", size=11, fill=INK, bold=True)
        for i in range(2):
            yy = y1 + 238 + i * 50
            rect(d, (x1 + 153, yy, x2 - 25, yy + 37), "#FBFCFF", radius=10, outline=LINE)
            icon_check(d, x1 + 169, yy + 10, MINT, 16)
            text(img, (x1 + 196, yy + 9), "OAuth2 connection" if i == 0 else "Last sync: now", size=9, fill=MUTED, bold=i == 0)
    else:
        for i, (label, val, col) in enumerate([("Auto-refresh", "5 minutes", BRAND), ("Preview lines", "2 lines", BLUE), ("Remote images", "Blocked", MINT)]):
            yy = y1 + 151 + i * 63
            text(img, (x1 + 153, yy), label, size=10, fill=INK, bold=True)
            rect(d, (x1 + 335, yy - 2, x2 - 26, yy + 25), "#F8F9FC", radius=9, outline=LINE)
            text(img, (x1 + 348, yy + 5), val, size=9, fill=col, bold=True)
    return img


def draw_scene_base(scene_no, chapter, chapter_label, title, subtitle, accent=BRAND):
    img = make_background(scene_no)
    d = ImageDraw.Draw(img)
    # top identity bar
    text(img, (62, 42), "MAIL-SHOP", size=13, fill=BRAND_DARK, bold=True)
    text(img, (165, 43), "QUICK TUTORIAL", size=11, fill=MUTED_2, bold=True)
    pill(img, (1017, 30, 1218, 59), "BANGLA VOICE  ·  05:00", fill=WHITE, fg=MUTED, size=9)
    line(d, [(62, 77), (1218, 77)], LINE, 1)
    # chapter marker
    text(img, (72, 138), f"0{chapter}  /  {chapter_label.upper()}", size=11, fill=accent, bold=True)
    text(img, (72, 174), title, size=38, fill=INK, bold=True)
    paragraph(img, (74, 235), subtitle, 465, size=16, fill=MUTED, leading=8)
    # left accent rule
    rect(d, (72, 304, 78, 397), accent, radius=3)
    # footer progress chrome
    text(img, (72, 656), "A focused workspace for real email and OTP data", size=11, fill=MUTED_2)
    text(img, (1154, 656), f"{scene_no:02d} / 15", size=11, fill=MUTED_2, bold=True)
    line(d, [(72, 685), (1208, 685)], LINE, 4)
    line(d, [(72, 685), (72 + (1136 * scene_no / 15), 685)], accent, 4)
    return img


def scene_01():
    img = draw_scene_base(1, 1, "Welcome", "Your inbox, made simple", "One calm place for messages, accounts, and verification codes.", BRAND)
    d = ImageDraw.Draw(img)
    draw_person(img, 1010, 438, 1.35, BRAND, "wave")
    icon_mail(d, 835, 202, BRAND, 130, 90)
    rect(d, (803, 322, 1108, 412), WHITE, radius=18, outline=LINE)
    pill(img, (826, 343, 925, 367), "INBOX", fill=LAVENDER, fg=BRAND_DARK, size=9)
    text(img, (826, 381), "28 messages", size=19, fill=INK, bold=True)
    icon_shield(d, 1062, 285, MINT, 44, MINT)
    return img


def scene_02():
    img = draw_scene_base(2, 1, "Welcome", "Four spaces. One workflow.", "Move from connection to code without losing context.", PURPLE)
    d = ImageDraw.Draw(img)
    cards = [(680, 178, "Inbox", "Read and search", BRAND, "mail"), (922, 178, "OTP Vault", "Copy safely", AMBER, "key"), (680, 340, "Accounts", "Connect mailboxes", BLUE, "people"), (922, 340, "Settings", "Tune privacy", MINT, "gear")]
    for x, y, label, sub, col, ico in cards:
        rect(d, (x, y, x + 215, y + 132), WHITE, radius=18, outline=LINE)
        ellipse(d, (x + 20, y + 20, x + 58, y + 58), col + "22" if len(col) == 7 else col)
        if ico == "mail": icon_mail(d, x + 27, y + 29, col, 24, 18, WHITE)
        elif ico == "key": icon_key(d, x + 26, y + 28, col, 24)
        elif ico == "gear": icon_settings(d, x + 25, y + 27, col, 27)
        else:
            ellipse(d, (x + 29, y + 27, x + 47, y + 45), col)
            line(d, [(x + 23, y + 51), (x + 53, y + 51)], col, 3)
        text(img, (x + 20, y + 76), label, size=15, fill=INK, bold=True)
        text(img, (x + 20, y + 101), sub, size=10, fill=MUTED)
    return img


def scene_03():
    img = draw_scene_base(3, 2, "Connect", "Connect an account", "Choose the provider method that matches your setup.", BLUE)
    d = ImageDraw.Draw(img)
    draw_person(img, 770, 476, 1.05, BLUE, "point")
    # laptop
    rect(d, (855, 282, 1174, 489), WHITE, radius=16, outline=LINE)
    rect(d, (879, 306, 1150, 454), "#F7F8FC", radius=9, outline=LINE)
    text(img, (901, 325), "ADD ACCOUNT", size=11, fill=BLUE, bold=True)
    for i, (lab, val) in enumerate([("Email", "name@example.com"), ("Refresh token", "••••••••••"), ("Client ID", "optional")]):
        yy = 355 + i * 31
        text(img, (901, yy), lab, size=8, fill=MUTED_2, bold=True)
        rect(d, (989, yy - 3, 1127, yy + 18), WHITE, radius=6, outline=LINE)
        text(img, (998, yy + 2), val, size=8, fill=MUTED)
    rect(d, (879, 464, 1150, 508), BLUE, radius=12)
    text(img, (1014, 480), "Add account", size=11, fill=WHITE, bold=True, anchor="mm")
    line(d, [(1076, 550), (1130, 550)], BLUE, 3)
    polygon(d, [(1130, 550), (1118, 542), (1118, 558)], BLUE)
    text(img, (923, 539), "provider method", size=10, fill=MUTED, bold=True)
    return img


def scene_04():
    img = draw_scene_base(4, 2, "Connect", "Keep tokens private", "A simple rule: credentials stay in your trusted environment.", MINT)
    d = ImageDraw.Draw(img)
    rect(d, (684, 170, 1137, 532), WHITE, radius=22, outline=LINE)
    icon_shield(d, 874, 200, MINT, 76, MINT)
    text(img, (772, 300), "PRIVATE BY DEFAULT", size=13, fill=MINT, bold=True)
    text(img, (804, 329), "No screenshots", size=18, fill=INK, bold=True)
    text(img, (811, 363), "No forwarded tokens", size=18, fill=INK, bold=True)
    for i, label in enumerate(["Refresh token", "API key", "Client ID"]):
        yy = 412 + i * 28
        rect(d, (750, yy, 1069, yy + 20), "#F8F9FC", radius=6, outline=LINE)
        text(img, (766, yy + 4), label, size=9, fill=MUTED)
        text(img, (1022, yy + 4), "••••••••", size=9, fill=BRAND_DARK, bold=True)
    draw_person(img, 1135, 476, .72, MINT, "wave")
    return img


def scene_05():
    img = draw_scene_base(5, 2, "Connect", "Sync with confidence", "Watch the status pill, then let the workspace load real data.", BRAND)
    d = ImageDraw.Draw(img)
    icon_mail(d, 754, 270, BRAND, 150, 104)
    icon_mail(d, 1010, 270, BLUE, 150, 104)
    line(d, [(912, 315), (994, 315)], BRAND, 4)
    polygon(d, [(994, 315), (976, 303), (976, 327)], BRAND)
    pill(img, (753, 414, 903, 442), "CONNECTED", fill=MINT_SOFT, fg=MINT, size=10, dot=MINT)
    pill(img, (1008, 414, 1159, 442), "SYNCING", fill=LAVENDER, fg=BRAND_DARK, size=10, dot=BRAND)
    rect(d, (765, 478, 1154, 511), WHITE, radius=11, outline=LINE)
    rect(d, (782, 490, 1089, 499), "#E6E8F2", radius=5)
    rect(d, (782, 490, 1026, 499), BRAND, radius=5)
    text(img, (766, 532), "First sync may take a moment", size=11, fill=MUTED, bold=True)
    return img


def scene_06():
    img = draw_scene_base(6, 3, "Inbox", "Inbox at a glance", "Live summary cards help you see what needs attention first.", BRAND)
    img = draw_ui_shell(img, (690, 145, 1190, 575), active="Inbox")
    return img


def scene_07():
    img = draw_scene_base(7, 3, "Inbox", "Search in seconds", "Find a sender, subject, body phrase, or code with one focused query.", PURPLE)
    d = ImageDraw.Draw(img)
    # search panel
    rect(d, (690, 180, 1179, 550), WHITE, radius=22, outline=LINE)
    text(img, (724, 207), "INBOX SEARCH", size=11, fill=PURPLE, bold=True)
    rect(d, (722, 242, 1149, 289), "#F8F9FC", radius=12, outline=LINE)
    icon_search(d, 742, 253, PURPLE, 23)
    text(img, (781, 256), "verification code", size=15, fill=INK, bold=True)
    pill(img, (1014, 252, 1127, 278), "3 RESULTS", fill=LAVENDER, fg=BRAND_DARK, size=9)
    results = [("Security team", "Your verification code", AMBER), ("Account notice", "Confirm your sign-in", BRAND), ("Login service", "One-time passcode", MINT)]
    for i, (sender, subj, col) in enumerate(results):
        yy = 323 + i * 62
        ellipse(d, (728, yy + 3, 756, yy + 31), col)
        text(img, (770, yy + 2), sender, size=11, fill=INK, bold=True)
        text(img, (770, yy + 23), subj, size=10, fill=MUTED)
        line(d, [(722, yy + 47), (1149, yy + 47)], LINE, 1)
    # magnifier accent
    icon_search(d, 1100, 475, PURPLE, 34)
    return img


def scene_08():
    img = draw_scene_base(8, 3, "Inbox", "Open, read, copy", "Message details keep sender, subject, and read state together.", BLUE)
    d = ImageDraw.Draw(img)
    rect(d, (684, 154, 1176, 568), WHITE, radius=22, outline=LINE)
    pill(img, (716, 181, 829, 208), "MESSAGE DETAIL", fill=BLUE_SOFT, fg=BLUE, size=9)
    text(img, (716, 232), "Your verification code", size=22, fill=INK, bold=True)
    text(img, (716, 272), "Security team  ·  today, 10:42", size=11, fill=MUTED)
    line(d, [(716, 303), (1145, 303)], LINE, 1)
    for i, txt in enumerate(["Hello! We received a sign-in request.", "Use the one-time code below to continue.", "This code expires soon."]):
        text(img, (716, 336 + i * 28), txt, size=12, fill=INK if i == 1 else MUTED, bold=i == 1)
    rect(d, (716, 448, 907, 492), BRAND, radius=11)
    text(img, (811, 470), "Copy message", size=11, fill=WHITE, bold=True, anchor="mm")
    rect(d, (924, 448, 1145, 492), LAVENDER, radius=11)
    icon_check(d, 942, 462, BRAND, 15)
    text(img, (1050, 470), "Read state", size=11, fill=BRAND_DARK, bold=True, anchor="mm")
    return img


def scene_09():
    img = draw_scene_base(9, 4, "OTP Vault", "OTP Vault", "Real codes, clearly separated from the rest of your inbox.", AMBER)
    img = draw_ui_shell(img, (690, 145, 1190, 575), active="OTP Vault")
    return img


def scene_10():
    img = draw_scene_base(10, 4, "OTP Vault", "Copy only what you need", "Treat every verification code as sensitive—even after it is convenient.", ROSE)
    d = ImageDraw.Draw(img)
    rect(d, (702, 174, 930, 526), WHITE, radius=22, outline=LINE)
    icon_key(d, 780, 214, AMBER, 66)
    text(img, (752, 307), "LATEST OTP", size=12, fill=AMBER, bold=True)
    text(img, (750, 347), "482 109", size=32, fill=INK, bold=True)
    text(img, (750, 397), "Security team", size=12, fill=MUTED, bold=True)
    rect(d, (748, 444, 881, 486), BRAND, radius=11)
    text(img, (815, 465), "Copy OTP", size=11, fill=WHITE, bold=True, anchor="mm")
    # right caution card
    rect(d, (976, 206, 1150, 470), ROSE_SOFT, radius=22)
    icon_shield(d, 1034, 240, ROSE, 58, ROSE)
    text(img, (1006, 334), "DO NOT", size=12, fill=ROSE, bold=True)
    text(img, (1006, 364), "forward", size=19, fill=INK, bold=True)
    text(img, (1006, 392), "or paste", size=19, fill=INK, bold=True)
    text(img, (1006, 420), "on unknown pages", size=12, fill=MUTED)
    line(d, [(932, 365), (970, 365)], ROSE, 3)
    polygon(d, [(970, 365), (958, 357), (958, 373)], ROSE)
    return img


def scene_11():
    img = draw_scene_base(11, 5, "Settings", "Tune your workspace", "Small preferences can make a busy inbox feel calm and predictable.", BRAND)
    img = draw_ui_shell(img, (690, 145, 1190, 575), active="Settings")
    return img


def scene_12():
    img = draw_scene_base(12, 5, "Settings", "Privacy-first settings", "Keep remote images blocked and remember what a shared device can retain.", MINT)
    d = ImageDraw.Draw(img)
    rect(d, (694, 170, 1178, 535), WHITE, radius=22, outline=LINE)
    text(img, (729, 205), "PRIVACY CHECK", size=12, fill=MINT, bold=True)
    rows = [("Remote images", "Blocked", MINT), ("Remember session", "Off", BRAND), ("Auto-refresh", "5 minutes", BLUE)]
    for i, (lab, val, col) in enumerate(rows):
        yy = 263 + i * 76
        text(img, (729, yy), lab, size=15, fill=INK, bold=True)
        text(img, (729, yy + 26), "A safer default for this workspace", size=10, fill=MUTED)
        soft = {MINT: MINT_SOFT, BRAND: LAVENDER, BLUE: BLUE_SOFT}[col]
        rect(d, (1010, yy + 4, 1124, yy + 34), soft, radius=15)
        ellipse(d, (1024 if val == "Off" else 1096, yy + 9, 1042 if val == "Off" else 1114, yy + 27), col)
        text(img, (1050 if val == "Off" else 1023, yy + 11), val, size=9, fill=col, bold=True)
        line(d, [(729, yy + 57), (1135, yy + 57)], LINE, 1)
    icon_shield(d, 1116, 463, MINT, 42, MINT)
    return img


def scene_13():
    img = draw_scene_base(13, 5, "Settings", "The safe workflow", "A short checklist turns five screens into one repeatable habit.", PURPLE)
    d = ImageDraw.Draw(img)
    steps = [("Connect", "Use your provider method", BLUE), ("Refresh", "Load real messages", BRAND), ("Verify", "Check the sender", AMBER), ("Copy", "Clear the clipboard", MINT)]
    for i, (lab, sub, col) in enumerate(steps):
        yy = 178 + i * 79
        rect(d, (715, yy, 1148, yy + 59), WHITE, radius=15, outline=LINE)
        ellipse(d, (733, yy + 13, 766, yy + 46), col)
        text(img, (749, yy + 29), str(i + 1), size=13, fill=WHITE, bold=True, anchor="mm")
        text(img, (790, yy + 12), lab, size=15, fill=INK, bold=True)
        text(img, (790, yy + 34), sub, size=10, fill=MUTED)
        icon_check(d, 1100, yy + 20, col, 18)
    return img


def scene_14():
    img = draw_scene_base(14, 5, "Finish", "Ready when you are", "Simple, focused, and always guided by the real provider message.", BRAND)
    d = ImageDraw.Draw(img)
    # logo card
    rect(d, (713, 197, 1139, 480), WHITE, radius=26, outline=LINE)
    rect(d, (871, 228, 981, 338), BRAND, radius=27)
    icon_mail(d, 890, 262, WHITE, 71, 48, BRAND)
    text(img, (786, 371), "MAIL-SHOP", size=25, fill=INK, bold=True)
    text(img, (793, 412), "A calmer way to handle email and OTP", size=11, fill=MUTED)
    pill(img, (835, 447, 1019, 475), "WORKFLOW COMPLETE", fill=MINT_SOFT, fg=MINT, size=9, dot=MINT)
    draw_person(img, 1107, 492, .78, BRAND, "wave")
    return img


def scene_15():
    img = draw_scene_base(15, 5, "Finish", "Keep it secure", "Thanks for watching. Your data stays yours.", MINT)
    d = ImageDraw.Draw(img)
    draw_person(img, 850, 464, 1.25, MINT, "wave")
    icon_shield(d, 1017, 237, MINT, 96, MINT)
    text(img, (974, 368), "SAFE", size=18, fill=MINT, bold=True)
    text(img, (953, 401), "BY DEFAULT", size=15, fill=INK, bold=True)
    pill(img, (938, 458, 1112, 488), "SEE YOU IN INBOX", fill=LAVENDER, fg=BRAND_DARK, size=10)
    return img


SCENES = [scene_01, scene_02, scene_03, scene_04, scene_05, scene_06, scene_07, scene_08, scene_09, scene_10, scene_11, scene_12, scene_13, scene_14, scene_15]


def main():
    for i, render in enumerate(SCENES, start=1):
        out = OUT / f"scene_{i:02d}.png"
        img = render().resize((W, H), Image.Resampling.LANCZOS).convert("RGB")
        img.save(out, quality=95, optimize=True)
        print(out)


if __name__ == "__main__":
    main()
