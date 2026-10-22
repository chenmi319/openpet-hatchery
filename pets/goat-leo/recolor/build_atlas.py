#!/usr/bin/env python3
"""套装图集 = 蓝白九行原帧换色（见 recolor.py）；动作、表情、位置与蓝白逐帧一致。用法：build_atlas.py [套装]"""

from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[3]
CW, CH = 192, 208
# 套装 → (中间帧目录, 输出图集)；与 recolor.KITS 的目录一致
KITS = {
    "red-blue-legend": ("work/goat-leo/redblue-redraw", "dist/goat-leo/outfits/red-blue-legend.webp"),
    "golden-farewell": ("work/goat-leo/golden-recolor", "dist/goat-leo/outfits/golden-farewell.webp"),
    "flamingo-pink": ("work/goat-leo/pink-recolor", "dist/goat-leo/outfits/flamingo-pink.webp"),
}


def main(kit: str) -> None:
    work, out = ROOT / KITS[kit][0], ROOT / KITS[kit][1]
    scripts = ROOT / ".opencode/skills/hatch-pet/scripts"
    specs = runpy.run_path(str(scripts / "compose_atlas.py"))["ROW_SPECS"]
    classic = Image.open(ROOT / "dist/goat-leo/spritesheet.webp").convert("RGBA")
    root = work / "atlas-frames"
    for state, row, n in specs:
        d = root / state
        d.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            cell = Image.open(work / "frames-recolor" / state / f"{i:02d}.png").convert("RGBA")
            assert cell.size == (CW, CH), (state, i, cell.size)
            cell.save(d / f"{i:02d}.png")
    png = work / f"{kit}.png"
    subprocess.run(
        [sys.executable, str(scripts / "compose_atlas.py"), "--frames-root", str(root), "--output", str(png), "--webp-output", str(out)],
        check=True,
    )
    # 轮廓与蓝白一致（只换色不改形），且每行确实换了色
    new = Image.open(out).convert("RGBA")
    assert new.getchannel("A").tobytes() == classic.getchannel("A").tobytes()
    for state, row, _ in specs:
        box = (0, row * CH, 8 * CW, (row + 1) * CH)
        assert ImageChops.difference(new.crop(box), classic.crop(box)).convert("RGB").getbbox() is not None, state
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "red-blue-legend")
