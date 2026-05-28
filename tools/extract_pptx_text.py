from pathlib import Path
from xml.etree import ElementTree as ET
import re
import zipfile


PPTX = Path(r"C:\Users\醨\xwechat_files\wxid_odh8547copbs32_bb21\temp\RWTemp\2026-05\6666bd15fb58091eeaccd0914bcd1ac0\Echo(4).pptx")


def slide_key(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def main() -> None:
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    with zipfile.ZipFile(PPTX) as zf:
        slides = sorted(
            [name for name in zf.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")],
            key=slide_key,
        )
        for index, name in enumerate(slides, 1):
            root = ET.fromstring(zf.read(name))
            texts = []
            for node in root.findall(".//a:t", ns):
                value = (node.text or "").strip()
                if value:
                    texts.append(value)
            print(f"\n--- SLIDE {index} ---")
            print("\n".join(texts))


if __name__ == "__main__":
    main()
