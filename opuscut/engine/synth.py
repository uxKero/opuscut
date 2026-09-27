"""Sound primitives driven by timeline.json. Write your own sound.py that imports this and builds the score.

  from synth import *
  mix = Mix()
  mix.add(kick(), at(0), bus="drums")
  mix.add(pluck(note("A3"), 0.8), at(4.5), pan=-0.3)
  mix.duck("music", by="drums", depth=0.5)
  mix.write("out/sound.wav")
"""
import json
import os
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt

ROOT = os.path.dirname(os.path.abspath(__file__))
SR = 48000
with open(os.path.join(ROOT, "timeline.json"), encoding="utf-8") as _f:
    TL = json.load(_f)
SPB = 60.0 / TL["bpm"]
LENGTH = TL["beats"] * SPB
_rng = np.random.default_rng(TL.get("seed", 7))

PITCH = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
         "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def at(beat):
    return beat * SPB


def note(name):
    return 440.0 * 2 ** ((12 * (int(name[-1]) + 1) + PITCH[name[:-1]] - 69) / 12)


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def filt(x, kind, cutoff, order=2):
    wn = [c / (SR / 2) for c in cutoff] if isinstance(cutoff, (list, tuple)) else cutoff / (SR / 2)
    sos = butter(order, wn, btype=kind, output="sos")
    return sosfilt(sos, x, axis=0)


def adsr(sec, a=0.005, d=0.1, s=0.7, r=0.1):
    t = t_axis(sec)
    env = np.where(t < a, t / max(a, 1e-6), np.where(t < a + d, 1 - (1 - s) * (t - a) / max(d, 1e-6), s))
    tail = np.clip((sec - t) / max(r, 1e-6), 0, 1)
    return env * tail


def osc(freq, sec, shape="sine", detune_cents=0.0):
    t = t_axis(sec)
    f = freq * 2 ** (detune_cents / 1200)
    ph = (f * t + _rng.random()) % 1.0
    if shape == "sine":
        return np.sin(2 * np.pi * ph)
    if shape == "saw":
        return 2 * ph - 1
    if shape == "square":
        return np.sign(np.sin(2 * np.pi * ph))
    if shape == "triangle":
        return 2 * np.abs(2 * ph - 1) - 1
    raise ValueError(shape)


def sweep(f0, f1, sec, shape="sine"):
    t = t_axis(sec)
    f = f0 * (f1 / f0) ** (t / sec)
    ph = np.cumsum(f) / SR
    return np.sin(2 * np.pi * ph) if shape == "sine" else 2 * (ph % 1) - 1


def noise(sec, color="white"):
    x = _rng.standard_normal(int(sec * SR))
    if color == "pink":
        x = lfilter([0.049922, -0.095993, 0.050612, -0.004408], [1, -2.494956, 2.017265, -0.522189], x)
    if color == "brown":
        x = np.cumsum(x)
        x -= np.linspace(x[0], x[-1], len(x))
    return x / (np.abs(x).max() + 1e-9)


def pluck(freq, sec=1.0, bright=0.5, decay=0.996):
    period = max(2, int(round(SR / freq)))
    n = int(sec * SR)
    burst = filt(_rng.uniform(-1, 1, period), "lowpass", 1500 + 7000 * bright)
    x = np.zeros(n)
    x[:period] = burst
    a = np.zeros(period + 2)
    a[0], a[period], a[period + 1] = 1, -decay * 0.5, -decay * 0.5
    return lfilter([1.0], a, x) * np.clip((sec - t_axis(sec)) / 0.03, 0, 1)


def mallet(freq, sec=1.0, ratios=(1, 3.93), decays=(7, 26), gains=(1, 0.3)):
    t = t_axis(sec)
    x = sum(g * np.sin(2 * np.pi * freq * r * t) * np.exp(-t * d) for r, d, g in zip(ratios, decays, gains))
    return x * np.minimum(1, t / 0.002)


def bell(freq, sec=2.0):
    return mallet(freq, sec, ratios=(1, 2.76, 5.4, 8.93), decays=(2.5, 5, 9, 14), gains=(1, 0.4, 0.2, 0.1))


def pad(freqs, sec, voices=5, detune=12.0, cutoff=2500, attack=0.3, release=0.4, shape="saw"):
    t = t_axis(sec)
    out = np.zeros((len(t), 2))
    for f in freqs:
        for i, c in enumerate(np.linspace(-detune, detune, voices)):
            p = (i / max(1, voices - 1)) * 1.6 - 0.8
            v = osc(f, sec, shape, c)
            out[:, 0] += v * np.sqrt(0.5 * (1 - p))
            out[:, 1] += v * np.sqrt(0.5 * (1 + p))
    out = filt(out / (voices * len(freqs)), "lowpass", cutoff)
    env = np.minimum(1, t / attack) * np.clip((sec - t) / release, 0, 1)
    return out * env[:, None]


