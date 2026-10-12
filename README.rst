Description
===========

Converts Variable Frame Rate (VFR) video to a Constant Frame Rate (CFR) video through the use of Matroska Version 2 Timecodes.

Ported from the Avisynth plugin written by Nicholai Main.

This fork targets the VapourSynth API 4 (R55 and newer, required since R80). The namespace, the function
and its arguments are unchanged.


Usage
=====
::

    vfrtocfr.VFRToCFR(clip clip, string timecodes, int fpsnum, int fpsden[, bint drop = True])

Parameters:
    *clip*
        Input clip.

    *timecodes*
        Name of the Matroska V2 Timecodes file.

    *fpsnum*
        Target output framerate numerator. Must be greater than 0.
        
    *fpsden*
        Target output framerate denominator. Must be greater than 0.
        
    *drop*
        If set to True, allows frame drops to acquire target framerate.
        Otherwise, throws an error if frames are dropped.

Installation
============
Wheels for Windows x64, Linux x86_64 and macOS arm64 are attached to the GitHub releases::

    pip install vapoursynth_vfrtocfr-<version>-py3-none-<platform>.whl

The wheel puts the plugin into ``site-packages/vapoursynth/plugins``, where VapourSynth autoloads it.

Building from sources
=====================
You need `The Meson Build System <http://mesonbuild.com>`_ installed. Without system VapourSynth headers the
vendored API 4 headers in ``include/vapoursynth`` are used.
::

    $ meson setup build --buildtype release && ninja -C build

Tests::

    $ python3 test/test_vfrtocfr.py build/libvfrtocfr.so
