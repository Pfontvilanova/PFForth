Pfforth language is a forth with python primitives. you need to see the wiki tab for a user manual. you can run it in every device with python an at less 1MB of memory for the core, better more than 5 MB if you want to install all extensions. To run it you must download the folders and the files to your computer. then run python.

from pfforth import InteractiveForth
f = InteractiveForth()

this is the python interactive way, if you want the rel mode you mus do also:
f.repl()
and you will see the 
ok> in the screen. On ipad I use A-shell and jupyter notebook, in mac the terminal. A-shell also in Iphone.

A second way is: from terminal
python main.py
appears
>>> on screen. is python way, you can use python interactive mode, and if you want the repl mode you need also write:
f.repl()

The next is how I start from A-shell on my Ipad:

[~/Documents/ForthInsight]$ python main.py
============================================================
PFForth v2.0 - Modular Edition
Pere Font 2025
============================================================

Instancia de Forth creada como 'f'

Ejemplos DSL:
  f.push(10, 20).add().dot()       # 30
  f.execute('10 20 + .')           # 30

Para REPL de Forth:
  f.repl()                         # REPL interactivo

Documentacion:
  f.execute('help')                # Ver palabras
  f.execute('words')               # Listar palabras
============================================================

>>> f.repl()
PFForth v2.0 - Modular Edition
Escribe 'bye' para salir, 'help' para ayuda

OK> 
