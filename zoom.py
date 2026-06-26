"""Animated Mandelbrot zoom -> GIF.

Geometrically zooms into the Seahorse Valley spiral, ramping the iteration
count as the view shrinks so deep detail stays crisp. Each frame is colored
with a matplotlib colormap and the sequence is written to an animated GIF.

Examples
--------
    python zoom.py                       # 60-frame zoom into the spiral
    python zoom.py --frames 90 --size 700 -o deep.gif
    python zoom.py -x -0.745428 -y 0.113009 --end 5e-5
"""

import argparse

import matplotlib
import numpy as np
from PIL import Image

from mandelbrot import mandelbrot

# The classic Seahorse Valley deep-zoom point; holds detail to extreme depth.
SPIRAL_X, SPIRAL_Y = -0.7436438870375158, 0.1318259042053119


def colorize(values, cmap):
    """Map a normalized escape array to an RGB uint8 image."""
    rgba = cmap(np.sqrt(values))  # sqrt stretch boosts deep-region contrast
    return (rgba[..., :3] * 255).astype(np.uint8)


def main():
    p = argparse.ArgumentParser(description="Render an animated Mandelbrot zoom GIF.")
    p.add_argument("-x", type=float, default=SPIRAL_X, help="zoom target x")
    p.add_argument("-y", type=float, default=SPIRAL_Y, help="zoom target y")
    p.add_argument("--start", type=float, default=1.4, help="starting half-width")
    p.add_argument("--end", type=float, default=4e-4, help="final half-width")
    p.add_argument("--frames", type=int, default=60)
    p.add_argument("--size", type=int, default=600, help="frame size in pixels")
    p.add_argument("--base-iters", type=int, default=300)
    p.add_argument("--max-iters", type=int, default=1400)
    p.add_argument("--fps", type=int, default=20)
    p.add_argument("--cmap", default="twilight_shifted")
    p.add_argument("-o", "--out", default="zoom.gif")
    args = p.parse_args()

    cmap = matplotlib.colormaps[args.cmap]
    # Geometric (constant-ratio) schedule -> visually uniform zoom speed.
    half_widths = np.geomspace(args.start, args.end, args.frames)

    frames = []
    for i, hw in enumerate(half_widths):
        # Ramp iterations from base->max as we descend, scaled by zoom depth.
        depth = np.log(args.start / hw) / np.log(args.start / args.end)
        iters = int(args.base_iters + depth * (args.max_iters - args.base_iters))
        values = mandelbrot(args.x, args.y, hw, args.size, args.size, iters)
        frames.append(Image.fromarray(colorize(values, cmap)))
        print(f"frame {i + 1}/{args.frames}  half-width {hw:.2e}  iters {iters}")

    # Bounce: play forward then back so the loop breathes instead of snapping.
    sequence = frames + frames[-2:0:-1]
    duration_ms = int(1000 / args.fps)
    sequence[0].save(
        args.out,
        save_all=True,
        append_images=sequence[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    print(f"Saved {args.out} ({len(sequence)} frames)")


if __name__ == "__main__":
    main()
