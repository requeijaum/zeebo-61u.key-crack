# Testes de hardware (para quem tem Zeebo bloqueado + SD + PC)

> Nada aqui abre o console nem solda nada. Só SD card e botão.
> Faça na ordem (do mais simples ao mais elaborado) e REPORTE tudo,
> inclusive o que NÃO funcionou.

## O que é cada coisa (simples)

- **`61u.key`**: arquivo de 14 letras/números que libera a porta de
  diagnóstico. Cada console tem o seu. A gente quer saber se QUALQUER
  conteúdo funciona ou se precisa ser o original.
- **"Text Script"**: um desenvolvedor da época disse que bastava um
  arquivo de texto no SD para o Zeebo instalar jogos sozinho, em
  qualquer console, sem chave. Achamos no firmware o mecanismo
  correspondente (`autocopysdcardinfotoenand.dat`). Queremos saber se
  ele funciona e com que conteúdo.
- **EMAPPLET**: tela de engenharia que abre com botão (sem chave), com
  opção de copiar coisas do SD para o console.

## Teste 1 — Chave falsa (5 min)

1. No PC, crie um arquivo com o conteúdo `AAAAAAAAAAAAAA` (14 letras A).
2. Salve como `61u.key` (só isso, sem `.txt` no final!).
3. Copie para a RAIZ do SD card. Só esse arquivo.
4. Desligue o Zeebo, coloque o SD, ligue, espere a tela do Dragon.
5. Conecte o USB traseiro no PC: a porta de diagnóstico apareceu?
   (No Windows: Gerenciador de Dispositivos → Portas COM; algo novo?)
6. **Reporte**: apareceu ou não + versão do sistema do console.

## Teste 2 — Text Script / auto-copy (15 min)

> Correção importante (wiki `Carregando seu código`): a cópia automática
> exige a porta de diagnóstico ATIVA. Sem DIAG, nada acontece — então
> este teste só vale em console desbloqueado ou com `61u.key` válido.
> Mesmo assim vale rodar: confirma o mecanismo.

1. No SD: pastas `/mif` e `/mod/nome/` na raiz (ex: um homebrew com
   `.mif`, `.mod`, `.sig`).
2. Crie a pasta `/longcheerzeebo` com o arquivo
   `autocopysdcardinfotoenand.dat` (pode ser VAZIO).
3. Com DIAG ativo: Appmgr → EMAPPLET → Field Test → Memory Copy
   (ou só insira o SD e espere — a cópia pode disparar sozinha em
   segundos; os LEDs piscam durante a cópia).
4. **Reporte**: copiou? Mensagem de sucesso? App aparece após reboot?
   (Para RODAR o app ainda precisa do Unlock — a checagem de assinatura
   é no load, não na instalação.)

## Teste 3 — EMAPPLET Memory Copy (15 min)

1. Com o console ligado, segure **ZL + direcional Cima + botão 3 +
   Home** (abre telas de sistema/engenharia).
2. Procure o EMAPPLET / Field Test / Memory Copy.
3. Com SD contendo `/mif` + `/mod/` de um homebrew, tente o Memory Copy.
4. **Reporte**: chegou até onde? Alguma opção pede chave/DIAG? Erro?

## Teste 4 — Cabo USB + programas de diagnóstico (30 min, PC Windows)

1. Instale o driver do Zeebo ( TripleOxygen ) e o RevSkills 2.04.
2. Sem SD com chave: conecte o USB, abra o RevSkills → DIAG →
   "Get HW Details". Respondeu algo ou travou?
3. Repita ligando o console COM o SD já inserido (janela de boot).
4. **Reporte**: qualquer resposta diferente de erro/travamento.

## O que anotar sempre

- Versão do sistema (1.1.0 / 1.1.1 / 1.1.2?) e região (BR/MX).
- Console bloqueado ou desbloqueado?
- Conteúdo EXATO de cada arquivo testado.
- Fotos/vídeo do que aparecer na tela.
