# zed-test

A small grab-bag of Python: a tested dice roller plus a from-scratch
**fractal + music pipeline** that renders Mandelbrot art, animates deep zooms,
synthesizes a mellow techno track, and fuses the two into a beat-synced video.

## Setup

Uses a virtual environment (the system Python on some distros is
externally managed, so installing globally is blocked).

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run everything with `.venv/bin/python` (or `source .venv/bin/activate` first).

## Contents

| File | What it does |
|------|--------------|
| `dice.py` | Simulates rolling two dice and prints the total. |
| `test_dice.py` | Pytest tests for the dice roller. |
| `mandelbrot.py` | Vectorized Mandelbrot renderer with smooth coloring → PNG. |
| `zoom.py` | Animated zoom into the Seahorse Valley spiral → GIF. |
| `techno.py` | NumPy synthesizer (kick, sub bass, pads, hats, arpeggio) → WAV. |
| `beatzoom.py` | Beat-synced fractal zoom muxed with the track → MP4. |

## Usage

Run the tests:

```bash
.venv/bin/python -m pytest
```

Roll the dice:

```bash
.venv/bin/python dice.py
```

Render a fractal still (try `--preset seahorse`, `spiral`, `elephant`, `minibrot`):

```bash
.venv/bin/python mandelbrot.py --preset seahorse -o seahorse.png
```

Animate a deep zoom (~175M× magnification):

```bash
.venv/bin/python zoom.py --start 1.4 --end 8e-9 --frames 90 --size 500 \
    --max-iters 2500 -o zoom_deep.gif
```

Synthesize the mellow techno track (A minor, 116 BPM, ~34s):

```bash
.venv/bin/python techno.py            # -> techno.wav
```

Render the beat-synced video (zoom punches inward and flashes on each kick;
requires `ffmpeg`):

```bash
.venv/bin/python beatzoom.py          # techno.wav -> beatzoom.mp4
```

## Notes

Generated media (`*.png`, `*.gif`, `*.wav`, `*.mp4`), caches, and `.venv/`
are gitignored — everything is reproducible from the scripts above.

## License

[MIT](LICENSE)
