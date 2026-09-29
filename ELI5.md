# check_61u_key explicado de forma simples

## A ideia em uma frase

O `check_61u_key` é um guarda que compara dois papéis: um guardado dentro do console e outro no cartão SD.

Se os papéis forem iguais, ele manda a mensagem `6`.

Se forem diferentes, ele manda a mensagem `0`.

O problema é que ele também pode mandar `6` quando nem chega a comparar os papéis.

## Onde estão os dois papéis?

- Papel interno:

```text
fs:/mcp/61u.key
```

- Papel no cartão SD:

```text
fs:/card0/61u.key
```

A função analisada está em:

```text
check_61u_key @ 0x108d081c
```

Ela é chamada diretamente por:

```text
bl @ 0x108d2694
```

Ou seja, existe um código anterior que decide chegar até essa verificação. Ainda não sabemos exatamente quando esse chamador executa — por exemplo, se é no boot, em um evento do sistema ou após outra etapa.

## NAND ou RAM?

Pense em duas cópias:

- **NAND:** é a cópia permanente guardada no firmware.
- **RAM:** é a cópia de trabalho, carregada na memória quando o console executa o firmware.

Quase tudo abaixo está gravado na NAND e também aparece na RAM durante a execução. A diferença importante é:

- código e textos fixos vêm da NAND;
- tabelas graváveis, resultados temporários e buffers de arquivo vivem ou podem mudar na RAM.

| Endereço | O que ele busca | Onde fica |
|---|---|---|
| `0x108d2694` | A instrução que chama o `check_61u_key` | Código na NAND, executado a partir da RAM |
| `0x108d081c` | O início do `check_61u_key` | Código na NAND, executado a partir da RAM |
| `0x108d08a4` | O texto fixo `fs:/mcp/61u.key` | Texto fixo na NAND, lido na RAM |
| `0x108d08b4` | O texto fixo `fs:/card0/61u.key` | Texto fixo na NAND, lido na RAM |
| `0x108d06ee` | A rotina que abre um arquivo de chave | Código na NAND, executado a partir da RAM |
| `0x108d07a0` | A rotina alternativa que compara buffers guardados | Código na NAND, executado a partir da RAM |
| `0x10af1534` | A rotina que testa/resolve o caminho e traduz o status | Código na NAND, executado a partir da RAM |
| `0x10aef9d0` | A resolução real do caminho no sistema de arquivos | Código na NAND, executado a partir da RAM |
| `0x10aefaa4` | A pesquisa do status na tabela de tradução | Código na NAND, executado a partir da RAM |
| `0x11425440` | A tabela que transforma status em códigos como `257` e `259` | Dados graváveis copiados da NAND para a RAM |
| `0x1141e4f8` | A variável global que guarda os resultados/buffers abertos | Dados graváveis copiados da NAND para a RAM |
| `0x109834c8` | O atalho que leva ao `strcmp` otimizado | Código na NAND, executado a partir da RAM |
| `0x101d7ec8` | A implementação do `strcmp` que compara os conteúdos | Código na NAND, executado a partir da RAM |
| `0x1079e4a0` | O atalho PLT para o cliente RDevMap | Código na NAND, executado a partir da RAM |
| `0x103693e8` | O cliente RDevMap que empacota a resposta em RPC | Código na NAND, executado a partir da RAM |
| `0x1036942a` | O ponto onde o cliente carrega o identificador da interface RPC | Código na NAND, executado a partir da RAM |
| `0x143bd5f` no AMSS | O texto `rdevmap.c`, que identifica o serviço no firmware do modem | Texto fixo na NAND do modem, lido na RAM do modem |
| `0x143bdbb` no AMSS | A mensagem `Invalid cmd: %d`, usada na validação do comando recebido | Texto fixo na NAND do modem, lido na RAM do modem |
| `0x143bdee` no AMSS | A mensagem `Invalid DEVMAP State: %d`, usada na validação do estado | Texto fixo na NAND do modem, lido na RAM do modem |
| `0x170a2e16` no AMSS | O texto `rdevmap_svc.c`, que identifica o lado servidor do RPC | Texto fixo na NAND do modem, lido na RAM do modem |

## O que ele faz, passo a passo

### 1. Procura o papel interno

