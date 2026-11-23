#!/usr/bin/env python3
"""Varredura EXAUSTIVA de referências a um endereço (paddr) numa imagem ARM ELF.

Existe porque `refs.py` é rápido mas cobre só Thumb `bl/blx` e o slot PLT ARM:
ele NÃO vê tail-calls (`b`/`b.w`), branches ARM, nem ponteiros de função em
tabelas/vtables — e é justamente um ponteiro de dados sem instrução que sustenta
o §37a. `find_str_refs.py` vê ponteiros e `adr`/`ldr`/`movw`, mas não branches.

Esta ferramenta cobre, numa passada só, para N alvos simultâneos:

  1. palavra LE32 em QUALQUER offset par de QUALQUER segmento LOAD
     (pega ponteiros em tabelas, vtables, structs, e a forma com bit0 Thumb);
  2. branches Thumb `bl`, `blx`, `b`, `b.w` para o alvo (inclui tail-call);
  3. branches ARM `b`, `bl`, `blx` para o alvo.

Limite honesto: dispatch indireto (`blx rN`, chamada por vtable/ponteiro) só
aparece se o ponteiro estiver estático na imagem. Registro de callback em
runtime não é detectável aqui — por isso "zero hits" prova ausência de
referência ESTÁTICA, não ausência de execução.

Uso:
    python3 tools/audit_refs.py firmware/1.1.2_APPS.bin 0x107639da 0x108d2c02
    python3 tools/audit_refs.py firmware/1.1.2_APPS.bin 0x10ad5cf0 --pointer-only

Custo: ~2 min por imagem (desmonta cada offset de 2 bytes nos segmentos de
código). Vale rodar todos os alvos de uma vez.
"""
import argparse
import re
import struct
import subprocess
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM


def load_segments(path):
    """[(file_off, file_end, paddr, flags)] a partir do readelf -l (paddr!)."""
    out = subprocess.run(["readelf", "-W", "-l", path],
                         capture_output=True, text=True).stdout
    pat = re.compile(r"\s*LOAD\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)"
                     r"\s+(0x[0-9a-f]+)\s+(0x[0-9a-f]+)\s+([RWE ]{3,5})")
    segs = []
    for line in out.splitlines():
        m = pat.match(line)
        if not m:
            continue
        off = int(m.group(1), 16)     # deslocamento no arquivo
        pa = int(m.group(3), 16)      # paddr (o que o Ghidra carrega)
        fsz = int(m.group(4), 16)     # FileSiz
        flags = m.group(6).replace(" ", "")
        if fsz:
            segs.append((off, off + fsz, pa, flags))
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("img")
    ap.add_argument("targets", nargs="+", help="endereços em hex (paddr)")
    ap.add_argument("--pointer-only", action="store_true")
    ap.add_argument("--branch-only", action="store_true")
    ap.add_argument("--max-print", type=int, default=20)
    a = ap.parse_args()

    data = open(a.img, "rb").read()
    segs = load_segments(a.img)
    targets = {int(t, 16) for t in a.targets}
    # Um alvo pode aparecer como ponteiro "puro", com bit0 (Thumb) ou como
    # endereço par de uma função cujo ponteiro Thumb tem bit0 — por isso as
    # três formas. Branch sempre cai no endereço par.
    want = {}
    for t in targets:
        for v in (t, t & ~1, t | 1):
            want.setdefault(v, set()).add(t)
    hits = {t: [] for t in targets}

    def foff(addr):
        for off, end, pa, _fl in segs:
            if pa <= addr < pa + (end - off):
                return off + (addr - pa)
        return None

    # 1) palavra LE32 (ponteiro), em qualquer offset par, em qualquer segmento
    if not a.branch_only:
        for off, end, pa, fl in segs:
            for addr in range(pa, pa + (end - off), 2):
                o = foff(addr)
                if o is None or o + 4 > len(data):
                    continue
                w = struct.unpack_from("<I", data, o)[0]
                for t in want.get(w, ()):
                    # Layout do thunk ARM: [literal][ldr pc,[pc,#-4]] — o stub
                    # em addr-4 carrega este literal. Marcar para nao confundir
                    # ponteiro de tabela com importacao.
                    kind = "ptr"
                    pk = foff(addr - 4)
                    if pk is not None and pk + 4 <= len(data) and \
                            struct.unpack_from("<I", data, pk)[0] == 0xE51FF004:
                        kind = "plt-lit"
                    hits[t].append((kind, addr, w, fl))

    # 2/3) branches
    if not a.pointer_only:
        thumb = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        thumb.skipdata = True
        arm = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        arm.skipdata = True
        for off, end, pa, fl in segs:
            if "E" not in fl:
                continue
            for addr in range(pa & ~1, pa + (end - off), 2):
                o = foff(addr)
                if o is None:
                    continue
                for ins in thumb.disasm(data[o:o + 4], addr):
                    if ins.address != addr:
                        break
                    if ins.mnemonic in ("bl", "blx", "b", "b.w") \
                            and ins.op_str.startswith("#0x"):
                        try:
                            v = int(ins.op_str[1:], 16)
                        except ValueError:
                            break
                        for t in want.get(v, ()):
                            hits[t].append(("thumb", addr, v, fl))
                    break
            for addr in range(pa & ~3, pa + (end - off), 4):
                o = foff(addr)
                if o is None:
                    continue
                for ins in arm.disasm(data[o:o + 4], addr):
                    if ins.address != addr:
                        break
                    if ins.mnemonic in ("b", "bl", "blx") \
                            and ins.op_str.startswith("#0x"):
                        try:
                            v = int(ins.op_str[1:], 16)
                        except ValueError:
                            break
                        for t in want.get(v, ()):
                            hits[t].append(("arm", addr, v, fl))
                    break

    rc = 0
    for t in sorted(targets):
        h = sorted(set(hits[t]), key=lambda x: (x[0], x[1]))
        print(f"=== {t:#010x}: {len(h)} hit(s) ===")
        for kind, addr, val, fl in h[:a.max_print]:
            print(f"  {kind:5s} @{addr:#x} -> {val:#x}  [{fl}]")
        if len(h) > a.max_print:
            print(f"  ... +{len(h) - a.max_print}")
        if not h:
            rc = 1
    return 0 if not rc else 0   # sempre 0: ausência é resultado, não erro


if __name__ == "__main__":
    sys.exit(main())
