====== Porta de diagnóstico ======

O Zeebo oferece uma porta USB Device na parte traseira que pode ser ativada para diagnóstico, transferência de dados e auxílio na depuração de aplicativos rodando no console.

Ela vem desativada de fábrica para evitar que os usuários façam alterações nos arquivos ou extraiam informações internas.

Esta porta - apesar de ser USB 2.0 - apresenta vários problemas e geralmente enumera apenas em 1.1 (full-speed). Controladoras USB mais recentes dificilmente conseguirão enumerar o console, portanto para usar esta porta, possivelmente precisará de um PC mais antigo.

===== Como ativá-la =====
Existem duas maneiras de ativá-la: manualmente pelo AUXSETTINGS (utilitário acessível pelo [[BREW Appmgr]]) ou através da chave [[61u.key]].

==== Pelo AUXSETTINGS ====
Você deve ter acesso ao [[BREW Appmgr]] para acessá-lo. Via [[JTAG]], use o comando "brew".

Do Appmgr, abra o aplicativo "AUXSETTINGS". Nele, navegue em:
 SIO Configuration > Port Map > Diag

Selecione "USB SER1" e confirme. Ele voltará a tela de Port Map. Volte até sair do aplicativo.

==== Pelo 61u.key ====
De posse de seu [[61u.key]], coloque-o na raiz de um cartão SD. Desligue o console e insira o cartão. Ligue o Zeebo e aguarde até aparecer a primeira tela com as instruções do Dragon.

==== Pelo usb.key ====

Caso a versão de seu console seja **[[sistema|1.1.1]]**, crie um arquivo de nome [[usb.key]], vazio, na raiz de um cartão SD. Desligue o console e insira o cartão. Ligue o Zeebo e aguarde até aparecer a primeira tela com as instruções do Dragon.

===== Modos da porta DIAG =====
Sua porta DIAG pode trabalhar de duas formas: Download ou Trace.
  * Download - Apresenta 3 interfaces ao seu PC: Diag, NMEA, Modem.
    * Diag - Porta de diagnóstico, transferência de dados
    * NMEA - Fornece dados NMEA (coordenadas) do GPS (no Zeebo, sem função)
    * Modem - Dá acesso ao modem do console. Talvez ativada no futuro para usar o console como modem.
  * Trace - Apresenta apenas uma interface ao seu PC: Diag.
    * Diag - Mesma funcionalidade acima

A diferença entre elas é que no modo Download, os outros controladores USB são desativados, deste modo, não se pode usar o nenhum periférico (teclado, Dragon, etc) enquanto o Zeebo estiver ligado ao PC. No modo Trace isso não acontece, já que o propósito deste modo é oferecer uma saída de informações dos aplicativos enquanto eles funcionam e assim auxiliar o desenvolvedor.

Estes modos podem ser definidos através do [[EMAPPLET]].

===== Comunicando com o Zeebo =====
Após mapear e ativar a porta por um dos dois métodos acima, basta conectar o Zeebo ao PC. O SO detectará o hardware e solicitará o driver caso ainda não esteja instalado. 

==== Drivers ====
O driver para instalar as portas do Zeebo no PC pode ser obtido através do SDK oficial ou deste //mirror// local: 
  * 32-bit [[https://www.tripleoxygen.net/files/devices/zeebo/driver/Zeebo-Driver-V0.2.zip]]
  * 64-bit [[https://www.tripleoxygen.net/files/devices/zeebo/driver/vista_7_x64.7z]]

==== Aplicações ====
Existem 2 aplicações que podem ser utilizadas para navegar no EFS (sistema de arquivos do BREW) do Zeebo:

  * [[EFS TOOL]] by Yoshihiro [[http://www.4shared.com/file/136359546/96799604/LG_EFS_TOOLS.html | Link]]

  * [[RevSkills]] by bkerler (a versão Free é o suficiente) [[http://psas.revskills.de/?q=node/6 | Link]]
    * [[https://www.tripleoxygen.net/files/devices/zeebo/tool/revskills2.04.zip | Download local]] 



Existem também as ferramentas oficiais da Qualcomm - tal como o QPST - que são opções comerciais, por isso torna-se inviável para nós.

Para usar estas ferramentas, leia os respectivos artigos.