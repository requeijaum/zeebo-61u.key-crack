evil_sd_v1.zip = exemplo congelado da imagem FAT32 maliciosa (LFN 200 chars).
Gerado por: python3 tools/make_evil_sd.py --out evil.raw --format raw
            (opções padrão: 256MB, nomes de 200 chars, com 61u.key de 14xA)
Descompactar: unzip evil_sd_v1.zip  ->  evil.raw (256MB, sector dump + MBR)
Validar:      python3 tools/make_evil_sd.py --verify evil.raw
                + fsck.vfat -n (na partição, skip=32) + mdir
Uso: dd em SD (fora daqui) ou alimentar clusters no Unicorn / dissecar
     no capstone/Ghidra. NÃO montar read-write. Remover o SD recupera
     qualquer bootloop.
Ver: re/notes.md seções 20 (audit), 25 (FAT/LFN), docs/testes_hardware.md.
