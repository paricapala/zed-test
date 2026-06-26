"""Beat-synced Mandelbrot zoom video, muxed with the techno track -> MP4.

Renders a continuous fractal zoom whose motion is locked to the song's
tempo: on every kick (each beat) the view punches inward a touch and the
image flashes brighter, so the visuals pulse in time with the music.

Frames are streamed straight to ffmpeg as raw RGB (no temp PNGs), and the
audio track is muxed in, trimmed to the shorter of the two streams.

    python beatzoom.py                       # techno.wav -> beatzoom.mp4
    python beatzoom.py --bpm 116 --fps 24 --end 3e-5 -o sync.mp4
"""

import argparse
import subprocess
import sys
import wave

import matplotlib
import numpy as np

from mandelbrot import mandelbrot
from zoom import SPIRAL_X, SPIRAL_Y, colorize


def audio_duration(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def main():
    p = argparse.ArgumentParser(description="Render a beat-synced Mandelbrot zoom MP4.")
    p.add_argument("--audio", default="techno.wav")
    p.add_argument("--bpm", type=float, default=116)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--size", type=int, default=480, help="frame size (even number)")
    p.add_argument("-x", type=float, default=SPIRAL_X)
    p.add_argument("-y", type=float, default=SPIRAL_Y)
    p.add_argument("--start", type=float, default=1.4, help="starting half-width")
    p.add_argument("--end", type=float, default=3e-5, help="final half-width")
    p.add_argument("--base-iters", type=int, default=220)
    p.add_argument("--max-iters", type=int, default=1200)
    p.add_argument("--punch", type=float, default=0.05, help="zoom kick depth")
    p.add_argument("--flash", type=float, default=0.22, help="brightness flash amount")
    p.add_argument("--cmap", default="twilight_shifted")
    p.add_argument("-o", "--out", default="beatzoom.mp4")
    args = p.parse_args()

    size = args.size - (args.size % 2)  # libx264 needs even dimensions
    cmap = matplotlib.colormaps[args.cmap]
    dur = audio_duration(args.audio)
    n_frames = round(dur * args.fps)
    beat = 60.0 / args.bpm
    # Decay so a beat's flash/punch has nearly faded by the next beat.
    decay = 6.6

    ff = subprocess.Popen(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{size}x{size}", "-r", str(args.fps), "-i", "-",
            "-i", args.audio,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
            "-shortest", args.out,
        ],
        stdin=subprocess.PIPE,
    )

    log_ratio = np.log(args.start / args.end)
    for i in range(n_frames):
        t = i / args.fps
        # Position along the geometric zoom (0 -> 1) and per-beat phase.
        u = t / dur
        frac = (t / beat) % 1.0
        env = np.exp(-frac * decay)                 # spike on the beat, decays

        base_hw = args.start * (args.end / args.start) ** u
        half_width = base_hw * (1 - args.punch * env)  # punch inward on the kick

        depth = np.log(args.start / half_width) / log_ratio
        iters = int(args.base_iters + depth * (args.max_iters - args.base_iters))

        values = mandelbrot(args.x, args.y, half_width, size, size, iters)
        rgb = colorize(values, cmap).astype(np.float32)
        rgb *= 1 + args.flash * env                 # flash brighter on the kick
        frame = np.clip(rgb, 0, 255).astype(np.uint8)

        ff.stdin.write(frame.tobytes())
        if i % 24 == 0 or i == n_frames - 1:
            print(f"frame {i + 1}/{n_frames}  hw {half_width:.2e}  iters {iters}")
            sys.stdout.flush()

    ff.stdin.close()
    rc = ff.wait()
    if rc != 0:
        sys.exit(f"ffmpeg failed with code {rc}")
    print(f"Saved {args.out}  ({n_frames} frames @ {args.fps}fps, {dur:.1f}s)")


if __name__ == "__main__":
    main()