def kick(punch=1.0, low=48, high=150, length=0.4):
    t = t_axis(length)
    f = low + (high - low) * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7 / length * 0.35)
    click = filt(_rng.standard_normal(len(t)), "bandpass", [1500, 5000]) * np.exp(-t * 400) * 0.25 * punch
    return np.tanh((body + click) * 1.2)


def snare(tone=190, length=0.25):
    t = t_axis(length)
    body = np.sin(2 * np.pi * tone * t) * np.exp(-t * 30)
    rattle = filt(_rng.standard_normal(len(t)), "bandpass", [1800, 9000]) * np.exp(-t * 22)
    return body * 0.4 + rattle * 0.6


def clap(length=0.3):
    t = t_axis(length)
    n = filt(_rng.standard_normal(len(t)), "bandpass", [900, 3500])
    env = sum(np.where(t >= d, np.exp(-(t - d) * 90), 0) for d in (0.0, 0.011, 0.022))
    env = env + np.where(t >= 0.03, np.exp(-(t - 0.03) * 18) * 0.5, 0)
    return n * env * 0.6


def hat(length=0.06, open_=False):
    t = t_axis(0.35 if open_ else length)
    return filt(_rng.standard_normal(len(t)), "highpass", 7000) * np.exp(-t * (8 if open_ else 60))


def hit(material="wood", length=0.3):
    bands = {"wood": [300, 1800], "glass": [2500, 9000], "metal": [800, 6000], "paper": [1500, 7000], "rubber": [120, 600]}
    t = t_axis(length)
    x = filt(_rng.standard_normal(len(t)), "bandpass", bands[material])
    decay = {"wood": 40, "glass": 12, "metal": 6, "paper": 55, "rubber": 30}[material]
    return x * np.exp(-t * decay)


def riser(sec, f0=200, f1=2000):
    t = t_axis(sec)
    x = filt(noise(sec, "white"), "bandpass", [f0, f1]) * (t / sec) ** 2
    return x + sweep(f0, f1, sec) * 0.2 * (t / sec) ** 2


def reverb(x, seconds=1.2, wet=0.25, tone=5000):
    ir_t = t_axis(seconds)
    ir = _rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t * 6 / seconds)[:, None]
    ir = filt(ir, "lowpass", tone)
    x2 = x if x.ndim == 2 else np.stack([x, x], 1)
    tail = np.stack([fftconvolve(x2[:, c], ir[:, c])[: len(x2)] for c in range(2)], 1)
    tail /= np.abs(tail).max() + 1e-9
    return x2 * (1 - wet) + tail * wet * np.abs(x2).max()


class Mix:
    def __init__(self, seconds=LENGTH):
        self.n = int(round(seconds * SR))
        self.buses = {}

    def bus(self, name):
        if name not in self.buses:
            self.buses[name] = np.zeros((self.n, 2))
        return self.buses[name]

    def add(self, sig, sec, bus="main", pan=0.0, gain=1.0):
        buf = self.bus(bus)
        start = int(round(sec * SR))
        if start >= self.n or start < 0:
            return
        s = sig[: self.n - start] * gain
        if s.ndim == 1:
            buf[start:start + len(s), 0] += s * np.sqrt(0.5 * (1 - pan))
            buf[start:start + len(s), 1] += s * np.sqrt(0.5 * (1 + pan))
        else:
            buf[start:start + len(s)] += s

    def duck(self, bus, by, depth=0.5, release=0.18):
        key = np.abs(self.bus(by)).max(1)
        env = np.zeros(self.n)
        level, fall = 0.0, np.exp(-1 / (release * SR))
        for i in range(0, self.n, 64):
            level = max(key[i:i + 64].max(initial=0), level * fall ** 64)
            env[i:i + 64] = level
        env = env / (env.max() + 1e-9)
        self.bus(bus)[:] *= (1 - depth * env)[:, None]

    def silence(self, start_sec, end_sec, fade=0.004):
        a, b = int(start_sec * SR), int(end_sec * SR)
        f = int(fade * SR)
        for buf in self.buses.values():
            buf[max(0, a - f):a] *= np.linspace(1, 0, min(f, a))[:, None]
            buf[a:b] = 0

    def write(self, path, true_peak_db=-2.0):
        total = sum(self.buses.values()) if self.buses else np.zeros((self.n, 2))
        total = np.tanh(total * 1.1) / np.tanh(1.1)
        true_peak = np.abs(resample_poly(total, 4, 1, axis=0)).max()
        total *= 10 ** (true_peak_db / 20) / (true_peak + 1e-9)
        tail = int(0.02 * SR)
        total[-tail:] *= np.linspace(1, 0, tail)[:, None]
        pcm = (np.clip(total, -1, 1) * 32767).astype(np.int16)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with wave.open(path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        return path
