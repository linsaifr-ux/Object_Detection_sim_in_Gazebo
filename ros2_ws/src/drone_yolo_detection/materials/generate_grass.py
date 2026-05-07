"""Generate CC0 grass PBR textures procedurally."""
import numpy as np
from PIL import Image
import os

OUT = os.path.join(os.path.dirname(__file__), 'textures')
os.makedirs(OUT, exist_ok=True)

RNG = np.random.default_rng(42)
SIZE = 1024


def smooth_noise(size, scale):
    """Bilienar-upsampled noise for natural variation."""
    small = RNG.random((size // scale, size // scale)).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8))
    return np.array(img.resize((size, size), Image.BILINEAR)) / 255.0


def fbm(size, octaves=6):
    """Fractional Brownian Motion for natural-looking noise."""
    result = np.zeros((size, size), dtype=np.float32)
    amp, freq = 0.5, 2
    for _ in range(octaves):
        result += amp * smooth_noise(size, max(1, size // freq))
        amp *= 0.5
        freq *= 2
    return (result - result.min()) / (result.max() - result.min())


def grass_blades(size, count=18000):
    """Add grass blade strokes as bright vertical streaks."""
    canvas = np.zeros((size, size), dtype=np.float32)
    xs = RNG.integers(0, size, count)
    ys = RNG.integers(0, size, count)
    lengths = RNG.integers(4, 18, count)
    for x, y, l in zip(xs, ys, lengths):
        y2 = min(size - 1, y + l)
        canvas[y:y2, x] = RNG.uniform(0.3, 1.0)
    # Blur slightly
    from PIL import ImageFilter
    img = Image.fromarray((canvas * 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    return np.array(img) / 255.0


print("Generating albedo map...")
base = fbm(SIZE, octaves=7)
blades = grass_blades(SIZE)

# Green palette: dark soil gaps → bright grass tips
dark_r  = np.array([25,  55,  20], dtype=np.float32) / 255
mid_r   = np.array([50,  100, 30], dtype=np.float32) / 255
light_r = np.array([90,  150, 45], dtype=np.float32) / 255
tip_r   = np.array([140, 200, 70], dtype=np.float32) / 255

t = base[..., None]
albedo = (dark_r * (1 - t) + mid_r * t)

blade_mask = blades[..., None]
albedo = albedo * (1 - blade_mask * 0.6) + light_r * blade_mask * 0.4 + tip_r * blade_mask * 0.2

# Add subtle hue variation
hue_shift = fbm(SIZE, octaves=4)[..., None] * 0.08
albedo[..., 0] += hue_shift[..., 0] * 20 / 255
albedo[..., 1] -= hue_shift[..., 0] * 10 / 255
albedo = np.clip(albedo, 0, 1)

albedo_img = Image.fromarray((albedo * 255).astype(np.uint8))
albedo_img.save(os.path.join(OUT, 'grass_albedo.png'))
print(f"  Saved grass_albedo.png ({SIZE}x{SIZE})")


print("Generating normal map...")
height = fbm(SIZE, octaves=5) * 0.5 + blades * 0.5
# Sobel-like gradient
dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
strength = 3.0
nx = -dx * strength
ny = -dy * strength
nz = np.ones((SIZE, SIZE), dtype=np.float32)
length = np.sqrt(nx**2 + ny**2 + nz**2)
nx /= length; ny /= length; nz /= length
normal = np.stack([(nx + 1) * 0.5, (ny + 1) * 0.5, (nz + 1) * 0.5], axis=-1)
normal_img = Image.fromarray((normal * 255).astype(np.uint8))
normal_img.save(os.path.join(OUT, 'grass_normal.png'))
print(f"  Saved grass_normal.png ({SIZE}x{SIZE})")


print("Generating roughness map...")
# Grass is rough; wet patches slightly smoother
rough_base = fbm(SIZE, octaves=4)
roughness = 0.75 + rough_base * 0.2 - blades * 0.1
roughness = np.clip(roughness, 0.55, 0.95)
rough_img = Image.fromarray((roughness * 255).astype(np.uint8))
rough_img.save(os.path.join(OUT, 'grass_roughness.png'))
print(f"  Saved grass_roughness.png ({SIZE}x{SIZE})")

print("\nAll textures generated successfully.")
