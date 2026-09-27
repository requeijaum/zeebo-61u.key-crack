====== 61u.key ======

Arquivo contendo uma sequência de 14 caracteres alfanuméricos (a-zA-Z0-9), //case-sensitive//, que serve como chave para ativar a [[porta de diagnóstico]] traseira através de um cartão SD. Um cartão SD inserido no console no momento do boot contendo este mesmo arquivo com a chave, ativará a porta até o próximo reboot.

A lógica ou geração desta sequência é desconhecida e pode ser totalmente aleatória ou obedecer algum padrão baseado em dados do console, como o IMEI.

Este arquivo está presente em todos os consoles com [[sistema|sistemas]] diferentes de 1.1.1.

==== Como extraí-lo? ====

A única maneira possível é via [[JTAG]]. Através dele, podemos forçar o console a entrar no Appmgr ao invés da Z-Wheel. De lá, a porta de DIAG pode ser manualmente ativada, dando assim, acesso ao sistema de arquivos do console para que o arquivo possa ser lido.

==== Como usá-lo? ====

Siga as instruções em [[Porta_de_diagnóstico#Pelo_61u.key|Porta de diagnóstico]].

==== Lista pública para estudos ====

Uma lista de informações de consoles e suas respectivas chaves está sendo construída no seguinte link:

https://docs.google.com/spreadsheets/d/1Rd9UGbUBCqipReINDDyM0gFQITxU_hE3l5IxNtlvLV8/edit?usp=sharing

Ela servirá para estudos e possivelmente, encontrar algum padrão ou lógica de geração para ajudar a todos os proprietários de um Zeebo conseguirem acessar, fazer backup e caso queira, desbloquear seus consoles sem a necessidade de JTAG.

Caso consiga algo, favor entrar em contato comigo em //zeebo$@$tripleoxygen.net// (remova os "$" do endereço antes). Se encontrado uma lógica e eventualmente um gerador ser criado, ele será disponibilizado livremente no Wiki do OpenZeebo.