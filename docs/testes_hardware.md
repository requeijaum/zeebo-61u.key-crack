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

## Teste 2 — Text Script (15 min)

1. No SD (pode apagar o teste 1), crie a pasta `longcheerzeebo`.
2. Dentro dela, crie o arquivo `autocopysdcardinfotoenand.dat`:
   - Tentativa A: arquivo VAZIO.
   - Tentativa B (se A não fizer nada): com os nomes dos arquivos,
     um por linha (exemplo com um homebrew: pastas `/mif` com o `.mif`
     e `/mod/nome/` com o `.mod` na raiz do SD, e o `.dat` listando
     esses nomes).
3. Desligue, SD dentro, ligue, espere BASTANTE (vários minutos).
4. Observe: alguma tela nova? LED piscando diferente? Jogo novo instalado?
5. **Reporte**: o que aconteceu em cada tentativa + conteúdo exato do `.dat`.

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
