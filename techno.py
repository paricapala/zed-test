"""Mellow techno track synthesized from scratch with NumPy -> WAV.

No samples, no external synths: every sound (kick, sub bass, pads, hats,
arpeggio) is generated mathematically, shaped with ADSR envelopes, warmed
with a one-pole low-pass filter, and mixed down to a 16-bit stereo WAV.

Vibe: deep/mellow techno, A minor, 116 BPM, four-on-the-floor.

    python techno.py                 # -> techno.wav (~33s, 16 bars)
    python techno.py --bars 32 -o long.wav
"""

import argparse
import wave

import numpy as np

SR = 44100  # sample rate


# ----------------------------------------------------------------------------
# Building blocks
# ----------------------------------------------------------------------------
def note(name, octave):
    """Equal-tempered frequency for e.g. note('A', 4) -> 440.0 Hz."""
    semis = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4,
             "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    n = semis[name] + (octave - 4) * 12
    return 440.0 * 2 ** (n / 12)


def adsr(n, a, d, s, r, sustain=0.7):
    """Sample-count ADSR envelope normalized to length n."""
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    a, d, r = max(a, 1), max(d, 1), max(r, 1)
    s_len = max(n - a - d - r, 0)
    env = np.concatenate([
        np.linspace(0, 1, a),
        np.linspace(1, sustain, d),
        np.full(s_len, sustain),
        np.linspace(sustain, 0, r),
    ])
    return np.resize(env, n)


def lowpass(x, cutoff):
    """Cheap one-pole low-pass for analog-style warmth."""
    dt = 1.0 / SR
    rc = 1.0 / (2 * np.pi * cutoff)
    alpha = dt / (rc + dt)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alpha * (x[i] - acc)
        y[i] = acc
    return y


def saw(freq, n):
    t = np.arange(n) / SR
    return 2 * (t * freq - np.floor(0.5 + t * freq))


def sine(freq, n):
    return np.sin(2 * np.pi * freq * np.arange(n) / SR)


