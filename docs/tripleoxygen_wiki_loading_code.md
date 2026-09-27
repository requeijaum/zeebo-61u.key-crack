====== Carregando seu código ======

Existem duas maneiras de carregar o Zeebo com sua aplicação:

  * Via SD Card, com a opção //Field Test// > //Memory Copy// * do [[EMAPPLET]].
  * Via [[Porta de diagnóstico|interface DIAG]], com o EFS Explorer (disponível no QPST) ou [[Revskills]].

* Esta opção só estará disponível se a porta de diagnóstico estiver **ativa**.

===== Via SD Card =====

É o método aconselhado (apesar de demorado), pois evita usar ferramentas da Qualcomm.

Lembre-se que sua aplicação deve conter os seguintes arquivos no mínimo: mif, mod, sig. Ela também pode conter arquivos .bar (recursos) ou arquivos externos (não aconselhado).

Supondo que sua aplicação se chame "meuapp", copie os arquivos para o cartão SD desta forma:

  * Tenha as pastas "mif" e "mod" na raiz do cartão ("sd" representa o caminho do cartão)

  sd:/mif
  sd:/mod

  * Copie o arquivo "meuapp.mif" para a pasta "mif".
 
  * Crie uma pasta com o nome de seu app dentro de "mod"

  sd:/mod/meuapp

  * Copie os arquivos .mod, .sig, .bar (se existir) para esta nova pasta que acabou de criar.

  * No final teremos:

  sd:/mif/meuapp.mif
  sd:/mod/meuapp/meuapp.mod
  sd:/mod/meuapp/meuapp.sig
  sd:/mod/meuapp/meuapp.bar

  * Se está usando arquivos externos, deverão ficar na mesma pasta, exemplos:

  sd:/mod/meuapp/musica1.mp3
  sd:/mod/meuapp/imagens/sprite.png

Agora, vá ao [[BREW Appmgr]] e execute o EMAPPLET. Ou se preferir, use o comando "em" no OpenOCD para carregar o EMAPPLET diretamente. Você precisa de acesso ao menu "Field Test" do EMAPPLET, e para que isso ocorra você precisa mapear a [[Porta de diagnóstico]] ou executar o comando "field" do OpenOCD. Como o propósito é só fazer a cópia dos arquivos, o comando "field" é mais rápido.

Insira o cartão SD ao Zeebo e acesse:
  EMAPPLET > Field Test > Memory Copy

O Zeebo irá piscar os LEDs superiores enquanto copia. Quando receber a mensagem de cópia com sucesso, você pode voltar e remover o cartão, sua aplicação já está na eNAND.

Agora reinicie o console e faça o método de [[Unlock]] para rodar sua aplicação.

==== Cópia automática ====

Caso no seu SD contenha um arquivo (vazio ou não) no seguinte caminho:

  /longcheerzeebo/autocopysdcardinfotoenand.dat
  
O EMAPPLET iniciará a cópia do SD para seu console automaticamente em alguns segundos após o cartão ser inserido. Este recurso só funcionará se a porta de diagnóstico estiver ativa.
  