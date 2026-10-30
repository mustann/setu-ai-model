"""
Generate local demo image assets for SIH 2026 scenarios and tests.
Creates:
1. overhead_tank.jpg (Water Supply - blue tones, tank structure, water flow)
2. pothole_road.jpg (Roads - textured asphalt, dark pothole crater)
3. sparking_wire.jpg (Electricity - wires, power pole, bright sparks)
4. garbage_dump.jpg (Sanitation - multi-colored debris, dustbin)
5. selfie_mismatch.jpg (Mismatch - portrait face / skin tones)
6. blurry_sample.jpg (Blurry image with Gaussian blur)
"""

from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).resolve().parent.parent / "data" / "demo_assets"


def make_overhead_tank() -> Image.Image:
    # 400x300 image
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    # Sky background (light blue)
    img[:150, :] = [210, 180, 135]  # BGR
    # Ground (gray concrete)
    img[150:, :] = [120, 120, 120]
    # Water tank cylinder (metallic blue-gray)
    cv2.rectangle(img, (120, 40), (280, 140), (180, 140, 90), -1)
    cv2.ellipse(img, (200, 40), (80, 20), 0, 0, 360, (200, 160, 110), -1)
    cv2.ellipse(img, (200, 140), (80, 20), 0, 0, 360, (150, 110, 70), -1)
    # Pillars
    cv2.rectangle(img, (130, 140), (150, 260), (90, 90, 90), -1)
    cv2.rectangle(img, (250, 140), (270, 260), (90, 90, 90), -1)
    # Cascading water stream (bright blue/white)
    for i in range(50):
        x = np.random.randint(260, 285)
        y1 = np.random.randint(120, 140)
        y2 = np.random.randint(220, 280)
        cv2.line(img, (x, y1), (x + np.random.randint(-5, 10), y2), (255, 230, 180), 2)
    # Water pool on ground
    cv2.ellipse(img, (270, 260), (90, 25), 0, 0, 360, (240, 200, 140), -1)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def make_pothole_road() -> Image.Image:
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    # Asphalt road texture (dark gray with noise)
    noise = np.random.randint(60, 95, (300, 400), dtype=np.uint8)
    img[:, :, 0] = noise
    img[:, :, 1] = noise
    img[:, :, 2] = noise
    # Yellow lane divider line
    cv2.line(img, (200, 0), (200, 300), (40, 215, 240), 6)
    # Large ragged pothole in center
    cv2.ellipse(img, (180, 160), (75, 45), 15, 0, 360, (25, 25, 25), -1)
    # Rough fractured edges around pothole
    for _ in range(40):
        pt1 = (np.random.randint(110, 260), np.random.randint(120, 200))
        pt2 = (pt1[0] + np.random.randint(-15, 15), pt1[1] + np.random.randint(-15, 15))
        cv2.line(img, pt1, pt2, (15, 15, 15), 2)
    # Broken stones / rubble in hole
    for _ in range(25):
        cv2.circle(img, (np.random.randint(130, 230), np.random.randint(135, 185)), np.random.randint(2, 5), (140, 140, 140), -1)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def make_sparking_wire() -> Image.Image:
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    # Night sky
    img[:] = [30, 25, 20]
    # Electric pole
    cv2.rectangle(img, (100, 50), (125, 300), (100, 100, 100), -1)
    cv2.rectangle(img, (60, 80), (200, 95), (80, 80, 80), -1)
    # Overhead wires
    cv2.line(img, (0, 85), (400, 120), (180, 180, 180), 2)
    cv2.line(img, (0, 95), (400, 145), (180, 180, 180), 2)
    # Broken dangling wire
    cv2.line(img, (220, 105), (260, 210), (220, 220, 220), 3)
    # Intense yellow/white spark at wire tip
    cv2.circle(img, (260, 210), 12, (255, 255, 255), -1)
    cv2.circle(img, (260, 210), 24, (50, 220, 255), 2)
    # Sparks shooting out
    for _ in range(30):
        angle = np.random.uniform(0, 2 * np.pi)
        length = np.random.randint(10, 45)
        end_x = int(260 + length * np.cos(angle))
        end_y = int(210 + length * np.sin(angle))
        cv2.line(img, (260, 210), (end_x, end_y), (100, 240, 255), 1)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def make_garbage_dump() -> Image.Image:
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    # Road and wall
    img[:120, :] = [140, 150, 160]
    img[120:, :] = [90, 90, 90]
    # Green municipal bin
    cv2.rectangle(img, (70, 80), (150, 200), (50, 140, 60), -1)
    # Piles of trash and plastic bags
    colors = [(40, 40, 220), (200, 200, 40), (220, 40, 40), (240, 240, 240), (30, 30, 30)]
    for _ in range(80):
        cx = np.random.randint(120, 360)
        cy = np.random.randint(150, 280)
        r = np.random.randint(8, 22)
        c = colors[np.random.randint(0, len(colors))]
        cv2.circle(img, (cx, cy), r, c, -1)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def make_selfie_mismatch() -> Image.Image:
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    # Background wall
    img[:] = [220, 220, 230]
    # Large human face occupying center (> 50% skin tone)
    # Skin tone BGR: ~ (150, 180, 230)
    cv2.ellipse(img, (200, 150), (110, 130), 0, 0, 360, (140, 175, 230), -1)
    # Hair
    cv2.ellipse(img, (200, 70), (115, 60), 0, 0, 180, (40, 30, 25), -1)
    # Eyes
    cv2.circle(img, (165, 130), 12, (255, 255, 255), -1)
    cv2.circle(img, (165, 130), 6, (40, 30, 25), -1)
    cv2.circle(img, (235, 130), 12, (255, 255, 255), -1)
    cv2.circle(img, (235, 130), 6, (40, 30, 25), -1)
    # Smile
    cv2.ellipse(img, (200, 200), (35, 18), 0, 0, 180, (60, 50, 180), 3)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def make_blurry_sample() -> Image.Image:
    base = make_pothole_road()
    cv_img = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)
    # Apply severe Gaussian blur
    blurred = cv2.GaussianBlur(cv_img, (45, 45), 25)
    return Image.fromarray(cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB))


def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    assets = {
        "overhead_tank.jpg": make_overhead_tank(),
        "pothole_road.jpg": make_pothole_road(),
        "sparking_wire.jpg": make_sparking_wire(),
        "garbage_dump.jpg": make_garbage_dump(),
        "selfie_mismatch.jpg": make_selfie_mismatch(),
        "blurry_sample.jpg": make_blurry_sample(),
    }
    for fname, im in assets.items():
        out_path = ASSETS_DIR / fname
        im.save(out_path, quality=92)
        print(f"Created demo asset: {out_path}")


if __name__ == "__main__":
    main()