Primeiro ele pergunta ao sistema de arquivos onde está o papel interno.

Três resultados são possíveis:

- Não encontra o papel interno  
  → manda `6`.

- Encontra o papel interno, mas o sistema devolve um status diferente de zero  
  → manda `6`.

- Encontra o papel interno com status exatamente zero  
  → continua para a comparação.

Esse é um detalhe importante: **nem sempre ele compara os dois arquivos**.  
Em dois casos, ele manda `6` antes da comparação.

### 2. Procura o papel no SD

Se passou da primeira etapa, ele procura:

```text
fs:/card0/61u.key
```

Se a resolução do cartão falhar aqui, o resultado observado é `0`, e o caminho da comparação não termina em sucesso.

### 3. Abre os dois arquivos

Ele abre os dois arquivos e guarda seus conteúdos na memória.

Se algum conteúdo estiver ausente ou inválido, o resultado é:

```text
0
```

### 4. Compara letra por letra

A comparação usa uma função `strcmp` otimizada em ARM.

```text
conteúdo interno == conteúdo do SD → 6
conteúdo interno != conteúdo do SD → 0
```

Não há:

- criptografia;
- verificação de IMEI;
- verificação de tamanho especial;
- senha secreta calculada no aparelho.

Quando chega a essa etapa, a única pergunta é: **os dois textos são iguais?**

Existe ainda uma rotina quase gêmea em `0x108d07a0`, mas ela não tem chamador direto conhecido. Por isso, o caminho principal documentado acima continua sendo o do `check_61u_key`.

## Para quem ele manda a resposta?

Ele não liga ou desliga a porta diretamente.

Ele envia a resposta por RPC para outro programa, o serviço RDevMap, que cuida do mapeamento das portas.

Simplificando:

```text
check_61u_key → mensagem 0 ou 6 → serviço de portas → decisão final
```

Por isso ainda não sabemos exatamente o que `6` faz no destino. Pode significar:

1. habilitar a porta de diagnóstico;
2. manter o mapeamento já gravado;
3. outro comando do serviço.

Essa é a principal incógnita atual.

Um agravante: existe uma função quase gêmea em `0x108d07a0` que faz a mesma
comparação, mas manda `4` em vez de `6` quando os papéis são iguais. Isso mostra
que o número enviado depende de **quem** está perguntando, e não significa
sozinho "destravou" ou "não destravou". Ele é lido e interpretado pelo outro
programa.

## Por que remover a chave interna pode funcionar?

Se o papel interno não for encontrado, o fluxo toma um atalho:

```text
chave interna ausente → helper retorna 259 → RPC(0, 6)
```

E um par de chaves iguais também produz:

```text
chaves iguais → RPC(0, 6)
```

Ou seja, no lado analisado até agora, **ausência da chave interna e chaves iguais geram a mesma mensagem observada**.

Mas ainda existe uma ressalva: uma chave interna presente e não vazia também pode gerar `6` sem comparar. Como existem consoles travados mesmo tendo chave interna, `6` provavelmente não significa automaticamente “destravar”. É um forte candidato, mas não uma prova final.

E, como visto acima, `6` não é um valor único de sucesso: outra função manda `4` na mesma situação. Por isso o número sozinho não decide nada.

## Outra forma possível de explorar

Como a comparação só exige igualdade, em teoria não precisamos descobrir a chave original.

Bastaria colocar o mesmo conteúdo controlado nos dois lugares:

```text
fs:/mcp/61u.key
fs:/card0/61u.key
```

O arquivo do SD é fácil de controlar. O difícil é escrever o arquivo interno.

Um possível caminho é o comando AT:

```text
AT+LCTUSBLOCK="<conteúdo>"
```

Mas ainda falta confirmar:

- se esse canal funciona sem diagnóstico;
- qual porta o recebe;
- se ele escreve realmente em `fs:/mcp`;
- qual ramo do firmware o novo arquivo seleciona.

## O que não funciona mais como antes

O antigo truque do arquivo vazio:

```text
usb.key
```

era documentado para a versão 1.1.

Na versão 1.1.2 analisada, a função que consumiria esse arquivo está presente, mas **não tem chamadores conhecidos**. Portanto, ela provavelmente não executa, e criar o arquivo vazio no SD tem previsão de não fazer efeito.
