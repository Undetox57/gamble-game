"""Tiny generated sound effects (D5).

No audio files ship with the game: every sound is synthesised the first time it is needed and
cached as a .wav in a temp folder, then handed to the operating system's own player. Everything
is wrapped in try/except, so a machine without a sound card - or without winsound - simply gets
silence instead of a crash.
"""
import math
import os
import struct
import tempfile
import wave

RATE = 22050                     # samples per second; 16-bit mono is plenty for a blip
_enabled = True
_music = False                   # D19: background music, off until the player asks for it
_cache = {}


def set_enabled(on):
    """Master switch for the 'Sound effects' setting."""
    global _enabled
    _enabled = bool(on)


def enabled():
    return _enabled


def set_music(on):
    """D19: background music - a synthesised loop, one toggle like the effects. Switching the
    same value twice does nothing, so re-applying settings never restarts the loop."""
    global _music
    on = bool(on)
    if on == _music:
        return
    _music = on
    try:
        import winsound                                   # Windows only
        if on:
            path = _wav('music')
            if path:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC |
                                   winsound.SND_LOOP | winsound.SND_NODEFAULT)
        else:
            winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass


def music_on():
    return _music


def _sweep(f0, f1, dur, vol=0.35, decay=1.4):
    """One tone gliding from f0 to f1 Hz with a quick attack and a smooth fade."""
    n = max(1, int(RATE * dur))
    samples = []
    phase = 0.0
    for i in range(n):
        p = i / n
        f = f0 + (f1 - f0) * p
        phase += 2 * math.pi * f / RATE
        attack = min(1.0, i / max(1.0, RATE * 0.006))
        env = attack * ((1.0 - p) ** decay)
        samples.append(math.sin(phase) * env * vol)
    return samples


def _mix(*parts):
    """Lay sounds on top of each other (start to start)."""
    total = max(len(p) for p in parts)
    out = [0.0] * total
    for part in parts:
        for i, v in enumerate(part):
            out[i] += v
    return out


def _seq(*parts, gap=0.03):
    """Play sounds one after another."""
    out = []
    for part in parts:
        out.extend(part)
        out.extend([0.0] * int(RATE * gap))
    return out


def _build(name):
    """The recipes. Each returns a list of samples in [-1, 1]."""
    if name == 'win':                      # a small rising flourish
        return _seq(_sweep(523, 660, 0.10), _sweep(660, 784, 0.10), _sweep(784, 1046, 0.22))
    if name == 'lose':                     # one descending, slightly buzzy thud
        return _sweep(330, 150, 0.34, vol=0.30, decay=1.8)
    if name == 'click':                    # the soft tick of a chip landing
        return _sweep(1400, 900, 0.05, vol=0.22, decay=2.5)
    if name == 'jackpot':                  # the one everybody listens for
        notes = [(523, 0.09), (659, 0.09), (784, 0.09), (1046, 0.12), (1318, 0.30)]
        return _seq(*[_sweep(f, f * 1.01, d, vol=0.34) for f, d in notes], gap=0.02)
    if name == 'streak':                   # ticking up, for the streak side bet
        return _seq(*[_sweep(700 + 90 * i, 780 + 90 * i, 0.06, vol=0.26) for i in range(4)], gap=0.02)
    if name == 'ach':                      # a bright little sparkle for an unlocked achievement
        return _seq(_sweep(1046, 1046, 0.05, vol=0.26), _sweep(1318, 1318, 0.05, vol=0.28),
                    _sweep(1568, 2093, 0.24, vol=0.30), gap=0.03)
    if name == 'coin':                     # coins landing: two bright metallic ticks
        return _seq(_sweep(1864, 1864, 0.05, vol=0.24), _sweep(2489, 2349, 0.14, vol=0.26), gap=0.05)
    if name == 'start':                    # a warm C-major swell for the start screen
        return _mix(_sweep(262, 262, 0.55, vol=0.14, decay=1.1),
                    _sweep(392, 392, 0.55, vol=0.13, decay=1.1),
                    _sweep(523, 523, 0.55, vol=0.13, decay=1.1))
    if name == 'music':                    # D19: a slow I-vi-IV-V pad with a soft arpeggio -
        beat = 0.75                        # two rounds make a 24 s loop that fades to silence
        chords = [(261.63, 329.63, 392.00),   # C                  at both ends, so it repeats
                   (220.00, 261.63, 329.63),   # Am                 without an audible seam
                   (174.61, 220.00, 261.63),   # F
                   (196.00, 246.94, 293.66)]   # G
        out = []
        for _round in range(2):
            for a, b, c in chords:
                dur = beat * 4
                pad = _mix(_sweep(a, a, dur, vol=0.095, decay=0.85),
                           _sweep(b, b, dur, vol=0.075, decay=0.85),
                           _sweep(c, c, dur, vol=0.075, decay=0.85))
                arp = []
                for f in (a, b, c, b, a, c, b, a):
                    arp.extend(_sweep(f * 2, f * 2, dur / 8 * 0.9, vol=0.05, decay=1.6))
                out.extend(_mix(pad, arp))
        breath = int(RATE * 0.75)                  # a slow breath at the seam: the loop wraps
        for i in range(breath):                    # from silence into the first downbeat, so
            k = i / breath                         # restarting it never clicks
            out[i] *= k
            out[-1 - i] *= k
        return out
    return []


def _path(name):
    folder = os.path.join(tempfile.gettempdir(), 'gamble_sounds')
    return os.path.join(folder, f'{name}_{RATE}.wav')


def _wav(name):
    """Synthesise (once) and return the file's path."""
    if name in _cache and os.path.exists(_cache[name]):
        return _cache[name]
    path = _path(name)
    if not os.path.exists(path):
        samples = _build(name)
        if not samples:
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with wave.open(path, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            frames = b''.join(struct.pack('<h', max(-32767, min(32767, int(v * 32767))))
                              for v in samples)
            w.writeframes(frames)
    _cache[name] = path
    return path


def play(name):
    """Play one effect by name. Never raises, never blocks: silence is a perfectly good answer."""
    if not _enabled or name in (None, ''):
        return
    try:
        path = _wav(name)
        if not path:
            return
        import winsound                                   # Windows only
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception:
        pass
