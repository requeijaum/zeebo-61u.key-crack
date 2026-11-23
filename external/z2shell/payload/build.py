#!/usr/bin/env python3
"""Build de um applet BREW 4.0.2 para Zeebo (payload.c -> payload.mod).

Reescrita portátil do `poc/payload/build.py` do Z2Shell (ver ../PROVENANCE.md):
mesmas flags oficiais do SDK/toolset, sem caminhos de Windows fixos.

Variáveis de ambiente (todas obrigatórias menos OUT):
  BREW_SDK      raiz do SDK, ex.: .../brew-sdk/platform_402/BREW 4.0.2 SP19
  ARM_BIN       pasta com arm-none-eabi-gcc/g++ (xpack ou ARM oficial)
  ELF2MOD_BIN   pasta do Toolset com elf2mod.exe (e elf2mod/src/gnu/elf2mod.x)
  OUT           pasta de saída (default: .)

Uso:
  python3 external/z2shell/payload/build.py [payload.c]

O .mod resultante é um applet BREW real (magic "BREW" em +0x08). Ele NÃO é
assinado: no console só roda com o carregador destravado (JTAG por boot) ou
depois de obtida execução de código — ver docs/z2shell_crosscheck.md.
"""
import os
import shutil
import subprocess
import sys


def need(env):
    v = os.environ.get(env)
    if not v:
        raise SystemExit("defina %s (ver docstring)" % env)
    if not os.path.isdir(v):
        raise SystemExit("%s nao e um diretorio: %s" % (env, v))
    return v


def exe(path):
    """Workaround para toolchains Windows: aceita tanto 'gcc' como 'gcc.exe'."""
    if os.path.isfile(path):
        return path
    if os.path.isfile(path + ".exe"):
        return path + ".exe"
    raise SystemExit("nao encontrado: %s" % path)


def run(cmd, **kw):
    print("$", " ".join(os.path.basename(c) for c in cmd[:1]) + " ...")
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        raise SystemExit("falhou (%d): %s" % (r.returncode, cmd[0]))
    return r


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "payload.c")
    sdk = need("BREW_SDK")
    arm = need("ARM_BIN")
    ts = need("ELF2MOD_BIN")
    out = os.environ.get("OUT", ".")
    os.makedirs(out, exist_ok=True)

    gcc = exe(os.path.join(arm, "arm-none-eabi-gcc"))
    gxx = exe(os.path.join(arm, "arm-none-eabi-g++"))
    elf2mod = exe(os.path.join(ts, "elf2mod"))
    script = os.path.join(ts, "elf2mod", "src", "gnu", "elf2mod.x")
    if not os.path.isfile(script):
        raise SystemExit("linker script do elf2mod nao encontrado: %s" % script)

    # Flags oficiais (make.d/defines_armgcc.min do Toolset 7.10).
    cflags = ["-marm", "-march=armv6", "-fshort-wchar", "-mword-relocations",
              "-ffunction-sections", "-O1",
              "-I" + os.path.join(sdk, "inc"),
              "-I" + os.path.join(sdk, "sdk", "inc")]
    srcs = [src,
            os.path.join(sdk, "sdk", "src", "AEEModGen.c"),
            os.path.join(sdk, "sdk", "src", "AEEAppGen.c")]
    for s in srcs:
        run([gcc] + cflags + ["-c", s, "-o", os.path.join(out, os.path.basename(s)[:-2] + ".o")])

    ldflags = ["-marm", "-march=armv6", "-fshort-wchar", "-mword-relocations",
               "-nostdlib", "-nodefaultlibs", "-nostartfiles",
               "-Wl,--pic-executable", "-Wl,--entry=AEEMod_Load",
               "-Wl,--emit-relocs", "-Wl,--no-wchar-size-warning",
               "-Wl,--default-script=" + script,
               "-o", os.path.join(out, "payload.elf"),
               os.path.join(out, "payload.o"),
               os.path.join(out, "AEEModGen.o"),
               os.path.join(out, "AEEAppGen.o")]
    run([gxx] + ldflags)

    run([elf2mod, "-o", os.path.join(out, "payload.mod"),
         os.path.join(out, "payload.elf")])

    mod = os.path.join(out, "payload.mod")
    size = os.path.getsize(mod)
    head = open(mod, "rb").read(16)
    print("payload.mod: %d bytes, head %s" % (size, head.hex()))
    if head[8:12] != b"BREW":
        raise SystemExit("cabecalho inesperado (sem magic BREW em +0x08)")
    print("ok — applet BREW valido. Instalar exige MIF+assinatura ou loadExec "
          "destravado; ver docs/z2shell_crosscheck.md")


if __name__ == "__main__":
    main()
