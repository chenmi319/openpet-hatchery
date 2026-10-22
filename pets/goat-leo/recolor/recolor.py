#!/usr/bin/env python3
"""把蓝白黄金基准行按调色映射换成别的套装，头/手/眼神/节奏与蓝白逐像素一致。

用户在自查后选定此法：生图编辑的遮罩锁不住头和手，逐帧细节总会偏离蓝白。
红蓝：白→藏青、天蓝→石榴红（白与天蓝之间的抗锯齿按比例插值），胸前深色号码→黄，
短裤藏青→红蓝藏青。蓝白金：只把号码换成金色。粉黑：浅色球衣/球袜→粉，号码/短裤→近黑。
黑色描边、皮肤、头发、金靴、足球保持原像素。
用法：recolor.py [套装] [行...]，默认红蓝、九行。
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
CW, CH = 192, 208
ROWS = {
    "idle": (0, 6), "running-right": (1, 8), "running-left": (2, 8), "waving": (3, 4), "jumping": (4, 5),
    "failed": (5, 8), "waiting": (6, 6), "running": (7, 6), "review": (8, 6),
}
KIT_TOP = 60  # 眼白在此线以上，不能当作白色球衣
BALL_TOP = 128  # 九行所有帧的足球都在此线以下
WHITE, SKY = (240, 240, 240), (112, 192, 240)
NAVY, GARNET = (12, 40, 112), (168, 8, 52)
SHORTS_SRC, SHORTS_DST = (8, 36, 72), (8, 32, 96)
YELLOW = (250, 206, 24)
GOLD = (196, 146, 20)  # 号码压在白/天蓝条纹上，亮黄看不清，取偏深的金
PINK, BLACK = (244, 156, 184), (20, 20, 24)  # 概念粉黑，近黑保留短裤明暗层次
# 套装 → (中间帧目录, 号码色, 是否换条纹与短裤, 白/天蓝/短裤目标色)。
# 粉黑两种条纹使用同色；保留源图局部明暗，不保留蓝白色差。
KITS = {
    "red-blue-legend": ("work/goat-leo/redblue-redraw", YELLOW, True, (NAVY, GARNET, SHORTS_DST)),
    "golden-farewell": ("work/goat-leo/golden-recolor", GOLD, False, (NAVY, GARNET, SHORTS_DST)),  # 只换号码，条纹短裤保持蓝白
    "flamingo-pink": ("work/goat-leo/pink-recolor", BLACK, True, (PINK, PINK, BLACK)),
}
# 右跑第 3 帧号码与袖口同色且相连，纯颜色泛洪无法区分语义边界。
# 仅对已逐像素复核的蓝白原帧补号码遮罩；摘要绑定源像素，不能套到其他姿势。
# shortcut: 此遮罩仅适用当前蓝白源帧；替换基准图时须重新复核，回归测试会拦截旧摘要。
OCCLUDED_NUMBER_FRAME = "57ecdaddd9e89329b4a0d4972f3a620750a2993ac93f374941dcdd18612cd655"
OCCLUDED_NUMBER_SPANS = (
    (84, 85, 87), (85, 85, 92), (86, 84, 92), (87, 84, 92),
    (88, 84, 91), (89, 87, 91), (90, 87, 91), (91, 85, 90),
    (92, 85, 90), (93, 86, 89), (94, 87, 89),
)


def lum(c: tuple[int, ...]) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def mix(a: tuple[int, ...], b: tuple[int, ...], t: float) -> tuple[float, ...]:
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def scaled(c: tuple[float, ...], k: float) -> tuple[int, int, int]:
    r, g, b = (max(0, min(255, round(v * k))) for v in c)
    return r, g, b


def kit_class(c: tuple[int, ...]) -> str | None:
    r, g, b = c[:3]
    if lum(c) > 100 and ((max(c[:3]) - min(c[:3]) < 36 and min(c[:3]) > 100) or b > r + 20):
        return "light"
    if b > r + 15 and lum(c) < 120:
        return "dark"
    return None


def kit_region(cell: Image.Image, num: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """从必属球衣的天蓝/藏青像素出发，经球衣色4连通泛洪。

    足球、眼白也是白色，但与球衣之间隔着黑色描边，不会被泛洪到；用位置圈球会误伤贴着球的袜子。
    """
    px = cell.load()
    seeds = [
        (x, y)
        for y in range(KIT_TOP, CH)
        for x in range(CW)
        if px[x, y][3] > 200 and px[x, y][2] > px[x, y][0] + 40  # 球的阴影偶有 b-r≈30 的单像素，不能当种子
    ]
    # 球边缘也有几像素的青色抗锯齿团，会把整块白色球面泛洪成藏青；真球衣的种子团都很大
    left, kept = set(seeds), []
    while left:
        comp, st = [], [left.pop()]
        while st:
            x, y = st.pop()
            comp.append((x, y))
            for q in ((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                if q in left:
                    left.remove(q)
                    st.append(q)
        # 球都在 y>=128；更高处的小团是手臂与躯干间被描边封住的球衣缝隙，要保留
        if len(comp) >= 10 or max(y for _, y in comp) < BALL_TOP:
            kept += comp
    # 纯黑号码会把“0”的内孔与球衣隔开，号码本身也作种子才能泛洪进内孔
    seeds = kept + list(num)
    region = set(seeds)
    stack = list(seeds)
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if KIT_TOP <= ny < CH and 0 <= nx < CW and (nx, ny) not in region:
                p = px[nx, ny]
                if p[3] > 0 and kit_class(p) is not None:
                    region.add((nx, ny))
                    stack.append((nx, ny))
    return region


def number_pixels(cell: Image.Image) -> set[tuple[int, int]]:
    """胸前号码 = 被浅色球衣包围、不接触透明背景的深色连通块。

    深色含近黑像素（“1”的衬线是黑的）；衣摆/袖口描边连到外轮廓会碰到透明，领口太扁，靠高度排除。
    """
    px = cell.load()

    def dark(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        return a > 200 and lum((r, g, b)) < 120 and b + 12 >= r  # 号码有藏青也有纯黑

    sky = [x for y in range(KIT_TOP, 130) for x in range(CW) if px[x, y][3] > 200 and px[x, y][2] > px[x, y][0] + 60]
    chest_x = sum(sky) / len(sky)

    seen: set[tuple[int, int]] = set()
    out: set[tuple[int, int]] = set()
    for y0 in range(KIT_TOP, 130):
        for x0 in range(40, 152):
            if (x0, y0) in seen or not dark(x0, y0):
                continue
            comp, stack, open_edge = [], [(x0, y0)], False
            seen.add((x0, y0))
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not (0 <= nx < CW and 0 <= ny < CH) or px[nx, ny][3] < 40:
                        open_edge = True
                        continue
                    if ny >= KIT_TOP and (nx, ny) not in seen and dark(nx, ny):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            xs, ys = [p[0] for p in comp], [p[1] for p in comp]
            near_center = abs(sum(xs) / len(xs) - chest_x) < 16  # 侧身褶皱线也是封闭深色块，靠离胸口中线的距离排除
            w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            # 手臂遮挡可把“1”分成仅 3~4px 高的片段；仍由邻接浅色/实心度排除描边。
            if not open_edge and near_center and 6 <= len(comp) <= 300 and w <= 28 and 3 <= h <= 30:
                cs = set(comp)
                nb = {q for x, y in comp for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q not in cs}
                light = sum(kit_class(px[q]) == "light" for q in nb) / len(nb)
                fill = len(comp) / (w * h)
                # 侧身时袖口/领口描边也闭合在球衣内，但只有 1px 宽（fill 低）且一侧贴皮肤；号码四周全是浅色球衣，被手臂挡住时仍较实
                if light >= 0.9 or (fill >= 0.45 and len(comp) >= 30):
                    out.update(comp)
    if hashlib.sha256(cell.tobytes()).hexdigest() == OCCLUDED_NUMBER_FRAME:
        out.update(
            (x, y) for y, left, right in OCCLUDED_NUMBER_SPANS
            for x in range(left, right + 1) if dark(x, y)
        )
    return out


def recolor(
    cell: Image.Image, number: tuple[int, int, int] = YELLOW, stripes: bool = True,
    palette: tuple[tuple[int, int, int], ...] = (NAVY, GARNET, SHORTS_DST),
) -> Image.Image:
    cell = cell.convert("RGBA")
    out = cell.copy()
    src, dst = cell.load(), out.load()
    num = number_pixels(cell)
    region = kit_region(cell, num) if stripes else set()
    for x, y in region | num:
        r, g, b, a = src[x, y]
        c = (r, g, b)
        if (x, y) in num:
            dst[x, y] = (*number, a)
        elif kit_class(c) == "light":
            t = max(0.0, min(1.0, (b - r) / (SKY[2] - SKY[0])))
            base = mix(WHITE, SKY, t)
            dst[x, y] = (*scaled(mix(palette[0], palette[1], t), lum(c) / lum(base)), a)
        else:
            # 描边旁的抗锯齿像素比短裤亮得多，不限幅会被放大成亮蓝边
            dst[x, y] = (*scaled(palette[2], min(1.4, (lum(c) + 4) / (lum(SHORTS_SRC) + 4))), a)
    return out


def main(args: list[str]) -> None:
    kit = args.pop(0) if args and args[0] in KITS else "red-blue-legend"
    work, number, stripes, palette = KITS[kit]
    sheet = Image.open(ROOT / "dist/goat-leo/spritesheet.webp").convert("RGBA")
    for name in args or list(ROWS):
        row, n = ROWS[name]
        d = ROOT / work / "frames-recolor" / name
        d.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            cell = sheet.crop((i * CW, row * CH, (i + 1) * CW, (row + 1) * CH))
            new = recolor(cell, number, stripes, palette)
            # 只允许改球衣：y<KIT_TOP 的头部像素必须与蓝白完全一致
            assert new.crop((0, 0, CW, KIT_TOP)).tobytes() == cell.crop((0, 0, CW, KIT_TOP)).tobytes()
            assert new.getchannel("A").tobytes() == cell.getchannel("A").tobytes()
            new.save(d / f"{i:02d}.png")
            if not stripes:
                continue  # 条纹本就保留天蓝白，下面的漏换检查不适用
            # 不允许成片残留天蓝（漏换）；球边缘零星青色抗锯齿本就该保留
            q = new.load()
            left = sum(
                q[x, y][3] > 200 and q[x, y][2] > q[x, y][0] + 40 and lum(q[x, y]) > 110
                for y in range(KIT_TOP, CH)
                for x in range(CW)
            )
            assert left < 10, (name, i, left)
            # 球以上不得残留球衣浅色（号码内孔、手臂缝隙都算）；b>=r 排除偏暖的皮肤高光
            stray = [
                (x, y)
                for y in range(KIT_TOP, BALL_TOP)
                for x in range(CW)
                if q[x, y][3] > 200 and kit_class(q[x, y]) == "light" and q[x, y][2] >= q[x, y][0]
            ]
            assert not stray, (name, i, stray[:5])
        print("recolored", kit, name)


if __name__ == "__main__":
    main(sys.argv[1:])
