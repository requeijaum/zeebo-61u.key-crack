# Cross-check: Z2Shell (SterTheStar) contra o 61u.key

Auditoria do material importado, feita em 2026-11-23 sobre o commit `fa210ba` do
Z2Shell, com **re-execução** dos POCs e **re-verificação estática** das afirmações
sobre a NAND 1.1.2 que interessam a este projeto. O upstream está também como
submódulo em `external/upstream/Z2Shell` (mesmo commit). Onde a conta não fecha,
o número está aqui; o registro técnico completo (com endereços e código) está em
`re/notes.md` §40.

Regra usada: só entra como "confirmado" o que eu reproduzi ou dissertei instrução a
instrução; o resto é marcado como não verificado.

---

## 1. O que se sustenta (e vale para nós)

**1.1 Bug do parser QX — confirmado no disassembly e nos POCs**

`mod+0x3B750` faz `mul r8, #0x9c, count` com `count` lido do arquivo e, depois,
só checa alinhamento (`tst r4,#3`). Nenhum compare contra o tamanho do blob. Os
três POCs rodam em Linux (Unicorn 2.1.2) com o shell real e reproduzem o
documentado:

| POC | resultado medido |
|---|---|
| `poc_full.py` (v5) | loader → StructInit → resolver; `out[0] = blob + 0x1234` |
| `poc_v7_selfcontained.py` (v7) | 1256 B; MatAnim/stream/tabela/valores no próprio arquivo; `out[0]-values = 0x40`, float `777.5`; canary `0x51CCE7EC` |
| `poc_v8_write.py` (v8) | `str [r4,#0x14]` do playback real grava em `HELPER+0x9C`; canary ok |

**1.2 `flixfile.dat` decide o applet de boot — confirmado contra o dump real**

Extraí o arquivo do `1.1.2.bin` (offset `0x6D2A000`, 737 bytes, CRLF): o comentário
do próprio arquivo documenta `0=DEFAULT,1=EM,2=CONFTEST,3=TECTOY`. A variante
`FIRSTAPP:1` boota no EMAPPLET, que expõe Field Test (Memory Copy) e AUXSETTINGS
(SIO Port Map). É a descoberta de maior valor prático do Z2Shell para nós.

**1.3 Pipeline de payload BREW — confirmado por evidência visual**

`payload.mod` (2556 B) tem magic `BREW` em +0x08 — é applet BREW real. O frame
`evidence/hello_world.png` mostra HELLO/WORLD desenhados (fonte bitmap própria,
fundo vermelho): o pipeline SDK 4.0.2 + elf2mod funciona. O emulador encerra a
sessão quando a fila de eventos esvazia (daí o timer periódico) — detalhe útil
para qualquer payload nosso.

---

## 2. O que NÃO se sustenta (com o número na mão)

**2.1 `usb.key` "checado no evento de mount" — errado em três camadas**

O `DEPLOY.md` dá confiança ALTA a isso. Verificação:

- `0x10C4CDD0`, `0x10C4CDE4`, `0x10C4CDF8` **não são handlers**: são registros de
  log `{id, flags, msg_ptr, file_ptr="fs_hotplug.c", enabled=1}` (§36h).
- eles estão **dentro** do APPS.bin (foff `0xB88DD0`), não "fora" como o texto diz.
- a "tabela de handlers por caminho" em `0x10763D80` tem **zero** referências, e a
  região `0x10763D70+` é ilha de dados (a desmontagem degenera exatamente ali);
  `0x10763D40`, citado como "função de polling", é meio de função (sem prólogo).

O check de mount repousa na mesma função `0x107639DA` que este projeto já provou
morta (§36g). Re-rodei com scanner superset (palavras de ponteiro LE32 + Thumb
`b/b.w/bl/blx` + ARM `b/bl/blx`) sobre todos os 14 LOAD segments:
**0 ponteiros, 0 branches**. A leitura correta é a do `TESTE_HARDWARE.md`
(confiança MÉDIA) — ou menos.

**2.2 Autocópia do SD: conclusão certa, método inválido**

O `findptr.py` buscou `0x100A1CF1` e `0x0A1CF1`. `0xA1CF0` é **file offset**; o
paddr correspondente é `0x10AD5CF0` (segmento foff `0x76000` → paddr `0x1013A000`).
Ou seja, o scan de ponteiro procurou o valor errado e não provava nada.