# ----------------------------------------------------------------------------
# Instruments
# ----------------------------------------------------------------------------
def kick(dur=0.32):
    """Punchy sub kick: a sine whose pitch drops fast."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    pitch = 110 * np.exp(-t * 28) + 42        # 110Hz -> 42Hz sub
    phase = 2 * np.pi * np.cumsum(pitch) / SR
    body = np.sin(phase) * np.exp(-t * 6)
    click = np.exp(-t * 200) * 0.4            # transient snap
    return np.tanh((body + click) * 1.4)


def hat(dur=0.05, cutoff=9000):
    """Short filtered-noise hi-hat."""
    n = int(dur * SR)
    noise = np.random.default_rng(0).standard_normal(n)
    return noise * np.exp(-np.arange(n) / SR * 60) * 0.5


def bass(freq, dur):
    """Round sine sub + a touch of saw, low-passed."""
    n = int(dur * SR)
    tone = sine(freq, n) * 0.8 + saw(freq, n) * 0.2
    tone = lowpass(tone, 220)
    return tone * adsr(n, 0.005, 0.05, 0.04, 0.08, sustain=0.85)


def pad(freqs, dur):
    """Lush detuned-saw chord pad, slow attack, gently filtered."""
    n = int(dur * SR)
    mix = np.zeros(n)
    for f in freqs:
        mix += saw(f, n) + saw(f * 1.005, n) + saw(f * 0.995, n)  # detune
    mix = lowpass(mix / (len(freqs) * 3), 1400)
    return mix * adsr(n, 0.25, 0.2, 0.7, 0.6, sustain=0.7) * 0.6


def pluck(freq, dur):
    """Soft sine arpeggio note with quick decay."""
    n = int(dur * SR)
    tone = sine(freq, n) * 0.7 + sine(freq * 2, n) * 0.15
    return tone * adsr(n, 0.004, 0.12, 0.0, 0.05, sustain=0.0)


def delay(x, time=0.34, feedback=0.35, mix=0.4):
    """Tempo-ish echo for spacious arps."""
    d = int(time * SR)
    out = x.copy()
    tap = np.zeros(len(x) + d * 6)
    tap[:len(x)] = x
    for k in range(1, 6):
        tap[k * d:k * d + len(x)] += x * (feedback ** k)
    return (1 - mix) * out + mix * tap[:len(x)]


# ----------------------------------------------------------------------------
# Arrangement
# ----------------------------------------------------------------------------
def add(buf, sound, at):
    """Mix `sound` into stereo-mono buffer `buf` starting at sample `at`."""
    end = min(at + len(sound), len(buf))
    if at < len(buf):
        buf[at:end] += sound[:end - at]


def main():
    p = argparse.ArgumentParser(description="Synthesize a mellow techno WAV.")
    p.add_argument("--bpm", type=float, default=116)
    p.add_argument("--bars", type=int, default=16)
    p.add_argument("-o", "--out", default="techno.wav")
    args = p.parse_args()

    beat = 60.0 / args.bpm
    step = beat / 4                       # 16th-note grid
    spb = int(beat * SR)                  # samples per beat
    total = int(args.bars * 4 * beat * SR) + SR
    L = np.zeros(total)
    R = np.zeros(total)

    # i - VI - III - VII in A minor: Am - F - C - G, one chord per bar.
    prog = [
        ("A", [note("A", 2), note("A", 3), note("C", 4), note("E", 4)]),
        ("F", [note("F", 2), note("F", 3), note("A", 3), note("C", 4)]),
        ("C", [note("C", 2), note("C", 3), note("E", 3), note("G", 3)]),
        ("G", [note("G", 2), note("G", 3), note("B", 3), note("D", 4)]),
    ]

    k, h = kick(), hat()
    rng = np.random.default_rng(7)

    for bar in range(args.bars):
        bar_start = int(bar * 4 * beat * SR)
        root_name, chord = prog[bar % len(prog)]
        root = chord[0]

        # --- Pad: full bar, fades in after the 2-bar intro ---
        if bar >= 2:
            pad_gain = min((bar - 1) / 4, 1.0) * 0.9
            add(L, pad(chord, 4 * beat) * pad_gain, bar_start)
            add(R, pad([f * 1.002 for f in chord], 4 * beat) * pad_gain, bar_start)

        for b in range(4):                # four beats per bar
            beat_at = bar_start + b * spb
            # Four-on-the-floor kick.
            add(L, k, beat_at)
            add(R, k, beat_at)
            # Offbeat hats (the "and" of each beat), softly.
            if bar >= 1:
                add(L, h * 0.5, beat_at + spb // 2)
                add(R, h * 0.5, beat_at + spb // 2)
            # Bass: root on the beat, with an octave hop on beat 3.
            if bar >= 1:
                bf = root * (2 if b == 2 else 1)
                add(L, bass(bf, beat) * 0.9, beat_at)
                add(R, bass(bf, beat) * 0.9, beat_at)

        # --- Arpeggio: gentle 16th plucks over the chord, from bar 4 ---
        if bar >= 4:
            pattern = [0, 2, 1, 3, 2, 3, 1, 2]   # indices into chord (+oct)
            arp = np.zeros(int(4 * beat * SR) + SR)
            for i in range(16):
                idx = pattern[i % len(pattern)]
                f = chord[idx] * 2                # up an octave, airy
                at = int(i * step * SR)
                add(arp, pluck(f, step * 1.6) * 0.35, at)
            arp = delay(arp)
            add(L, arp, bar_start)
            add(R, np.roll(arp, int(0.012 * SR)), bar_start)  # stereo spread

    # Master: soft-clip, normalize, gentle fade in/out.
    mix = np.stack([L, R], axis=1)
    mix = np.tanh(mix * 0.8)
    mix /= np.max(np.abs(mix)) + 1e-9
    fade = int(0.8 * SR)
    mix[:fade] *= np.linspace(0, 1, fade)[:, None]
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]

    pcm = (mix * 32767 * 0.92).astype(np.int16)
    with wave.open(args.out, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    dur = len(mix) / SR
    print(f"Saved {args.out}  ({dur:.1f}s, {args.bars} bars @ {args.bpm:g} BPM)")


if __name__ == "__main__":
    main()
