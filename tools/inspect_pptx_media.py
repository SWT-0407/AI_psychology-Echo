from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile

from PIL import Image


PPTX = Path(r"C:\Users\醨\xwechat_files\wxid_odh8547copbs32_bb21\temp\RWTemp\2026-05\6666bd15fb58091eeaccd0914bcd1ac0\Echo(4).pptx")
OUT_DIR = Path(r"E:\Users\醨\PycharmProjects\PythonProject6\reports\pptx_media")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PPTX) as zf:
        media = [name for name in zf.namelist() if name.startswith("ppt/media/")]
        for name in media:
            target = OUT_DIR / Path(name).name
            target.write_bytes(zf.read(name))
            try:
                with Image.open(target) as img:
                    print(f"{Path(name).name}\t{img.width}x{img.height}\t{img.mode}")
            except Exception:
                print(f"{Path(name).name}\tnon-image")

        for slide_no in [7, 8, 14]:
            rel_name = f"ppt/slides/_rels/slide{slide_no}.xml.rels"
            if rel_name not in zf.namelist():
                continue
            root = ET.fromstring(zf.read(rel_name))
            print(f"\n--- slide {slide_no} rels ---")
            for rel in root:
                rid = rel.attrib.get("Id")
                target = rel.attrib.get("Target")
                rel_type = rel.attrib.get("Type", "").rsplit("/", 1)[-1]
                print(rid, rel_type, target)


if __name__ == "__main__":
    main()
