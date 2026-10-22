#!/usr/bin/env python3
"""红蓝图集 = 蓝白九行原帧换色（见 recolor.py）；动作、表情、位置与蓝白逐帧一致。"""

from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / "work/goat-leo/redblue-redraw"  # 中间帧放在被忽略的 work/ 下
CW, CH = 192, 208
ACCEPTED_ROOT = WORK / "frames-recolor"
OUT = ROOT / "dist/goat-leo/outfits/red-blue-legend.webp"


def main() -> None:
    scripts = ROOT / ".opencode/skills/hatch-pet/scripts"
    specs = runpy.run_path(str(scripts / "compose_atlas.py"))["ROW_SPECS"]
    classic = Image.open(ROOT / "dist/goat-leo/spritesheet.webp").convert("RGBA")
    root = WORK / "atlas-frames"
    for state, row, n in specs:
        d = root / state
        d.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            cell = Image.open(ACCEPTED_ROOT / state / f"{i:02d}.png").convert("RGBA")
            assert cell.size == (CW, CH), (state, i, cell.size)
            cell.save(d / f"{i:02d}.png")
    png = WORK / "red-blue-legend.png"
    subprocess.run(
        [sys.executable, str(scripts / "compose_atlas.py"), "--frames-root", str(root), "--output", str(png), "--webp-output", str(OUT)],
        check=True,
    )
    # 轮廓与蓝白一致（只换色不改形），且每行确实换了色
    new = Image.open(OUT).convert("RGBA")
    assert new.getchannel("A").tobytes() == classic.getchannel("A").tobytes()
    for state, row, _ in specs:
        box = (0, row * CH, 8 * CW, (row + 1) * CH)
        assert ImageChops.difference(new.crop(box), classic.crop(box)).convert("RGB").getbbox() is not None, state
    print("ok", OUT)


if __name__ == "__main__":
    main()
