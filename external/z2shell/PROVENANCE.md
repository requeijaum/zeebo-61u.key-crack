# Material importado de Z2Shell (SterTheStar)

Origem: https://github.com/SterTheStar/Z2Shell
Commit importado: `fa210baac7cc9fd001b9e7879887f19b0e3a02a5` ("Initial import: Z2Shell — engenharia reversa da Z-Wheel (Zeebo)")
Data da importação: 2026-11-23

O repositório original está também como **submódulo git** em
`external/upstream/Z2Shell` (pin no mesmo `fa210ba`, branch `main`, clone raso).
Este diretório (`external/z2shell/`) é a cópia curada: só o material
reproduzível, com o caminho do `tectoy.mod` lido de `$TECTOY_MOD` e o gerador de
`flixfile` corrigido. Para outros clonarem o projeto:

```bash
git clone --recurse-submodules <repo>      # ou: git submodule update --init
```

O submódulo baixa ~440 MB de árvore (2.119 PNGs de evidência, o dump em `.7z` e
o `tectoy.mod`). Quem só quer o material curado pode ignorá-lo:
`git submodule update --init -- path/to/other` não é necessário para nada que
esteja referenciado nos docs daqui.

## Por que este diretório existe

O Z2Shell resolve a metade que faltava neste projeto: transformar um **arquivo de
dados não assinado** (`.qxm`/`.qxa` lidos pelo shell da Z-Wheel) em corrupção de
memória controlada, e depois em execução de código no contexto do shell (BREW 4,
ARM11). O 61u.key resolve a outra metade: o que é preciso para abrir o DIAG.

A auditoria do que se sustenta e do que não se sustenta está em
`../../docs/z2shell_crosscheck.md`. Este diretório guarda apenas o material
reproduzível — nada de firmware, nada de binário da TecToy.

## O que foi copiado

| arquivo aqui | origem no Z2Shell | sha256 do original |
|---|---|---|
| `poc/poc_full.py` | `poc/poc_full.py` | `b52026f2…b709` |
| `poc/poc_v7_selfcontained.py` | `poc/exploit_v3_exec/poc_v7_selfcontained.py` | `72615072…27fa` |
| `poc/poc_v8_write.py` | `poc/exploit_v3_exec/poc_v8_write.py` | `a127177e…3cac` |
| `payload/payload.c` | `poc/payload/payload.c` | `e3f0c76b…c90ee` |
| `payload/aeehelperfuncs_slots_oficial.inc` | `poc/aeehelperfuncs_slots_oficial.inc` | `f8894b5a…e2192` |
| `evidence/hello_world.png` | `poc/exploit_v2_hello/evidencia/frame_payload_hello_world.png` | `0f300b13…6964` |
| `evidence/zwheel_normal.png` | `poc/exploit_v2_hello/evidencia/frame_original_normal.png` | `f6dcc921…27c3` |

## O que foi alterado

Uma única coisa nos três POCs: a linha `MOD = r"C:\Users\Esther\Downloads\..."` foi
trocada por leitura da variável de ambiente **`TECTOY_MOD`**, com erro explícito se
ela não existir. Nenhuma lógica foi tocada.

`payload/build.py` **não** foi copiado: o original fixa caminhos de Windows
(`C:\Users\Esther\AppData\...`). `payload/build.py` aqui é uma reescrita portátil
com as mesmas flags oficiais do SDK (a linha de comando está documentada dentro do
arquivo). O credit é do Z2Shell; o código é novo.

## O que NÃO foi copiado, de propósito

- `mod/274755/tectoy.mod` (580 KB) e `research/nand_112/dumps/1.1.2.bin.7z` (34 MB):
  binários da TecToy/firmware. O repo upstream os redistribui; aqui não.
- `research/zeebx-emu/` (emulador vendorizado, GPL-2.0, com patches de instrumentação
  `Z2S-PC`/`Z2S-PB`): já existe em `~/projects/zeebx-emu`.
- As 2119 PNGs / 332 BMPs de evidência, os 65 `.qxm` de strike (até 4 MB cada), os
  traces de 1–2 MB e os desassemblies gerados.
- `poc/flixfile_original.dat` / `poc/flixfile_emboot.dat`: em vez do arquivo da TecToy,
  `flixfile/make_flixfile.py` extrai o `fs:/lctsys/flixfile.dat` **do seu próprio dump**
  e gera a variante `FIRSTAPP:1` preservando CRLF (737 bytes). O upstream distribui
  uma cópia com LF e 708 bytes — ver `docs/z2shell_crosscheck.md` §4c.

## Como rodar os POCs

Precisa de `unicorn` e de uma cópia do shell (`tectoy.mod`), que você extrai do seu
dump ou do próprio clone do Z2Shell:

```bash
export TECTOY_MOD=~/projects/zeebo-exploit-z2shell/mod/274755/tectoy.mod
python3 external/z2shell/poc/poc_full.py          # v5: loader + StructInit + resolver
python3 external/z2shell/poc/poc_v7_selfcontained.py  # v7: cadeia self-contained
python3 external/z2shell/poc/poc_v8_write.py      # v8: write-primitive (harness-armada)
```

Resultado esperado (verificado em 2026-11-23, Unicorn 2.1.2 / capstone 5.0.7):
v5 → `out[0] = blob + 0x1234`; v7 → `out[0] - values = 0x40`, float `777.5`, canary
`0x51CCE7EC`; v8 → `ESCREVEU VIA CODIGO REAL DO SHELL: True` e `PWN=True`
(**atenção:** o PWN do v8 é armado pelo harness — o objeto de playback é construído
à mão; ver `docs/z2shell_crosscheck.md` §3).

## Licença e proveniência — leia antes de publicar

O repositório upstream **não tem arquivo de licença**, ou seja, por padrão todos os
direitos são reservados ao autor. Copiar trechos para um repositório público sem
permissão explícita é juridicamente arriscado. Este diretório:

- existe para uso **local** (pesquisa e reprodução);
- mantém a atribuição completa (origem, commit, hashes);
- **não deve ser publicado** enquanto o autor do Z2Shell não der uma licença
  permissiva (ou autorização por escrito).

Se for publicar o projeto, apague `external/z2shell/` do push, ou peça licença ao
autor (SterTheStar). O conhecimento derivado (as notas em `re/notes.md` §40 e o
cross-check em `docs/`) é reescrito e não contém código de terceiros.
