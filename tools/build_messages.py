"""Build locale/<lang>/LC_MESSAGES/django.{po,mo} from a translation map.

No GNU gettext required — the .mo is written with a small pure-Python compiler,
so it works on Windows / cPanel alike. Run after updating locale_content.json:

    python tools/build_messages.py

Inputs:
- locale_content.json  : {"<ru>": {"uz": "...", "en": "..."}, ...}  (UI + content)
Outputs:
- locale/uz/LC_MESSAGES/django.po + .mo
- locale/en/LC_MESSAGES/django.po + .mo
"""

import json
import os
import re
import struct
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LANGS = ("uz", "en")

# msgids that templates use via {% blocktranslate %} (not caught by the simple
# {% trans %} scan) — provide them explicitly with their placeholders.
MANUAL = {
    "По запросу «%(query)s»": {
        "uz": "«%(query)s» so‘rovi bo‘yicha",
        "en": "For “%(query)s”",
    },
}


def extract_ui_msgids():
    """All {% trans %}/{% translate %} and _()/gettext() msgids in the project."""
    ids = set()
    re_t = re.compile(r"{%\s*(?:trans|translate)\s+(\"([^\"]*)\"|'([^']*)')")
    re_py = re.compile(r"(?:gettext_lazy|gettext|_)\(\s*(\"([^\"]*)\"|'([^']*)')\s*\)")
    for f in BASE.glob("templates/**/*.html"):
        s = f.read_text(encoding="utf-8")
        for m in re_t.finditer(s):
            ids.add(m.group(2) if m.group(2) is not None else m.group(3))
    for f in BASE.glob("*/**/*.py"):
        if "venv" in f.parts or "migrations" in f.parts or "tools" in f.parts:
            continue
        s = f.read_text(encoding="utf-8")
        for m in re_py.finditer(s):
            ids.add(m.group(2) if m.group(2) is not None else m.group(3))
    return {x for x in ids if x.strip()}


def po_escape(s):
    return (s.replace("\\", "\\\\").replace("\"", "\\\"")
             .replace("\n", "\\n").replace("\t", "\\t"))


def write_po(path, lang, entries):
    """entries: list of (msgid, msgstr)."""
    lines = [
        'msgid ""', 'msgstr ""',
        '"Project-Id-Version: akproftom\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8bit\\n"',
        f'"Language: {lang}\\n"',
        "",
    ]
    for msgid, msgstr in entries:
        lines.append(f'msgid "{po_escape(msgid)}"')
        lines.append(f'msgstr "{po_escape(msgstr)}"')
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_mo(path, catalog):
    """Write a GNU .mo file. catalog: dict {msgid: msgstr}, includes "" header."""
    keys = sorted(catalog.keys())
    offsets, ids, strs = [], b"", b""
    for k in keys:
        v = catalog[k]
        kb, vb = k.encode("utf-8"), v.encode("utf-8")
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b"\x00"
        strs += vb + b"\x00"
    n = len(keys)
    keystart = 7 * 4 + 16 * n
    valuestart = keystart + len(ids)
    koffsets, voffsets = [], []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    output = struct.pack(
        "Iiiiiii",
        0x950412DE, 0, n, 7 * 4, 7 * 4 + n * 8, 0, 0,
    )
    output += struct.pack("i" * len(koffsets), *koffsets)
    output += struct.pack("i" * len(voffsets), *voffsets)
    output += ids + strs
    path.write_bytes(output)


def main():
    tr = json.loads((BASE / "locale_content.json").read_text(encoding="utf-8"))
    tr = {**tr, **MANUAL}  # manual entries win
    ui = extract_ui_msgids() | set(MANUAL.keys())

    for lang in LANGS:
        entries, missing = [], []
        for msgid in sorted(ui):
            t = tr.get(msgid, {}).get(lang)
            if t:
                entries.append((msgid, t))
            else:
                missing.append(msgid)
        # PO for humans
        ldir = BASE / "locale" / lang / "LC_MESSAGES"
        ldir.mkdir(parents=True, exist_ok=True)
        write_po(ldir / "django.po", lang, entries)
        # MO for runtime (include empty-string header entry)
        catalog = {"": (
            "Content-Type: text/plain; charset=UTF-8\n"
            f"Language: {lang}\n"
        )}
        for msgid, msgstr in entries:
            catalog[msgid] = msgstr
        write_mo(ldir / "django.mo", catalog)
        print(f"[{lang}] {len(entries)} translated, {len(missing)} missing")
        if missing:
            for m in missing[:20]:
                print(f"    MISSING: {m[:70]}")


if __name__ == "__main__":
    main()
