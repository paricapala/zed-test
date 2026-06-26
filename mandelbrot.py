"""Snazzy Mandelbrot fractal renderer.

Vectorized escape-time computation with smooth (continuous) iteration
coloring for gradient-free, banding-free images. Renders headlessly to a
high-resolution PNG, so it works fine over SSH / in a plain terminal.

Examples
--------
    python mandelbrot.py                      # classic full view
    python mandelbrot.py --preset seahorse    # zoom into Seahorse Valley
    python mandelbrot.py --preset spiral -o spiral.png
    python mandelbrot.py -x -0.745 -y 0.113 --zoom 800 --iters 2000
"""

import argparse

import matplotlib

matplotlib.use("Agg")  # headless backend: render straight to a file

import matplotlib.pyplot as plt
import numpy as np

# Famous coordinates worth zooming into. (center_x, center_y, half_width).
PRESETS = {
    "full": (-0.6, 0.0, 1.6),
    "seahorse": (-0.743, 0.131, 0.012),
    "spiral": (-0.7435, 0.1314, 0.0018),
    "elephant": (0.2750, 0.0070, 0.020),
    "minibrot": (-1.7497, 0.0000, 0.0007),
}


def mandelbrot(center_x, center_y, half_width, width, height, max_iters):
    """Return a smooth escape-time array for the requested viewport."""
    aspect = height / width
    xs = np.linspace(center_x - half_width, center_x + half_width, width)
    ys = np.linspace(
        center_y - half_width * aspect, center_y + half_width * aspect, height
    )
    c = xs[np.newaxis, :] + 1j * ys[:, np.newaxis]

    z = np.zeros_like(c)
    escape = np.full(c.shape, max_iters, dtype=float)
    alive = np.ones(c.shape, dtype=bool)

    for n in range(max_iters):
        z[alive] = z[alive] * z[alive] + c[alive]
        escaped = alive & (np.abs(z) > 2.0)
        # Smooth coloring: fractional iteration count removes color banding.
        zmag = np.abs(z[escaped])
        escape[escaped] = n + 1 - np.log(np.log(zmag)) / np.log(2)
        alive &= ~escaped

    # Points that never escaped stay maxed out; normalize for the colormap.
    return escape / max_iters


def render(values, out_path, cmap):
    height, width = values.shape
    dpi = 100
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])  # fill the whole frame, no borders
    ax.set_axis_off()
    # sqrt stretch gives the deep regions more color contrast.
    ax.imshow(np.sqrt(values), cmap=cmap, origin="lower", interpolation="bilinear")
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description="Render a Mandelbrot fractal to PNG.")
    p.add_argument("--preset", choices=PRESETS, default="full")
    p.add_argument("-x", type=float, help="center x (overrides preset)")
    p.add_argument("-y", type=float, help="center y (overrides preset)")
    p.add_argument("--zoom", type=float, help="zoom factor relative to full view")
    p.add_argument("--width", type=int, default=1600)
    p.add_argument("--height", type=int, default=1200)
    p.add_argument("--iters", type=int, default=600, help="max iterations")
    p.add_argument("--cmap", default="twilight_shifted", help="matplotlib colormap")
    p.add_argument("-o", "--out", default="mandelbrot.png")
    args = p.parse_args()

    cx, cy, half_width = PRESETS[args.preset]
    if args.x is not None:
        cx = args.x
    if args.y is not None:
        cy = args.y
    if args.zoom is not None:
        half_width = 1.6 / args.zoom

    print(
        f"Rendering {args.width}x{args.height} @ ({cx}, {cy}), "
        f"half-width {half_width:g}, {args.iters} iters..."
    )
    values = mandelbrot(cx, cy, half_width, args.width, args.height, args.iters)
    render(values, args.out, args.cmap)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
