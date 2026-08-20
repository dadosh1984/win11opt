"""Compile .po to .mo using stdlib only (minimal .mo writer)."""
from __future__ import annotations

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_po(text: str) -> list[tuple[str, str]]:
    """Parse .po: return [(msgid, msgstr), ...] (singular only, no plural, skip header)."""
    pairs = []
    in_header = True
    cur_id = ""
    cur_str = ""
    last_keyword = None
    for line in text.splitlines():
        line = line.rstrip("\r")
        if line.startswith("msgid_plural"):
            cur_id = ""
            cur_str = ""
            last_keyword = "skip"
            continue
        if line.startswith("msgid "):
            content = line[6:].strip().strip('"')
            if content == "":
                # Это header: пропускаем всё до пустой строки
                in_header = True
                cur_id = ""
                cur_str = ""
                last_keyword = "msgid"
                continue
            if in_header:
                in_header = False
            if last_keyword == "msgstr" and cur_id:
                pairs.append((cur_id, cur_str))
            cur_id = content
            cur_str = ""
            last_keyword = "msgid"
        elif line.startswith("msgstr "):
            cur_str = line[7:].strip().strip('"')
            last_keyword = "msgstr"
        elif line.startswith('"'):
            if in_header:
                continue  # skip header continuations
            cont = line.strip().strip('"')
            if last_keyword == "msgid":
                cur_id = cur_id + cont
            elif last_keyword == "msgstr":
                cur_str = cur_str + cont
        elif not line.strip():
            if not in_header and last_keyword == "msgstr" and cur_id:
                pairs.append((cur_id, cur_str))
            cur_id = ""
            cur_str = ""
            last_keyword = None
            in_header = False
    if not in_header and last_keyword == "msgstr" and cur_id:
        pairs.append((cur_id, cur_str))
    return pairs


def write_mo(pairs: list[tuple[str, str]], out: Path) -> None:
    """Write GNU MO file (version 1, no plural, no hash table)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    # Filter: keep only pairs with non-empty msgstr
    filtered = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in pairs if v]
    n = len(filtered)
    # Header: 7 x uint32 = 28 bytes
    # Standard MO layout:
    #   [header 28 bytes]
    #   [msgid offsets: n * 8 bytes]
    #   [msgstr offsets: n * 8 bytes]
    #   [msgid strings data]
    #   [msgstr strings data]
    off_msgid = 28           # msgid offsets table starts right after header
    off_msgstr = 28 + n * 8  # msgstr offsets table follows msgid offsets
    header = struct.pack(
        "<7I",
        0x950412DE,  # magic
        0,           # version
        n,           # nstrings
        off_msgid,
        off_msgstr,
        0,           # hash size (none)
        0,           # hash offset (none)
    )
    assert len(header) == 28
    # Build msgid offsets + data
    pos = off_msgstr + n * 8  # after msgstr offsets
    msgid_offsets = b""
    msgid_data = b""
    for k, v in filtered:
        msgid_offsets += struct.pack("<II", pos, len(k))
        msgid_data += k + b"\x00"
        pos += len(k) + 1
    msgstr_offsets = b""
    msgstr_data = b""
    for k, v in filtered:
        msgstr_offsets += struct.pack("<II", pos, len(v))
        msgstr_data += v + b"\x00"
        pos += len(v) + 1
    out.write_bytes(header + msgid_offsets + msgstr_offsets + msgid_data + msgstr_data)


def main():
    for lang in ("en", "ru"):
        po = ROOT / "locale" / lang / "LC_MESSAGES" / "win11opt.po"
        mo = ROOT / "locale" / lang / "LC_MESSAGES" / "win11opt.mo"
        if not po.exists():
            print(f"missing: {po}")
            continue
        pairs = parse_po(po.read_text(encoding="utf-8"))
        # Filter header (empty msgid)
        pairs = [(k, v) for k, v in pairs if k]
        write_mo(pairs, mo)
        print(f"compiled: {mo} ({len(pairs)} entries)")


if __name__ == "__main__":
    main()