#!/usr/bin/env python3
"""Functional tests for the VFRToCFR VapourSynth plugin.

Usage: python3 test/test_vfrtocfr.py [path/to/libvfrtocfr.so]

Without an argument the plugin is expected to be autoloaded (e.g. from the
installed wheel) or to be found in site-packages/vapoursynth/plugins.

Requires the vapoursynth Python module (R55 or newer).
"""
import glob
import os
import sys
import tempfile

import vapoursynth as vs

core = vs.core


def load_plugin(args):
    if args:
        core.std.LoadPlugin(args[0])
        return
    if hasattr(core, "vfrtocfr"):
        return
    # Wheel layout: site-packages/vapoursynth/plugins/<plugin>
    plugin_dir = os.path.join(os.path.dirname(vs.__file__), "plugins")
    for ext in ("*.so", "*.dll", "*.dylib"):
        for path in glob.glob(os.path.join(plugin_dir, "*vfrtocfr" + ext)):
            core.std.LoadPlugin(path)
            return
    raise SystemExit("FAIL: vfrtocfr plugin is neither autoloaded nor found in " + plugin_dir)


def tagged_clip(frames):
    """A clip whose frames carry their index as frame property."""
    base = core.std.BlankClip(width=64, height=32, length=frames, format=vs.GRAY8)

    def tag(n, f):
        f = f.copy()
        f.props["Idx"] = n
        return f

    return core.std.ModifyFrame(base, base, tag)


def indices(clip):
    return [clip.get_frame(n).props["Idx"] for n in range(clip.num_frames)]


def check(cond, msg):
    if not cond:
        raise SystemExit("FAIL: " + msg)
    print("ok  ", msg)


def expect_error(fn, msg):
    try:
        fn()
    except vs.Error as e:
        check(True, "%s (%s)" % (msg, str(e).strip().splitlines()[-1]))
    else:
        raise SystemExit("FAIL: no error raised: " + msg)


def timecodes(tmp, name, stamps):
    path = os.path.join(tmp, name)
    with open(path, "w") as handle:
        handle.write("# timecode format v2\n")
        for stamp in stamps:
            handle.write("%.6f\n" % stamp)
    return path


def main():
    load_plugin(sys.argv[1:])
    check(hasattr(core, "vfrtocfr"), "plugin loaded (namespace vfrtocfr)")

    with tempfile.TemporaryDirectory() as tmp:
        cfr25 = timecodes(tmp, "cfr25.txt", [n * 40.0 for n in range(20)])
        src = tagged_clip(20)

        out = core.vfrtocfr.VFRToCFR(src, timecodes=cfr25, fpsnum=25, fpsden=1)
        check(out.num_frames == 20 and indices(out) == list(range(20)), "CFR 25 -> 25 keeps every frame")
        check((out.fps.numerator, out.fps.denominator) == (25, 1), "output frame rate 25/1")
        props = out.get_frame(3).props
        check((props["_DurationNum"], props["_DurationDen"]) == (1, 25), "_DurationNum/_DurationDen set to 1/25")

        out = core.vfrtocfr.VFRToCFR(src, timecodes=cfr25, fpsnum=50, fpsden=1)
        check(indices(out) == [n // 2 for n in range(40)], "CFR 25 -> 50 doubles every frame")

        out = core.vfrtocfr.VFRToCFR(src, timecodes=cfr25, fpsnum=25, fpsden=2)
        check(indices(out) == list(range(0, 20, 2)), "CFR 25 -> 12.5 takes every second frame")
        expect_error(lambda: core.vfrtocfr.VFRToCFR(src, timecodes=cfr25, fpsnum=25, fpsden=2, drop=False),
                     "drop=False rejects dropped frames")

        # 10 frames at 24 fps, then 10 frames at 48 fps, converted to 24 fps.
        stamps = [n * 1000.0 / 24 for n in range(10)] + [10 * 1000.0 / 24 + n * 1000.0 / 48 for n in range(10)]
        vfr = timecodes(tmp, "vfr.txt", stamps)
        out = core.vfrtocfr.VFRToCFR(src, timecodes=vfr, fpsnum=24, fpsden=1)
        idx = indices(out)
        check(idx[:10] == list(range(10)), "VFR 24 part kept 1:1")
        # The last frame lasts the average duration, so it gets a CFR frame of its own.
        check(idx[10:] == [10, 12, 14, 16, 18, 19], "VFR 48 part halved, last frame kept")

        expect_error(lambda: core.vfrtocfr.VFRToCFR(src, timecodes=cfr25, fpsnum=0, fpsden=1), "fpsnum 0 rejected")
        expect_error(lambda: core.vfrtocfr.VFRToCFR(src, timecodes=os.path.join(tmp, "missing.txt"), fpsnum=25, fpsden=1),
                     "missing timecodes file rejected")
        single = timecodes(tmp, "single.txt", [0.0])
        expect_error(lambda: core.vfrtocfr.VFRToCFR(src, timecodes=single, fpsnum=25, fpsden=1),
                     "timecodes with one timestamp rejected")

    print("all tests passed")


if __name__ == "__main__":
    main()
