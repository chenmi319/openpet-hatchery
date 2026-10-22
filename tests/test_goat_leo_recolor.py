"""号码遮挡回归：真实蓝白源帧验证笔画与袖口边界，覆盖发布和候选配色。"""

import hashlib
import runpy
import unittest
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
R = runpy.run_path(str(ROOT / "pets/goat-leo/recolor/recolor.py"))


class GoatLeoRecolorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with Image.open(ROOT / "dist/goat-leo/spritesheet.webp") as sheet:
            cls.sheet = sheet.convert("RGBA")

    def cell(self, row, index):
        return self.sheet.crop((index * 192, row * 208, (index + 1) * 192, (row + 1) * 208))

    def test_occluded_number_and_outline_boundaries(self):
        third = self.cell(1, 2)
        # 源图改变时必须复核遮罩，不能悄悄退回漏换结果。
        self.assertEqual(hashlib.sha256(third.tobytes()).hexdigest(), R["OCCLUDED_NUMBER_FRAME"])
        cases = (
            (0, [(89, 82), (94, 84)], [(99, 90), (98, 93)]),
            (2, [(86, 84), (85, 85), (89, 85), (92, 86), (91, 88), (90, 91)],
             [(82, 84), (95, 87), (94, 88), (93, 89)]),
            (5, [(86, 84), (85, 86), (90, 85)], [(82, 84), (95, 87), (96, 86)]),
        )
        for index, number, outline in cases:
            cell = self.cell(1, index)
            for _, color, stripes, palette in R["KITS"].values():
                with self.subTest(frame=index + 1, color=color):
                    result = R["recolor"](cell, color, stripes, palette)
                    for point in number:
                        self.assertEqual(result.getpixel(point)[:3], color, point)
                    for point in outline:
                        self.assertNotIn(point, R["number_pixels"](cell))
                        self.assertNotEqual(result.getpixel(point)[:3], color, point)
                        # 红蓝会重映射藏青抗锯齿；蓝白金必须原样保护袖口。
                        if not stripes:
                            self.assertEqual(result.getpixel(point), cell.getpixel(point), point)

    def test_all_frames_have_numbers_and_preserve_non_kit_pixels(self):
        for state, (row, count) in R["ROWS"].items():
            for index in range(count):
                cell = self.cell(row, index)
                number = R["number_pixels"](cell)
                self.assertTrue(number, (state, index + 1))
                for _, color, stripes, palette in R["KITS"].values():
                    with self.subTest(state=state, frame=index + 1, color=color):
                        result = R["recolor"](cell, color, stripes, palette)
                        self.assertEqual(result.getchannel("A").tobytes(), cell.getchannel("A").tobytes())
                        allowed = R["kit_region"](cell, number) if stripes else number
                        difference = ImageChops.difference(result, cell).convert("RGB")
                        for x, y in allowed:
                            difference.putpixel((x, y), (0, 0, 0))
                        self.assertIsNone(difference.getbbox())
                        for point in number:
                            self.assertEqual(result.getpixel(point)[:3], color)

    def test_released_recolors_stay_pixel_identical(self):
        # 配色调整不能悄悄改变已验收图集；发布物与重建结果必须一致。
        for kit in ("red-blue-legend", "golden-farewell", "flamingo-pink"):
            _, color, stripes, palette = R["KITS"][kit]
            with Image.open(ROOT / f"dist/goat-leo/outfits/{kit}.webp") as image:
                atlas = image.convert("RGBA")
            for row, count in R["ROWS"].values():
                for index in range(count):
                    result = R["recolor"](self.cell(row, index), color, stripes, palette)
                    expected = atlas.crop((index * 192, row * 208, (index + 1) * 192, (row + 1) * 208))
                    self.assertEqual(result.tobytes(), expected.tobytes(), (kit, row, index))


if __name__ == "__main__":
    unittest.main()
