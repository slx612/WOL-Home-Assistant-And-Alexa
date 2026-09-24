"""Build WakeLink's small native icon and Windows version resources."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
image = Image.new("RGBA", (256, 256))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((8, 8, 248, 248), radius=60, fill="#183b3a")
draw.arc((47, 51, 176, 195), 60, 300, fill="#eef3df", width=24)
draw.arc((99, 51, 228, 195), 240, 480, fill="#62d3ae", width=24)
draw.line((126, 38, 126, 113), fill="#eef3df", width=20)
image.save(ASSETS / "wakelink.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

BRAND = ROOT.parent / "custom_components" / "pc_power_free" / "brand"
BRAND.mkdir(exist_ok=True)
image.save(BRAND / "icon.png")
logo = Image.new("RGBA", (720, 256), (0, 0, 0, 0))
logo.alpha_composite(image, (0, 0))
ImageDraw.Draw(logo).text((282, 78), "WakeLink", fill="#183b3a",
                          font=ImageFont.load_default(size=82))
logo.save(BRAND / "logo.png")

for filename, description in (("PCPowerAgent", "WakeLink local power agent"),
                               ("PCPowerTray", "WakeLink system tray"),
                               ("PCPowerSetup", "WakeLink desktop")):
    version = f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers=(0,2,0,12), prodvers=(0,2,0,12), mask=0x3f, flags=0x2,
                   OS=0x40004, fileType=0x1, subtype=0x0, date=(0,0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'WakeLink open-source project'),
    StringStruct('FileDescription', '{description}'),
    StringStruct('FileVersion', '0.2.0-beta.12'),
    StringStruct('InternalName', '{filename}'),
    StringStruct('OriginalFilename', '{filename}.exe'),
    StringStruct('ProductName', 'WakeLink'),
    StringStruct('ProductVersion', '0.2.0-beta.12')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
'''
    (ASSETS / f"{filename}.version.txt").write_text(version, encoding="utf-8")
