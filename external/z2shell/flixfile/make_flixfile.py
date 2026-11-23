#!/usr/bin/env python3
"""Extrai /lctsys/flixfile.dat do dump 1.1.2 e gera a variante FIRSTAPP:N.

Descoberta do Z2Shell (ver ../PROVENANCE.md): o applet que a Z-Wheel inicia no
boot é escolhido por este arquivo de texto:

    //0=DEFAULT,1=EM,2=CONFTEST,3=TECTOY
    FIRSTAPP:0

Ou seja: trocar `FIRSTAPP:0` por `FIRSTAPP:1` faz o console bootar no EMAPPLET
(menu de engenharia da Longcheer), que tem Field Test (Memory Copy do SD) e
AUXSETTINGS (SIO Port Map — ativa o DIAG sem chave, DEPOIS de já haver acesso).

Dois cuidados que o material original do Z2Shell não tem:

  1. O arquivo real tem 737 bytes e termina linhas com CRLF. A cópia distribuída
     no repo upstream está com LF (708 bytes), apesar do guia mandar "conferir
     737 bytes". Aqui o arquivo é extraído do SEU dump, byte a byte.
  2. O APN do seu console pode não ser o do dump (o dump é BR/Claro). Por isso
     este script NUNCA embute conteúdo próprio: ele copia o seu arquivo e altera
     só o valor de FIRSTAPP.

Uso:
  python3 external/z2shell/flixfile/make_flixfile.py                 # mostra o valor
  python3 external/z2shell/flixfile/make_flixfile.py --firstapp 1 -o flixfile_em.dat
  python3 external/z2shell/flixfile/make_flixfile.py --dump /caminho/1.1.2.bin

Escrever no console exige DIAG (ou EM já ativo): o arquivo vive em
fs:/lctsys/flixfile.dat.
"""
import argparse
import hashlib
import os
import sys

MARK = b"//this is a test file"
KEY = b"FIRSTAPP:"
NAMES = {0: "DEFAULT (Z-Wheel)", 1: "EM (EMAPPLET)", 2: "CONFTEST", 3: "TECTOY"}


def find_file(data):
    i = data.find(MARK)
    if i < 0:
        raise SystemExit("marcador do flixfile.dat nao encontrado no dump")
    j = data.find(b"\x00", i)
    if j < 0:
        raise SystemExit("NUL terminador nao encontrado")
    return i, data[i:j]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default=os.path.expanduser(
        "~/projects/zeebo-lle/nand/1.1.2.bin"),
        help="dump completo 1.1.2 (default: %(default)s)")
    ap.add_argument("--firstapp", type=int, choices=[0, 1, 2, 3],
                    help="valor a gravar em FIRSTAPP (omitido = so mostra)")
    ap.add_argument("-o", "--out", help="arquivo de saida")
    a = ap.parse_args()

    if not os.path.isfile(a.dump):
        raise SystemExit("dump nao encontrado: %s" % a.dump)
    data = open(a.dump, "rb").read()
    off, real = find_file(data)
    print("dump:        %s" % a.dump)
    print("offset:      0x%X" % off)
    print("tamanho:     %d bytes%s" % (len(real),
          "" if len(real) == 737 else "  (ATENCAO: esperado 737)"))
    print("sha256:      %s" % hashlib.sha256(real).hexdigest())
    print("CRLF:        %s" % ("sim" if b"\r\n" in real else "NAO"))

    k = real.find(KEY)
    if k < 0:
        raise SystemExit("FIRSTAPP nao encontrado no arquivo")
    cur = real[k + len(KEY):k + len(KEY) + 1]
    print("FIRSTAPP:    %s" % cur.decode("latin1"))

    if a.firstapp is None:
        for v, n in NAMES.items():
            print("  %d = %s" % (v, n))
        return 0

    if len(cur) != 1 or not cur.isdigit():
        raise SystemExit("valor de FIRSTAPP inesperado: %r" % cur)
    out = real[:k + len(KEY)] + str(a.firstapp).encode() + real[k + len(KEY) + 1:]
    assert len(out) == len(real), "o arquivo mudou de tamanho"
    print("novo valor:  %d (%s), %d bytes" % (a.firstapp, NAMES[a.firstapp], len(out)))
    print("sha256 novo: %s" % hashlib.sha256(out).hexdigest())

    if not a.out:
        raise SystemExit("nada gravado (use -o ARQUIVO)")
    with open(a.out, "wb") as f:
        f.write(out)
    print("gravado:     %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
