#!/usr/bin/env python3
"""
PPT Master - User-level font installer

Installs TTF/OTF files (or the families bundled under assets/fonts/) for the
current user without administrator rights, so SVG decks render and export with
the family the standard names (Pretendard, IBM Plex Sans KR, NanumSquareNeo, ...).
PPTX never embeds fonts: every machine that opens a deck needs the family too.

Usage:
    python3 scripts/install_fonts.py                       # install every bundled family
    python3 scripts/install_fonts.py --family IBMPlexSansKR
    python3 scripts/install_fonts.py --dir <folder-or-zip> [--dir ...]
    python3 scripts/install_fonts.py --list                 # show families the standard knows

Windows: copies into %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts and registers
HKCU\\Software\\Microsoft\\Windows NT\\CurrentVersion\\Fonts. macOS: ~/Library/Fonts.
Linux: ~/.local/share/fonts (+ fc-cache when available).

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from console_encoding import configure_utf8_stdio  # noqa: E402

ASSETS = _SCRIPTS_DIR.parent / "assets" / "fonts"
FONT_SUFFIXES = {".ttf", ".otf"}


def font_full_name(path: Path) -> str:
    """Read nameID 4 (full name) from the OpenType name table; fall back to the stem."""
    try:
        data = path.read_bytes()
        tag = data[:4]
        if tag == b"ttcf":
            return path.stem
        num_tables = struct.unpack(">H", data[4:6])[0]
        for i in range(num_tables):
            off = 12 + i * 16
            name, _, toff, tlen = struct.unpack(">4sIII", data[off:off + 16])
            if name == b"name":
                table = data[toff:toff + tlen]
                count, str_off = struct.unpack(">HH", table[2:6])
                best = {}
                for j in range(count):
                    rec = table[6 + j * 12:18 + j * 12]
                    pid, eid, lid, nid, length, noff = struct.unpack(">HHHHHH", rec)
                    if nid != 4:
                        continue
                    raw = table[str_off + noff:str_off + noff + length]
                    if pid == 3 and eid in (1, 10):
                        txt = raw.decode("utf-16-be", "ignore")
                    elif pid == 1:
                        txt = raw.decode("mac-roman", "ignore")
                    else:
                        continue
                    best[(pid, lid)] = txt.strip()
                for key in ((3, 0x409), (3, 0x412), (1, 0)):
                    if key in best:
                        return best[key]
                if best:
                    return next(iter(best.values()))
        return path.stem
    except Exception:  # noqa: BLE001
        return path.stem


def collect(source: Path, tmp: Path) -> list[Path]:
    if source.is_file() and source.suffix.lower() == ".zip":
        out = tmp / source.stem
        out.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source) as z:
            for m in z.infolist():
                if m.is_dir() or "__MACOSX" in m.filename or Path(m.filename).suffix.lower() not in FONT_SUFFIXES:
                    continue
                target = out / Path(m.filename).name
                target.write_bytes(z.read(m))
        source = out
    if source.is_file():
        return [source] if source.suffix.lower() in FONT_SUFFIXES else []
    return sorted(p for p in source.rglob("*") if p.suffix.lower() in FONT_SUFFIXES and "__MACOSX" not in p.parts)


def install_windows(files: list[Path]) -> list[str]:
    import winreg  # noqa: PLC0415

    dest = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
    dest.mkdir(parents=True, exist_ok=True)
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts", 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
    done = []
    for f in files:
        target = dest / f.name
        if not target.exists() or target.stat().st_size != f.stat().st_size:
            shutil.copy2(f, target)
        label = f"{font_full_name(f)} ({'OpenType' if f.suffix.lower() == '.otf' else 'TrueType'})"
        winreg.SetValueEx(key, label, 0, winreg.REG_SZ, str(target))
        done.append(label)
    winreg.CloseKey(key)
    try:  # tell running apps the font table changed (best effort)
        import ctypes  # noqa: PLC0415
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)
    except Exception:  # noqa: BLE001
        pass
    return done


def install_posix(files: list[Path]) -> list[str]:
    dest = Path.home() / ("Library/Fonts" if platform.system() == "Darwin" else ".local/share/fonts")
    dest.mkdir(parents=True, exist_ok=True)
    done = []
    for f in files:
        shutil.copy2(f, dest / f.name)
        done.append(font_full_name(f))
    if platform.system() != "Darwin" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], check=False)
    return done


def main(argv=None) -> int:
    configure_utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", action="append", help="bundled family folder name under assets/fonts (repeatable)")
    ap.add_argument("--dir", action="append", type=Path, help="folder or zip with TTF/OTF files (repeatable)")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    bundled = sorted(p for p in ASSETS.iterdir() if p.is_dir()) if ASSETS.exists() else []
    if args.list:
        for p in bundled:
            print(f"{p.name}: {', '.join(f.name for f in sorted(p.glob('*.[ot]tf')))}")
        return 0
    sources: list[Path] = []
    if args.family:
        for name in args.family:
            p = ASSETS / name
            if not p.exists():
                print(f"[install_fonts] unknown bundled family: {name} (have: {', '.join(x.name for x in bundled)})")
                return 1
            sources.append(p)
    if args.dir:
        sources.extend(args.dir)
    if not sources:
        sources = bundled
    with tempfile.TemporaryDirectory() as tmp:
        files: list[Path] = []
        for s in sources:
            files.extend(collect(Path(s), Path(tmp)))
        if not files:
            print("[install_fonts] no TTF/OTF files found")
            return 1
        done = install_windows(files) if platform.system() == "Windows" else install_posix(files)
    for d in done:
        print(f"  + {d}")
    print(f"[install_fonts] installed {len(done)} font file(s) for the current user")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
