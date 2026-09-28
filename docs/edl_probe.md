# EDL probe no Zeebo (MSM7201A) — roteiro

> Status: NÃO TESTADO. Procedimento de entrada em EDL no Zeebo é
> desconhecido; o que segue é a escada, do menos pro mais invasivo.
> Objetivo: PID USB `0x9008` (Qualcomm HS-USB QDLoader). Se aparecer,
> ler HWID/PK_HASH com `bkerler/edl` responde a pergunta do secure boot
> (fused vs unfused) e pode liberar leitura/escrita da NAND.

## Ferramentas (PC Linux)

```bash
git clone https://github.com/bkerler/edl && cd edl
pip install pyusb pyserial
sudo cp Drivers/51-edl.rules /etc/udev/rules.d && sudo udevadm control -R
```

## Escada de entrada (tentar nesta ordem)

1. **Observar**: `lsusb` + `watch` enquanto liga o console de vários
   jeitos (power; power+Home; power+botões). Anotar qualquer VID:PID
   Qualcomm (`05c6:9008` = EDL, `05c6:9006/900e` = relacionado).
2. **Cabo EDL (deep-flash)**: curto D+ com GND no plug USB ao ligar.
   Não abre o console; às vezes força 9008.
3. **Modem AT (se a interface modem enumerar)**: `AT!BOOTHOLD` /
   `AT!QPSTDLOAD` podem jogar o modem em download.
4. **Test-points/JTAG**: último recurso (abrir o console).

## Se o 9008 aparecer

```bash
./edl.py -secureboot     # diz se é fused (precisa loader assinado) ou não
./edl.py printgpt        # tabela de partições
./edl.py -r <part> f.bin # backup antes de qualquer escrita!
```

Loader para MSM7201A: tentar os genéricos `NPRG*.bin`/`FHPRG` da pasta
`Loaders/` do edl; específico provavelmente não existe público.
Se unfused, qualquer loader serve — e aí dá pra patchear o strcmp
(`04d1→00bf` no offset `0x80c864` do APPS) direto na NAND.

## Riscos

- Escrita errada bricka (sem JTAG por perto, NÃO escreva).
- Só LEIA nas primeiras tentativas (`printgpt`, `-r`).