Refiz no endereço certo: **0 ponteiros, 0 branches**. A conclusão "sem chamador
estático" está correta — e agora pode ser tratada como proof, não como incerteza.
Consequência prática: o teste **3.5b** do guia (marcador `autocopysdcardinfotoenand.dat`
no SD disparando a cópia no boot) pode ser aposentado; a cópia vive só dentro do
EMAPPLET.

**2.3 `flixfile.dat`: 737 bytes no guia, 708 no artefato**

O arquivo distribuído é o mesmo conteúdo com CRLF→LF. O guia manda "conferir 737
bytes" e afirma "mesmo tamanho, overwrite in-place seguro" — as duas coisas são
falsas para o artefato. Por isso `external/z2shell/flixfile/make_flixfile.py`
extrai do dump do usuário e preserva CRLF.

**2.4 "PWN=True" no v8 é harness-armado**

A `SESSAO4_qxa.md` diz "PWN FECHADO NO UNICORN COM CÓDIGO REAL ... canary". O que
o `poc_v8_write.py` faz: o objeto de playback (`OBJ/A/B/P`), o alvo
`HELPER+0x9C-0x14` e o ponteiro `P` são montados **no harness**; o passo 5 chama o
slot sequestrado diretamente. É demonstração do primitivo (write real em alvo
arbitrário **se** P for controlável), não exploit. No emulador real, a matriz
(`bf_matrix_results.txt`) mostra `PWN=False` em 25+ execuções. O `README.md` raiz
diz PARCIAL — essa é a versão correta; a `SESSAO4` linha 51 é que exagera.

**2.5 "BREW 4 sem ASLR/DEP" — afirmado, não demonstrado**

Aparece em três documentos como fato. O heap `rw+exec` citado é o **do emulador**
(`map_zeroed` com exec=true), não o do console. É premissa plausível, não achado.
Não usar como base de decisão sem teste.

---

## 3. O que a auditoria acrescentou (não veio do Z2Shell)

**3.1 `arg2` do RDevMap decodificado (§40a)**

O "código 6" que o HANDOFF tratava como bloqueio insolúvel é o **device id** do
RDevMap: `check_61u_key` chama `rdm_assign_port(service=0, device=6)`, e device 6 é
**"USB SER1"** na tabela `RDM_DEV_MAP` do AMSS (`0x17567744`, 24 entradas, lida
pelo getter `0x16E07BFA`, que rejeita `>= 0x18` e copia o nome com limite de 13
bytes).
O "clone" `0x108D07A0` chama `(service=1, device=4)` = **"USB MDM"**. Isso fecha o
§38c e explica o §37b (valores diferentes = devices diferentes, não "sucesso").

**3.2 Terceiro consumidor de `/usb.key` — vivo, na tabela AT (§40b)**

`0x103611EE` (Thumb) faz `adr r0, "/usb.key"` e é referenciado **uma única vez**:
palavra `0x103611EF` em `0x113D0950`, dentro da tabela de comandos AT — entrada
**`+LCTUSBDISABLE`** (o layout da tabela ficou claro: nome inline, padding até 8,
`{id, flags, p1, p2, handler}`). A sequência chama `0x1033088C` (core_ui.c) que
termina em `blx [r0+0x54]` com `(cmd=3, arg, flags=0x7000)` — a mesma
vtable+0x54 que as notas deste projeto chamam de "AUXSETTINGS enable".

Não fechei se `0x112A116A` (wrapper varargs) é open/create de arquivo ou apenas
log da string. O que está provado: **há referência viva, da tabela AT, ao caminho
`/usb.key`, seguida de chamada ao gancho de port-map.** É o próximo item estático,
e não depende de adivinhar volume/partição como o `+LCTUSBLOCK`.

---

## 4. O que isso muda na estratégia

Os dois projetos são metades do mesmo problema:

- Z2Shell tem corrupção controlada + payload BREW válido, mas precisa do DIAG para
  plantar o arquivo;
- este projeto quer o DIAG sem chave e não tem execução de código;
- o elo que falta aos dois é o mesmo: uma primitiva de escrita não autenticada.

Com o §40a, o alvo do payload deixou de ser especulativo: qualquer execução no
ARM11 pode chamar `rdm_assign_port(0, 6)` e mapear `USB SER1` — o unlock. Um applet
BREW que faça isso é o payload final; não precisa de keygen.

Fica valendo o que já estava no `HARDWARE_TODO.md`, com duas correções: o teste do
marcador no SD sai (morto por proof) e o `+LCTUSBLOCK` ganha um irmão mais
interessante (`+LCTUSBDISABLE` → `/usb.key`).
