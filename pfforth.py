import math
import os
import sys
import select
import time
import importlib.util

class Forth:
    def __init__(self):
        self.stack = []          # Pila de datos principal
        self.rstack = []         # Pila de retorno
        self.words = {}
        self.variables = {}      # Diccionario para variables: nombre -> valor
        self.constants = {}      # Diccionario para constantes
        self.values = {}         # Diccionario para values
        self.immediate_words = {}  # Diccionario para palabras inmediatas

        # Registro ordenado de todas las definiciones
        self._definition_order = []  # Lista de tuplas (tipo, nombre)
        self._definition_source = {}  # Diccionario nombre -> código fuente original
        self._defining = False
        self._current_definition = []
        self._current_name = None
        self._last_defined_word = None

        # Detectar directorio base (funciona en scripts y Jupyter)
        try:
            self._base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # __file__ no está definido en Jupyter/IPython
            self._base_dir = os.path.abspath(os.getcwd())

        # Sistema de memoria dinámica - 64KB
        self._memory_size = 65536  # 64KB de memoria
        self._pad_size = 256  # Tamaño del área PAD (protegida)
        self.memory = [0] * self._memory_size
        self.here = self._pad_size  # Puntero de memoria (empieza después de PAD)

        # Sistema de ejecución diferida
        self._tick_mode = False
        self._compiling_tick = False

        # Flag para [ ] - interpretación temporal durante compilación
        self._bracket_mode = False

        # Sistema de bucles DO/LOOP
        self._loop_stack = []  # Pila para índices y límites de bucles
        self._leave_flag = False  # Flag para LEAVE
        self._exit_flag = False  # Flag para EXIT (salir de palabra actual)

        # Sistema de control IF/THEN/ELSE
        self._control_stack = []  # Pila para rastrear saltos pendientes de IF/ELSE

        # Sistema CREATE/DOES>
        self._last_created_word = None  # Última palabra creada con CREATE
        self._last_created_address = None  # Dirección de la última palabra CREATE

        # Input stream para CREATE runtime
        self._input_tokens = []
        self._input_index = 0

        # BASE numérica (decimal, hex, binary)
        self._create_variable('base')
        self.variables['base'] = 10  # Por defecto, decimal

        # Sistema CODE/ENDCODE para extensiones Python
        self._code_mode = False  # Flag para captura de código Python
        self._code_name = None  # Nombre de la palabra CODE (incluye grupo/nombre)
        self._code_buffer = []  # Buffer para acumular líneas de código Python

        self._register_core_words()

    def _register_core_words(self):
        # Aritméticas básicas
        self.words['+'] = self._plus
        self.words['-'] = self._minus
        self.words['*'] = self._mult
        self.words['/'] = self._div
        self.words['/mod'] = self._divmod
        self.words['1+'] = self._one_plus
        self.words['1-'] = self._one_minus

        # Comparaciones con cero
        self.words['0='] = self._zero_equal
        self.words['0<'] = self._zero_less
        self.words['0>'] = self._zero_greater

        # Stack operations
        self.words['dup'] = self._dup
        self.words['drop'] = self._drop
        self.words['swap'] = self._swap
        self.words['over'] = self._over
        self.words['.'] = self._dot
        self.words['.r'] = self._dot_r
        self.words['.s'] = self._dot_s

        # Sistema
        self.words['words'] = self._list_words
        self.words['clear'] = self._clear_stack
        self.words['see'] = self._see
        self.words['help'] = self._help
        self.words['measure'] = self._measure
        self.words['code'] = self._code_stub
        self.words['endcode'] = self._endcode_stub
        self.words['import'] = self._import_stub
        self.words['lscode'] = self._lscode
        self.words['vlist'] = self._vlist
        self.words['rmcode'] = self._rmcode_stub
        self.words['seecode'] = self._seecode_stub

        # Palabras para cadenas
        self.words['type'] = self._type
        self.words['evaluate'] = self._evaluate
        self.words['s>mem'] = self._s_to_mem
        self.words['parse'] = self._parse
        self.words['cr'] = self._cr
        self.words['page'] = self._page

        # Variables y memoria
        self.words['@'] = self._fetch
        self.words['!'] = self._store

        # Pila de retorno
        self.words['>r'] = self._to_r
        self.words['r>'] = self._from_r
        self.words['r@'] = self._r_fetch

        # Palabra forget
        self.words['forget'] = self._forget

        # Palabra immediate - INMEDIATA
        self.immediate_words['immediate'] = self._immediate

        # Memoria dinámica
        self.words['here'] = self._here
        self.words['allot'] = self._allot
        self.words['buffer'] = self._buffer
        self.words[','] = self._comma
        self.words['m@'] = self._m_fetch
        self.words['m!'] = self._m_store
        self.words['dump'] = self._dump
        self.words['cells'] = self._cells

        # Nuevas operaciones de memoria
        self.words['+!'] = self._plus_store
        self.words['?'] = self._question
        self.words['fill'] = self._fill
        self.words['erase'] = self._erase
        self.words['move'] = self._move
        self.words['cmove'] = self._cmove
        self.words['cmove>'] = self._cmove_up
        self.words['cell+'] = self._cell_plus

        # Guardado y carga de archivos
        self.words['save'] = self._save_words
        self.words['load'] = self._load_file
        self.words['lssave'] = self._lssave
        self.words['rmsave'] = self._rmsave
        self.words['pwd'] = self._pwd

        # Operaciones de bytes
        self.words['c@'] = self._c_fetch
        self.words['c!'] = self._c_store
        self.words['mc@'] = self._mc_fetch
        self.words['mc!'] = self._mc_store
        self.words['c,'] = self._c_comma
        self.words['emit'] = self._emit
        self.words['key'] = self._key
        self.words['key?'] = self._key_question
        self.words['accept'] = self._accept
        self.words['pad'] = self._pad

        # Bucles DO/LOOP
        self.words['i'] = self._loop_i
        self.words['j'] = self._loop_j
        self.words['k'] = self._loop_k
        self.words['leave'] = self._loop_leave
        self.words['exit'] = self._exit_word
        # RECURSE - recursión en definiciones
        self.immediate_words['recurse'] = self._recurse
        # Registrar do, loop, +loop para que aparezcan en words (manejadas especialmente en execute)
        self.immediate_words['do'] = self._do_marker
        self.immediate_words['loop'] = self._loop_marker
        self.immediate_words['+loop'] = self._plusloop_marker

        # Condicionales IF/THEN/ELSE (solo en modo compilación)
        self.immediate_words['if'] = self._if_marker
        self.immediate_words['else'] = self._else_marker
        self.immediate_words['then'] = self._then_marker

        # Bucles BEGIN/UNTIL/AGAIN/WHILE/REPEAT
        self.immediate_words['begin'] = self._begin_marker
        self.immediate_words['until'] = self._until_marker
        self.immediate_words['again'] = self._again_marker
        self.immediate_words['while'] = self._while_marker
        self.immediate_words['repeat'] = self._repeat_marker

        # Ejecución diferida
        self.words["'"] = self._tick
        self.words['execute'] = self._execute_word
        self.immediate_words["[']"] = self._bracket_tick

        # Palabras para espacios y caracteres
        self.words['space'] = self._space
        self.words['bl'] = self._bl
        self.immediate_words['char'] = self._char_immediate
        self.immediate_words['[char]'] = self._bracket_char

        # Palabras de strings (manejadas especialmente en el parser)
        self.immediate_words['."'] = self._dot_quote
        self.immediate_words['s"'] = self._s_quote

        # POSTPONE - compilación diferida de palabras inmediatas
        self.immediate_words['postpone'] = self._postpone

        # CREATE/DOES> - meta-programación avanzada
        self.immediate_words['create'] = self._create  # CREATE es inmediata
        self.immediate_words['does>'] = self._does

        # Comentarios
        self.immediate_words['('] = self._paren_comment

        # Literal - Compila un valor de la pila
        self.immediate_words['literal'] = self._literal

        # Palabra [ ] - modo interpretación temporal
        self.immediate_words['['] = self._open_bracket
        self.immediate_words[']'] = self._close_bracket

        # Variable STATE - indica modo de compilación
        # 0 = interpretación, -1 = compilación
        self._create_variable('state')
        self.variables['state'] = 0  # Inicialmente en modo interpretación

    # Núcleo de operaciones
    def _plus(self):
        if len(self.stack) >= 2:
            self.stack.append(self.stack.pop() + self.stack.pop())

    def _minus(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a - b)

    def _mult(self):
        if len(self.stack) >= 2:
            self.stack.append(self.stack.pop() * self.stack.pop())

    def _div(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            if b != 0:
                # Usar división entera si ambos son enteros
                if isinstance(a, int) and isinstance(b, int):
                    self.stack.append(a // b)
                else:
                    self.stack.append(a / b)
            else:
                print("Error: division by zero")
                self.stack.extend([a, b])

    def _divmod(self):
        """/MOD : División con resto ( n1 n2 -- resto cociente )
        Ejemplo: 17 5 /mod → 2 3 (resto=2, cociente=3)
        """
        if len(self.stack) >= 2:
            divisor = self.stack.pop()
            dividendo = self.stack.pop()
            if divisor != 0:
                resto = dividendo % divisor
                cociente = dividendo // divisor
                self.stack.append(resto)      # resto primero (estándar Forth)
                self.stack.append(cociente)   # cociente segundo
            else:
                print("Error: division by zero")
                self.stack.extend([dividendo, divisor])
        else:
            print("Error: /MOD requiere 2 valores en la pila")

    def _one_plus(self):
        """1+ : Incrementa el valor en el tope de la pila en 1"""
        if self.stack:
            self.stack.append(self.stack.pop() + 1)
        else:
            print("Error: pila vacía para 1+")

    def _one_minus(self):
        """1- : Decrementa el valor en el tope de la pila en 1"""
        if self.stack:
            self.stack.append(self.stack.pop() - 1)
        else:
            print("Error: pila vacía para 1-")

    def _zero_equal(self):
        """0= : Verifica si el tope es igual a cero (flag: -1=true, 0=false)"""
        if self.stack:
            value = self.stack.pop()
            self.stack.append(-1 if value == 0 else 0)
        else:
            print("Error: pila vacía para 0=")

    def _zero_less(self):
        """0< : Verifica si el tope es menor que cero (flag: -1=true, 0=false)"""
        if self.stack:
            value = self.stack.pop()
            self.stack.append(-1 if value < 0 else 0)
        else:
            print("Error: pila vacía para 0<")

    def _zero_greater(self):
        """0> : Verifica si el tope es mayor que cero (flag: -1=true, 0=false)"""
        if self.stack:
            value = self.stack.pop()
            self.stack.append(-1 if value > 0 else 0)
        else:
            print("Error: pila vacía para 0>")

    def _dup(self):
        if self.stack:
            self.stack.append(self.stack[-1])

    def _drop(self):
        if self.stack:
            self.stack.pop()

    def _swap(self):
        if len(self.stack) >= 2:
            a, b = self.stack.pop(), self.stack.pop()
            self.stack.extend([a, b])

    def _over(self):
        if len(self.stack) >= 2:
            self.stack.append(self.stack[-2])

    def _dot(self):
        if self.stack:
            value = self.stack.pop()
            base = self.variables.get('base', 10)

            # Verificar si es un número
            try:
                # Si es un float con parte decimal, imprimirlo como float
                if isinstance(value, float) and value != int(value):
                    print(value, end=' ')
                    sys.stdout.flush()
                    return
                
                # Si es entero o float sin decimales (ej: 5.0), convertir a int
                int_value = int(value)
            except (ValueError, TypeError):
                # Si no se puede convertir, imprimir tal cual
                print(value, end=' ')
                sys.stdout.flush()
                return

            # Formatear según la base
            if base == 16:
                # Hexadecimal (sin prefijo 0x)
                print(format(int_value, 'x'), end=' ')
            elif base == 2:
                # Binario (sin prefijo 0b)
                print(format(int_value, 'b'), end=' ')
            elif base == 8:
                # Octal (sin prefijo 0o)
                print(format(int_value, 'o'), end=' ')
            else:
                # Decimal u otra base
                print(int_value, end=' ')
            sys.stdout.flush()

    def _dot_r(self):
        """.R ( n width -- ) Imprime n right-aligned en campo de ancho 'width'
        Ejemplo: 42 5 .r → "   42 " (justificado a la derecha)
        """
        if len(self.stack) >= 2:
            width = int(self.stack.pop())
            n = self.stack.pop()
            base = self.variables.get('base', 10)

            # Convertir número a string según la base
            try:
                int_value = int(n)
            except (ValueError, TypeError):
                # Si no se puede convertir, imprimir tal cual
                num_str = str(n)
                formatted = num_str.rjust(width)
                print(formatted, end=' ')
                sys.stdout.flush()
                return

            # Formatear según la base
            if base == 16:
                num_str = format(int_value, 'x')
            elif base == 2:
                num_str = format(int_value, 'b')
            elif base == 8:
                num_str = format(int_value, 'o')
            else:
                num_str = str(int_value)

            # Justificar a la derecha con espacios
            formatted = num_str.rjust(width)
            print(formatted, end=' ')
            sys.stdout.flush()
        else:
            print("Error: .R requiere dos valores en la pila (n width)")

    def _dot_s(self):
        base = self.variables.get('base', 10)

        # Formatear elementos según la base
        formatted_stack = []
        for item in self.stack:
            try:
                int_value = int(item)
                if base == 16:
                    formatted_stack.append(format(int_value, 'x'))
                elif base == 2:
                    formatted_stack.append(format(int_value, 'b'))
                elif base == 8:
                    formatted_stack.append(format(int_value, 'o'))
                else:
                    formatted_stack.append(str(int_value))
            except (ValueError, TypeError):
                formatted_stack.append(str(item))

        print(f"<{len(self.stack)}> {formatted_stack}")

        if self.rstack:
            formatted_rstack = []
            for item in self.rstack:
                try:
                    int_value = int(item)
                    if base == 16:
                        formatted_rstack.append(format(int_value, 'x'))
                    elif base == 2:
                        formatted_rstack.append(format(int_value, 'b'))
                    elif base == 8:
                        formatted_rstack.append(format(int_value, 'o'))
                    else:
                        formatted_rstack.append(str(int_value))
                except (ValueError, TypeError):
                    formatted_rstack.append(str(item))
            print(f"R:<{len(self.rstack)}> {formatted_rstack}")

        return self

    def _cr(self):
        print()

    def _page(self):
        """Limpia la pantalla - palabra STANDARD Forth"""
        clear_screen()
        sys.stdout.flush()

    def _space(self):
        """Imprime un espacio - palabra STANDARD Forth"""
        print(' ', end='')
        sys.stdout.flush()

    def _bl(self):
        """Coloca el valor ASCII del espacio (32) en la pila - palabra STANDARD Forth"""
        self.stack.append(32)

    def _char_immediate(self):
        """Palabra CHAR - obtiene el código ASCII del siguiente carácter"""
        # Esta función se llamará desde execute() que ya maneja el parsing
        pass

    def _bracket_char(self):
        """Palabra [CHAR] - versión compilada de CHAR"""
        # Esta función se llamará desde execute() que ya maneja el parsing
        pass

    def _dot_quote(self):
        """Palabra ." - imprime un string
        Uso: ." texto aquí"
        """
        # Esta función se maneja especialmente en el parser (_simple_tokenize)
        pass

    def _s_quote(self):
        """Palabra s" - coloca un string en la pila
        Uso: s" texto aquí"
        """
        # Esta función se maneja especialmente en el parser (_simple_tokenize)
        pass

    def _paren_comment(self):
        """Palabra ( - comentarios en Forth
        Uso: ( esto es un comentario )
        """
        # Esta función se maneja especialmente en el parser (_simple_tokenize)
        # Los comentarios se eliminan antes de que los tokens lleguen a execute()
        pass

    def _postpone(self):
        """Palabra POSTPONE - compila palabras inmediatas en definiciones"""
        # Esta función se llamará desde execute() que ya maneja el parsing
        if not self._defining:
            print("Error: POSTPONE solo se puede usar durante compilación")
        # El resto se maneja en execute()
        pass

    def _create(self):
        """Palabra CREATE - crea una palabra que empuja su dirección de memoria
        Uso: CREATE nombre
        Luego opcionalmente se puede usar DOES> para definir comportamiento
        """
        # Esta función se llama desde execute() que maneja el nombre
        pass

    def _does(self):
        """Palabra DOES> - define el comportamiento de runtime de la última palabra CREATE
        Debe usarse dentro de una definición con ':'
        """
        if not self._defining:
            print("Error: DOES> solo se puede usar durante compilación")
            return

        if not self._last_created_word:
            print("Error: DOES> requiere una palabra creada con CREATE")
            return

        # Esta función se maneja especialmente en execute()
        pass

    def _literal(self):
        """LITERAL - compila un valor numérico de la pila en la definición"""
        # Esta función se llama desde _execute_token cuando _defining es True
        # y el token es un número. Se añade como ('literal', valor)
        pass

    def _open_bracket(self):
        """[ - entra en modo de interpretación temporal durante compilación"""
        if self._defining:
            self._bracket_mode = True
            # Cambiar state a interpretación
            self.variables['state'] = 0
        else:
            print("Error: [ solo se puede usar durante compilación")

    def _close_bracket(self):
        """] - sale del modo de interpretación temporal y vuelve a compilación"""
        if self._defining:
            self._bracket_mode = False
            # Restaurar state a compilación
            self.variables['state'] = -1
        else:
            print("Error: ] solo se puede usar durante compilación")

    def _clear_stack(self):
        self.stack.clear()
        return self

    # Operaciones de pila de retorno
    def _to_r(self):
        if self.stack:
            self.rstack.append(self.stack.pop())

    def _from_r(self):
        if self.rstack:
            self.stack.append(self.rstack.pop())

    def _r_fetch(self):
        if self.rstack:
            self.stack.append(self.rstack[-1])

    # Implementación de immediate
    def _immediate(self):
        if self._last_defined_word:
            for i, (def_type, name) in enumerate(self._definition_order):
                if name == self._last_defined_word and def_type == 'word':
                    if self._last_defined_word in self.words:
                        self.immediate_words[self._last_defined_word] = self.words[self._last_defined_word]
                        del self.words[self._last_defined_word]
                        self._definition_order[i] = ('immediate', self._last_defined_word)
                        print(f"Palabra '{self._last_defined_word}' marcada como IMMEDIATE")
                    break
            else:
                print(f"Error: '{self._last_defined_word}' no encontrada en definiciones")
        else:
            print("Error: no hay palabra recién definida para marcar como immediate")

    def _is_system_word(self, name):
        """Una palabra es del sistema si NO está en definiciones de usuario (word, immediate, code, etc.)"""
        # Cualquier palabra en _definition_order es palabra de usuario (puede redefinirse)
        user_words = {word_name for (_, word_name) in self._definition_order}
        
        # Si está en definiciones de usuario, NO es palabra del sistema
        if name in user_words:
            return False
        
        # Si existe en diccionarios pero NO en _definition_order, es del sistema
        is_in_dictionaries = (name in self.words or 
                              name in self.immediate_words or 
                              name in self.variables or 
                              name in self.constants or 
                              name in self.values)
        
        return is_in_dictionaries

    def _sanitize_relative_path(self, path, base_dir):
        """Sanitiza y valida un path relativo contra un directorio base.
        
        Rechaza:
        - Paths absolutos (empiezan con /)
        - Path traversal (.., '.. ', etc.)
        - Segmentos vacíos
        - Caracteres peligrosos
        - Paths que escapan del directorio base
        
        Args:
            path: Path relativo a validar
            base_dir: Directorio base (absoluto) contra el que validar
        
        Returns: path sanitizado y normalizado
        Raises: ValueError si el path es inválido
        """
        if not path or not isinstance(path, str):
            raise ValueError("Path vacío o inválido")
        
        # Rechazar paths absolutos
        if path.startswith('/') or path.startswith('\\'):
            raise ValueError("Paths absolutos no permitidos")
        
        # Separar en segmentos y validar cada uno
        segments = path.split('/')
        
        # Validar cada segmento
        for segment in segments:
            # Rechazar segmentos vacíos
            if not segment or segment.isspace():
                raise ValueError("Path con segmentos vacíos")
            
            # Rechazar percent-encoding (e.g., %2f, %2e)
            if '%' in segment:
                raise ValueError("Percent-encoding no permitido en paths")
            
            # Normalizar el segmento (eliminar espacios)
            normalized = segment.strip()
            
            # Rechazar segmentos que resuelven a . o ..
            if normalized in ('.', '..'):
                raise ValueError("Path traversal (. o ..) no permitido")
            
            # Rechazar caracteres peligrosos en segmentos
            dangerous_chars = set('<>:"|?*\\')
            if any(c in dangerous_chars for c in segment):
                raise ValueError(f"Caracteres no permitidos en path: {segment}")
        
        # Normalizar el path completo
        normalized_path = os.path.normpath(path)
        
        # Verificar que el path normalizado no empiece con ..
        if normalized_path.startswith('..') or normalized_path.startswith('.'):
            raise ValueError("Path intenta escapar del directorio base")
        
        # Verificar que no haya \ (Windows)
        if '\\' in normalized_path:
            raise ValueError("Separadores de Windows (\\) no permitidos")
        
        # Verificar resolución final contra base directory
        final_path = os.path.abspath(os.path.join(base_dir, normalized_path))
        
        # Usar os.path.commonpath para verificar contención estricta
        try:
            common = os.path.commonpath([base_dir, final_path])
            if common != base_dir:
                raise ValueError(f"Path intenta escapar del directorio base")
        except ValueError:
            # commonpath lanza ValueError si los paths están en diferentes drives (Windows)
            raise ValueError(f"Path intenta escapar del directorio base")
        
        # Retornar el path NORMALIZADO (crítico para seguridad)
        return normalized_path

    def _sanitize_code_path(self, path, allow_extension=False):
        """Sanitiza y valida un path para CODE/IMPORT/RMCODE.
        
        Wrapper específico que valida contra extended-code/
        
        Args:
            path: Path a sanitizar (formato: carpeta/nombre)
            allow_extension: Si True, permite extensiones .fth (para SAVE/LOAD compatibility)
        
        Returns: path sanitizado relativo a extended-code/
        """
        base_dir = os.path.abspath(os.path.join(self._base_dir, 'extended-code'))
        
        # Si allow_extension, permitir que pase .fth pero no es el caso típico de CODE
        try:
            return self._sanitize_relative_path(path, base_dir)
        except ValueError:
            # Re-raise con contexto específico de CODE
            return None

    def _sanitize_save_path(self, path):
        """Sanitiza y valida un path para SAVE/LOAD.
        
        Wrapper específico que valida contra el directorio actual y requiere extensión .fth
        
        Args:
            path: Path a sanitizar (formato: carpeta/nombre.fth)
        
        Returns: path sanitizado relativo al directorio actual
        Raises: ValueError si el path es inválido
        """
        # Validar que termine en .fth
        if not path.endswith('.fth'):
            raise ValueError("Archivo SAVE/LOAD debe terminar en .fth")
        
        base_dir = os.path.abspath(os.getcwd())
        
        # _sanitize_relative_path puede lanzar ValueError
        return self._sanitize_relative_path(path, base_dir)

    def _create_code_word(self, full_name, code_text):
        """Crea una palabra CODE y la persiste en extended-code/"""
        try:
            # Sanitizar el path
            try:
                sanitized_path = self._sanitize_code_path(full_name)
            except ValueError as e:
                print(f"Error: path inválido '{full_name}': {e}")
                return
            
            # Separar path completo y nombre de la palabra
            # Soporta paths anidados: sensors/temp/read → palabra "read"
            parts = sanitized_path.split('/')
            word_name = parts[-1]  # Última parte es el nombre de la palabra
            relative_path = '/'.join(parts[:-1])  # Resto es el path relativo
            
            # Verificar que no sea palabra del sistema
            if self._is_system_word(word_name):
                print(f"Error: '{word_name}' es palabra del sistema")
                return
            
            # Crear helpers para el código Python
            def push(val):
                self.stack.append(val)
            
            def pop():
                if not self.stack:
                    raise IndexError("Stack underflow")
                return self.stack.pop()
            
            def peek():
                if not self.stack:
                    raise IndexError("Stack empty")
                return self.stack[-1]
            
            # Preparar el namespace con helpers
            local_namespace = {
                'self': self,
                'push': push,
                'pop': pop,
                'peek': peek,
                'math': math,
            }
            
            # Compilar el código Python
            try:
                compiled_code = compile(code_text, f'<CODE {full_name}>', 'exec')
            except SyntaxError as e:
                print(f"Error de sintaxis en código Python para '{full_name}':")
                print(f"  {e}")
                return
            
            # Crear función wrapper
            def code_word_wrapper():
                try:
                    exec(compiled_code, local_namespace)
                except Exception as e:
                    print(f"Error ejecutando '{word_name}': {e}")
            
            # Registrar la palabra
            self.words[word_name] = code_word_wrapper
            self._definition_order.append(('code', word_name))
            self._definition_source[word_name] = f"CODE {full_name}\n{code_text}\nENDCODE"
            self._last_defined_word = word_name
            
            # Persistir en archivo
            self._save_code_word(relative_path, word_name, code_text, full_name)
            
            print(f"✓ Palabra CODE '{word_name}' creada y guardada en extended-code/{full_name}.py")
            
        except Exception as e:
            print(f"Error creando palabra CODE: {e}")
    
    def _save_code_word(self, relative_path, word_name, code_text, full_name):
        """Guarda la palabra CODE en extended-code/relative_path/nombre.py"""
        try:
            # Crear directorio extended-code/ si no existe
            base_dir = os.path.join(self._base_dir, 'extended-code')
            os.makedirs(base_dir, exist_ok=True)
            
            # Crear directorio del path relativo si no existe (puede ser anidado)
            path_dir = os.path.join(base_dir, relative_path)
            os.makedirs(path_dir, exist_ok=True)
            
            # Generar el archivo Python
            file_path = os.path.join(path_dir, f"{word_name}.py")
            
            # Formatear el código original Forth como comentarios
            forth_source_lines = code_text.split('\n')
            forth_comments = '\n'.join(f'# {line}' for line in forth_source_lines)
            
            # Plantilla del archivo
            file_content = f'''# FORTH CODE WORD: {full_name}
# Auto-generated by CODE/ENDCODE
# Original Forth name: {word_name}
#
# === CÓDIGO FORTH ORIGINAL ===
{forth_comments}
# === FIN CÓDIGO FORTH ===

def execute(forth):
    """
    Ejecuta la palabra CODE '{word_name}'
    Tiene acceso a helpers: push(), pop(), peek()
    """
    # Helpers
    def push(val):
        forth.stack.append(val)
    
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    
    def peek():
        if not forth.stack:
            raise IndexError("Stack empty")
        return forth.stack[-1]
    
    # Código del usuario
{chr(10).join("    " + line for line in code_text.split(chr(10)))}
'''
            
            with open(file_path, 'w') as f:
                f.write(file_content)
            
        except Exception as e:
            print(f"Advertencia: no se pudo guardar archivo: {e}")

    # Implementación de forget
    def _forget(self):
        if not self.stack:
            print("Error: nombre faltante para forget")
            return

        target_name = self.stack.pop()

        if self._is_system_word(target_name):
            print(f"Error: '{target_name}' es una palabra del sistema y no puede ser olvidada")
            return

        target_index = None
        for i, (def_type, name) in enumerate(self._definition_order):
            if name == target_name:
                target_index = i
                break

        if target_index is None:
            print(f"Error: '{target_name}' no encontrada en definiciones de usuario")
            return

        definitions_to_remove = self._definition_order[target_index:]

        for def_type, name in definitions_to_remove:
            self._remove_definition(def_type, name)

        self._definition_order = self._definition_order[:target_index]

        print(f"Olvidadas {len(definitions_to_remove)} definiciones desde '{target_name}'")

    def _remove_definition(self, def_type, name):
        if def_type == 'word':
            if name in self.words:
                del self.words[name]
            if name in self.immediate_words:
                del self.immediate_words[name]
            print(f"  - Palabra: {name}")

        elif def_type == 'immediate':
            if name in self.immediate_words:
                del self.immediate_words[name]
            print(f"  - Palabra inmediata: {name}")

        elif def_type == 'variable':
            if name in self.variables:
                del self.variables[name]
            if name in self.words:
                del self.words[name]
            print(f"  - Variable: {name}")

        elif def_type == 'constant':
            if name in self.constants:
                del self.constants[name]
            if name in self.words:
                del self.words[name]
            print(f"  - Constante: {name}")

        elif def_type == 'value':
            if name in self.values:
                del self.values[name]
            if name in self.words:
                del self.words[name]
            print(f"  - Value: {name}")

        elif def_type == 'created': # Para palabras definidas con CREATE
            if name in self.words:
                del self.words[name]
            print(f"  - Palabra CREATE: {name}")
        
        elif def_type == 'code': # Para palabras CODE
            if name in self.words:
                del self.words[name]
            print(f"  - Palabra CODE: {name}")

    def show_definitions(self):
        print("=== REGISTRO DE DEFINICIONES ===")
        for i, (def_type, name) in enumerate(self._definition_order):
            print(f"{i:3d}. {def_type:10} {name}")
        return self

    def _list_words(self):
        """Muestra palabras de forma compacta"""
        # Separar palabras del sistema de palabras de usuario
        system_words = []
        user_words = []
        for w in self.words.keys():
            if not w.startswith('_'):
                if self._is_system_word(w):
                    system_words.append(w)
                else:
                    user_words.append(w)

        system_words = sorted(system_words)
        # Palabras de usuario en orden de definición
        user_words_ordered = [name for (def_type, name) in self._definition_order if name in self.words]

        immediate_words = sorted(self.immediate_words.keys())
        variables = sorted(self.variables.keys())
        constants = sorted(self.constants.keys())
        values = sorted(self.values.keys())

        if system_words:
            print("Palabras:", " ".join(system_words))
        if user_words_ordered:
            print("Usuario:", " ".join(user_words_ordered))
        if immediate_words:
            print("Inmediatas:", " ".join(immediate_words))
        if variables:
            print("Variables:", " ".join(variables))
        if constants:
            print("Constantes:", " ".join(constants))
        if values:
            print("Values:", " ".join(values))
        return self

    def _list_immediate_words(self):
        print("Palabras inmediatas:", list(self.immediate_words.keys()))
        return self

    def _see(self):
        """Stub para SEE - el trabajo real se hace en execute() o llamando _see_word"""
        if not self.stack:
            print("Error: nombre de palabra faltante para see")
            return
        word_name = self.stack.pop()
        self._see_word(word_name)
        return self

    def _measure(self):
        """Stub para MEASURE - el trabajo real se hace en execute() que captura el siguiente token"""
        print("Error: MEASURE requiere el nombre de una palabra")
        print("Uso: measure nombre-palabra")
        return self

    def _code_stub(self):
        """Stub para CODE - el trabajo real se hace en execute()"""
        print("Error: CODE requiere un nombre en formato grupo/nombre")
        print("Uso: CODE grupo/nombre")
        return self

    def _endcode_stub(self):
        """Stub para ENDCODE - el trabajo real se hace en execute()"""
        print("Error: ENDCODE sin CODE previo")
        return self

    def _import_stub(self):
        """Stub para IMPORT - el trabajo real se hace en execute()"""
        print("Error: IMPORT requiere un nombre en formato grupo/nombre")
        print("Uso: import grupo/nombre")
        return self

    def _seecode_stub(self):
        """Stub para SEECODE - el trabajo real se hace en execute()"""
        print("Error: SEECODE requiere un nombre en formato grupo/nombre")
        print("Uso: seecode grupo/nombre")
        return self

    def _lscode(self):
        """Lista todas las palabras CODE disponibles en extended-code/"""
        import os
        
        base_dir = os.path.join(self._base_dir, 'extended-code')
        
        if not os.path.exists(base_dir):
            print("No hay palabras CODE guardadas (carpeta extended-code/ no existe)")
            return self
        
        print("\n=== Palabras CODE Disponibles ===\n")
        
        # Recopilar todos los archivos .py organizados por grupo
        groups = {}
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.py'):
                    # Obtener el grupo (nombre de la carpeta)
                    group = os.path.relpath(root, base_dir)
                    if group == '.':
                        group = '(raíz)'
                    
                    # Obtener el nombre de la palabra (sin .py)
                    word_name = file[:-3]
                    
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(word_name)
        
        if not groups:
            print("No hay palabras CODE guardadas")
            return self
        
        # Mostrar organizados por grupo
        for group in sorted(groups.keys()):
            print(f"📁 {group}/")
            for word in sorted(groups[group]):
                # Verificar si ya está cargada en cualquier diccionario
                is_loaded = (word in self.words or 
                            word in self.immediate_words or 
                            word in self.variables or 
                            word in self.constants or 
                            word in self.values)
                status = "✓" if is_loaded else "○"
                print(f"   {status} {word}")
            print()
        
        print("Leyenda: ✓ = cargada  ○ = no cargada")
        print("Uso: import grupo/nombre")
        print()
        
        return self

    def _vlist(self):
        """Lista todas las carpetas/vocabularios disponibles en extended-code/"""
        import os
        
        base_dir = os.path.join(self._base_dir, 'extended-code')
        
        if not os.path.exists(base_dir):
            print("No hay vocabularios (carpeta extended-code/ no existe)")
            return self
        
        print("\n=== Vocabularios Disponibles ===\n")
        
        # Recopilar todos los directorios
        vocabularies = set()
        for root, dirs, files in os.walk(base_dir):
            # Solo agregar si tiene archivos .py (ignorar carpetas vacías o solo con __pycache__)
            has_code = any(f.endswith('.py') for f in files)
            if has_code:
                vocab = os.path.relpath(root, base_dir)
                if vocab != '.':
                    vocabularies.add(vocab)
        
        if not vocabularies:
            print("No hay vocabularios con palabras CODE")
            return self
        
        # Mostrar vocabularios ordenados
        for vocab in sorted(vocabularies):
            print(f"📁 {vocab}/")
        
        print(f"\nTotal: {len(vocabularies)} vocabulario(s)")
        print("Uso: lscode para ver palabras en cada vocabulario")
        print()
        
        return self

    def _lssave(self):
        """Lista todos los archivos .fth guardados, organizados por carpeta"""
        import os
        import time
        from collections import defaultdict
        
        print("\n=== Archivos SAVE Disponibles ===\n")
        
        current_dir = os.getcwd()
        
        # Diccionario para organizar archivos por carpeta
        files_by_folder = defaultdict(list)
        total_files = 0
        
        try:
            # Buscar recursivamente todos los archivos .fth
            for root, dirs, files in os.walk(current_dir):
                for file in files:
                    if file.endswith('.fth'):
                        file_path = os.path.join(root, file)
                        # Calcular ruta relativa
                        rel_path = os.path.relpath(file_path, current_dir)
                        folder = os.path.dirname(rel_path)
                        if not folder:
                            folder = "."  # Raíz
                        
                        # Obtener información del archivo
                        stat_info = os.stat(file_path)
                        size = stat_info.st_size
                        mtime = stat_info.st_mtime
                        
                        files_by_folder[folder].append((file, rel_path, size, mtime))
                        total_files += 1
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            return self
        
        if total_files == 0:
            print("No hay archivos .fth guardados")
            print(f"Directorio actual: {current_dir}")
            print("\nUso: s\" nombre.fth\" save          → Guardar en raíz")
            print("     s\" carpeta/nombre.fth\" save → Guardar en carpeta")
            print()
            return self
        
        # Ordenar carpetas (raíz primero, luego alfabéticamente)
        sorted_folders = sorted(files_by_folder.keys(), key=lambda x: (x != ".", x))
        
        # Mostrar archivos organizados por carpeta
        for folder in sorted_folders:
            if folder == ".":
                # Archivos en la raíz, sin encabezado de carpeta
                pass
            else:
                print(f"📁 {folder}/")
            
            # Ordenar archivos por fecha de modificación (más reciente primero)
            files_in_folder = sorted(files_by_folder[folder], key=lambda x: x[3], reverse=True)
            
            for filename, rel_path, size, mtime in files_in_folder:
                # Formatear tamaño
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                
                # Formatear fecha
                mod_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime))
                
                # Mostrar con indentación si está en carpeta
                indent = "   " if folder != "." else ""
                print(f"{indent}📄 {filename:<25} {size_str:>8}  {mod_time}")
            
            if folder != ".":
                print()  # Línea en blanco entre carpetas
        
        print(f"Total: {total_files} archivo(s)")
        print("\nUso: s\" nombre.fth\" load          → Cargar desde raíz")
        print("     s\" carpeta/nombre.fth\" load → Cargar desde carpeta")
        print()
        
        return self

    def _rmcode_stub(self):
        """Stub para RMCODE - el trabajo real se hace en execute()"""
        print("Error: RMCODE requiere un nombre en formato grupo/nombre")
        print("Uso: rmcode grupo/nombre")
        return self

    def _format_time(self, seconds):
        """Formatea automáticamente el tiempo en unidades apropiadas (s, ms, μs, ns)
        Retorna una tupla (string_formateado, valor_numérico)
        """
        if seconds >= 1.0:
            # Segundos
            return (f"{seconds:.6f} s", seconds)
        elif seconds >= 0.001:
            # Milisegundos
            ms = seconds * 1000
            return (f"{ms:.3f} ms", ms)
        elif seconds >= 0.000001:
            # Microsegundos
            us = seconds * 1_000_000
            return (f"{us:.3f} μs", us)
        else:
            # Nanosegundos
            ns = seconds * 1_000_000_000
            return (f"{ns:.1f} ns", ns)

    def _see_word(self, word_name):
        """Muestra la definición de una palabra"""
        print(f"\n--- SEE {word_name} ---")

        # Verificar si la palabra existe
        if word_name not in self.words and word_name not in self.immediate_words and \
           word_name not in self.variables and word_name not in self.constants and \
           word_name not in self.values:
            print(f"Error: '{word_name}' no está definida")
            return

        # 1. Mostrar código fuente si está disponible
        if word_name in self._definition_source:
            print(f"Código fuente:")
            print(f"  {self._definition_source[word_name]}")
            print()

        # 2. Identificar el tipo de palabra
        word_type = []

        if word_name in self.immediate_words:
            word_type.append("INMEDIATA")

        if word_name in self.variables:
            # Mostrar valor actual si es variable o value
            if word_name in self.values:
                 word_type.append(f"VALUE (actual: {self.values[word_name]})")
            else:
                 word_type.append(f"VARIABLE (valor actual: {self.variables[word_name]})")


        if word_name in self.constants:
            word_type.append(f"CONSTANTE (valor: {self.constants[word_name]})")

        # Verificar si es una palabra del sistema
        if self._is_system_word(word_name):
            word_type.append("PRIMITIVA (palabra del sistema)")

        # Verificar si es una palabra de usuario definida con :
        is_user_word = False
        for def_type, name in self._definition_order:
            if name == word_name and def_type == 'word':
                is_user_word = True
                word_type.append("DEFINICIÓN DE USUARIO")
                break

        # Verificar si es una palabra creada con CREATE
        is_created_word = False
        for def_type, name in self._definition_order:
            if name == word_name and def_type == 'created':
                is_created_word = True
                word_type.append(f"PALABRA CREATE (dir: {self._last_created_address})") # Dirección puede no ser la correcta si hay forgets
                break

        if word_type:
            print(f"Tipo: {' + '.join(word_type)}")

        # 3. Para palabras compiladas, mostrar la representación interna si no hay fuente
        if is_user_word and word_name not in self._definition_source:
            if word_name in self.words:
                # Intentar obtener información de la definición compilada
                word_func = self.words[word_name]
                if hasattr(word_func, '__closure__') and word_func.__closure__:
                    print("Definición compilada (sin código fuente disponible)")
                    print("Sugerencia: usa SAVE para guardar y preservar el código fuente")

        # 4. Mostrar información adicional para CREATE words
        # (Ya se incluyó en word_type)

        print()
        return self

    def _type(self):
        if self.stack:
            string = self.stack.pop()
            print(string, end='')
            sys.stdout.flush()

    def _evaluate(self):
        """EVALUATE ( addr len -- ) o ( string -- )
        Ejecuta el texto en addr/len como código Forth.
        También acepta un string directamente de s"
        """
        if len(self.stack) < 1:
            print("Error: EVALUATE requiere al menos un valor en la pila")
            return

        code_string = None

        # Caso 1: Solo un string en el tope (de s")
        if isinstance(self.stack[-1], str):
            code_string = self.stack.pop()

        # Caso 2: addr len (dos valores numéricos)
        elif len(self.stack) >= 2:
            # Stack effect: ( addr len -- )
            try:
                length = int(self.stack.pop())
                address = int(self.stack.pop())
            except (ValueError, TypeError):
                print("Error: EVALUATE requiere (addr len) como números o un string")
                return

            # Validar rango de memoria
            if address < 0 or address >= self._memory_size:
                print(f"Error: dirección {address} fuera de rango (0-{self._memory_size-1})")
                return

            if length < 0:
                print(f"Error: longitud {length} debe ser >= 0")
                return

            # Leer string de memoria
            try:
                code_string = self._load_string(address, length)
            except Exception as e:
                print(f"Error leyendo de memoria: {e}")
                return
        else:
            print("Error: EVALUATE requiere un string o (addr len)")
            return

        # Ejecutar el código
        if code_string:
            try:
                self.execute(code_string)
            except Exception as e:
                print(f"Error en EVALUATE: {e}")

    # Variables y memoria
    def _create_variable(self, name):
        self.variables[name] = 0

        def push_variable_address():
            self.stack.append(name)

        self.words[name] = push_variable_address
        self._definition_order.append(('variable', name))
        # No imprimir nada por defecto para creación interna
        #print(f"Variable '{name}' creada")

    def _create_constant(self, name, value):
        self.constants[name] = value

        def push_constant_value():
            self.stack.append(value)

        self.words[name] = push_constant_value
        self._definition_order.append(('constant', name))
        #print(f"Constante '{name}' = {value} creada")

    def _create_value(self, name, initial_value):
        self.values[name] = initial_value

        def push_current_value():
            self.stack.append(self.values[name])

        self.words[name] = push_current_value
        self._definition_order.append(('value', name))
        #print(f"Value '{name}' = {initial_value} creado")

    def _set_value(self, name, new_value):
        if name in self.values:
            self.values[name] = new_value
            #print(f"Value '{name}' actualizado a {new_value}")
        else:
            print(f"Error: value '{name}' no definido")

    def _fetch(self):
        if len(self.stack) >= 1:
            address_or_name = self.stack.pop()
            if isinstance(address_or_name, str):
                if address_or_name in self.variables:
                    self.stack.append(self.variables[address_or_name])
                    return
                elif address_or_name in self.values:
                    self.stack.append(self.values[address_or_name])
                    return
            
            # No es variable/value, intentar como dirección de memoria
            if True:
                # Asumir que es una dirección de memoria
                try:
                    address = int(address_or_name)
                    if address in range(self._memory_size):
                        self.stack.append(self.memory[address])
                    else:
                        print(f"Error: dirección {address} fuera de rango")
                        self.stack.append(address_or_name)
                except (ValueError, TypeError):
                    print(f"Error: '{address_or_name}' no es una variable, value o dirección válida")
                    self.stack.append(address_or_name)


    def _store(self):
        if len(self.stack) >= 2:
            address_or_name = self.stack.pop()
            value = self.stack.pop()
            if isinstance(address_or_name, str):
                if address_or_name in self.variables:
                    self.variables[address_or_name] = value
                    return
                elif address_or_name in self.values:
                    self.values[address_or_name] = value
                    return
            
            # No es variable/value, intentar como dirección de memoria
            if True:
                 # Asumir que es una dirección de memoria
                try:
                    address = int(address_or_name)
                    if address in range(self._memory_size):
                        self.memory[address] = value
                    else:
                        print(f"Error: dirección {address} fuera de rango")
                        self.stack.extend([value, address_or_name])
                except (ValueError, TypeError):
                    print(f"Error: '{address_or_name}' no es una variable, value o dirección válida")
                    self.stack.extend([value, address_or_name])

    # Memoria dinámica
    def _here(self):
        self.stack.append(self.here)

    def _allot(self):
        if len(self.stack) < 1:
            print("Error: faltan parámetros para allot")
            return

        n = self.stack.pop()

        try:
            n = int(n)
        except (ValueError, TypeError):
            print(f"Error: ALLOT requiere un número, recibió {type(n)}")
            self.stack.append(n)
            return

        new_here = self.here + n

        if new_here < 0:
            print("Error: dirección de memoria negativa")
            self.stack.append(n)
            return

        if new_here >= self._memory_size:
            print(f"Error: memoria insuficiente (solicitado: {n}, disponible: {self._memory_size - self.here})")
            self.stack.append(n)
            return

        self.here = new_here
        #print(f"Memoria reservada: {n} bytes, here ahora en: {self.here}")

    def _buffer(self):
        """( len -- len addr ) Reserva buffer de len bytes y retorna dirección
        Duplica len, obtiene here, reserva espacio con allot
        Útil para: s" texto" buffer swap move
        """
        if len(self.stack) < 1:
            print("Error: buffer requiere un parámetro (len)")
            return

        length = self.stack[-1]  # Peek, no pop (queremos mantener len en pila)

        if not isinstance(length, (int, float)):
            print(f"Error: buffer requiere un número, recibió {type(length)}")
            return

        length = int(length)

        if length < 0:
            print("Error: longitud de buffer no puede ser negativa")
            return

        new_here = self.here + length

        if new_here > self._memory_size:
            print(f"Error: memoria insuficiente (solicitado: {length}, disponible: {self._memory_size - self.here})")
            return

        # Guardar dirección del buffer (before allot)
        buffer_addr = self.here

        # Reservar espacio
        self.here = new_here

        # Poner dirección en pila (len ya está ahí)
        self.stack.append(buffer_addr)

    def _s_to_mem(self):
        """( string -- addr len ) Copia string a memoria y retorna dirección y longitud
        Útil para: s" código" s>mem evaluate
        """
        if len(self.stack) < 1:
            print("Error: s>mem requiere un string en la pila")
            return

        string = self.stack.pop()

        if not isinstance(string, str):
            print(f"Error: s>mem requiere un string, recibió {type(string)}")
            self.stack.append(string)
            return

        length = len(string)

        if length == 0:
            # String vacío, retornar here y 0
            self.stack.extend([self.here, 0])
            return

        new_here = self.here + length

        if new_here > self._memory_size:
            print(f"Error: memoria insuficiente (string: {length} bytes, disponible: {self._memory_size - self.here})")
            self.stack.append(string)
            return

        # Guardar dirección del buffer
        buffer_addr = self.here

        # Copiar string a memoria
        for i, char in enumerate(string):
            self.memory[self.here + i] = ord(char)

        # Avanzar here
        self.here = new_here

        # Retornar addr y len en la pila
        self.stack.extend([buffer_addr, length])

    def _parse(self):
        r"""( char "ccc<char>" -- addr len ) Lee texto hasta encontrar delimitador
        
        Lee del código fuente actual hasta encontrar el carácter delimitador.
        Copia el texto a memoria y retorna dirección y longitud (sin incluir delimitador).
        
        IMPORTANTE: PARSE trabaja con el código fuente sin tokenizar. Debe ser la
        última palabra antes del texto a parsear en cada línea de ejecución.
        
        El texto parseado incluye espacios y caracteres especiales tal como aparecen
        en el código original, permitiendo procesar texto con formato complejo.
        
        Ejemplos:
          char ) parse texto hasta paréntesis)   \ addr len de "texto hasta paréntesis"
          bl parse palabra resto                \ addr len de "palabra"
          10 parse línea\nmás                  \ addr len hasta newline
          
        Para usar el texto parseado:
          char ! parse Hola Mundo! fin  type    \ imprime "Hola Mundo"
          
        Para entrada multi-línea use múltiples execute() o s":
          s" línea 1
          línea 2
          línea 3" s>mem evaluate
        """
        if len(self.stack) < 1:
            print("Error: parse requiere un delimitador en la pila")
            return

        delimiter_code = self.stack.pop()
        
        # Convertir a entero si es necesario
        try:
            delimiter_code = int(delimiter_code)
        except (ValueError, TypeError):
            print(f"Error: parse requiere un código ASCII, recibió {type(delimiter_code)}")
            return
        
        # Convertir código ASCII a carácter
        try:
            delimiter = chr(delimiter_code)
        except ValueError:
            print(f"Error: código ASCII inválido: {delimiter_code}")
            return

        # Verificar que tenemos código original disponible
        if not hasattr(self, '_input_code'):
            # No hay código, retornar string vacío
            self.stack.extend([self.here, 0])
            return

        # Encontrar dónde estamos en el código original
        # Necesitamos buscar después de la palabra "parse" en el código
        code = self._input_code
        
        # Buscar "parse" desde el inicio
        parse_pos = code.find('parse')
        if parse_pos == -1:
            # No encontramos parse, usar todo el código restante
            start_pos = 0
        else:
            # Empezar después de "parse" y saltar espacios
            start_pos = parse_pos + len('parse')
            while start_pos < len(code) and code[start_pos].isspace():
                start_pos += 1

        # Buscar el delimitador desde la posición actual
        text_to_search = code[start_pos:]
        delimiter_pos = text_to_search.find(delimiter)
        
        if delimiter_pos == -1:
            # Delimitador no encontrado, tomar todo el texto restante
            parsed_text = text_to_search
        else:
            # Delimitador encontrado, tomar hasta ahí (sin incluirlo)
            parsed_text = text_to_search[:delimiter_pos]
        
        # Marcar que consumimos todo el input restante (evita procesamiento de tokens)
        self._skip_remaining_tokens = True

        # Si el texto está vacío, retornar aquí con longitud 0
        length = len(parsed_text)
        if length == 0:
            self.stack.extend([self.here, 0])
            return

        # Verificar espacio en memoria
        new_here = self.here + length
        if new_here > self._memory_size:
            print(f"Error: memoria insuficiente (texto: {length} bytes, disponible: {self._memory_size - self.here})")
            self.stack.append(delimiter_code)
            return

        # Guardar dirección donde comienza el texto
        buffer_addr = self.here

        # Copiar texto a memoria
        for i, char in enumerate(parsed_text):
            self.memory[self.here + i] = ord(char)

        # Avanzar here
        self.here = new_here

        # Retornar addr y len
        self.stack.extend([buffer_addr, length])

    def _comma(self):
        if len(self.stack) < 1:
            print("Error: faltan parámetros para ,")
            return

        value = self.stack.pop()

        if self.here >= self._memory_size:
            print("Error: memoria llena")
            self.stack.append(value)
            return

        self.memory[self.here] = value
        #print(f"Almacenado {value} en dirección {self.here}")
        self.here += 1

    def _m_fetch(self):
        if len(self.stack) < 1:
            print("Error: faltan parámetros para m@")
            return

        address = self.stack.pop()

        try:
            address = int(address)
        except (ValueError, TypeError):
            print(f"Error: m@ requiere una dirección numérica, recibió {type(address)}")
            self.stack.append(address)
            return

        if address < 0 or address >= self._memory_size:
            print(f"Error: dirección de memoria inválida: {address}")
            self.stack.append(address)
            return

        self.stack.append(self.memory[address])

    def _m_store(self):
        if len(self.stack) < 2:
            print("Error: faltan parámetros para m!")
            return

        address = self.stack.pop()
        value = self.stack.pop()

        try:
            address = int(address)
        except (ValueError, TypeError):
            print(f"Error: m! requiere una dirección numérica, recibió {type(address)}")
            self.stack.extend([value, address])
            return

        if address < 0 or address >= self._memory_size:
            print(f"Error: dirección de memoria inválida: {address}")
            self.stack.extend([value, address])
            return

        self.memory[address] = value
        #print(f"Almacenado {value} en dirección {address}")

    def _dump(self):
        # Buscar el último dato no-cero en memoria
        max_used = self.here
        for addr in range(self._memory_size - 1, -1, -1):
            if self.memory[addr] != 0:
                max_used = max(max_used, addr + 1)
                break

        # Si no hay datos, mostrar hasta here
        if max_used == 0:
            max_used = max(self.here, 16)

        print(f"\n=== VOLCADO DE MEMORIA (0-{min(max_used + 16, self._memory_size)}) ===")
        print(f"Here: {self.here}, Datos hasta: {max_used}, Total: {self._memory_size} bytes ({self._memory_size//1024}KB)")
        print("-" * 78)

        end_address = min(max_used + 16, self._memory_size)
        lines_to_show = (end_address + 15) // 16

        for i in range(0, min(lines_to_show * 16, self._memory_size), 16):
            if i >= end_address:
                break

            addr_str = f"{i:05d}:"
            hex_bytes = []
            ascii_chars = []

            for j in range(16):
                if i + j < self._memory_size:
                    val = self.memory[i + j]
                    if isinstance(val, int):
                        byte_val = val & 0xFF
                        hex_bytes.append(f"{byte_val:02x}")
                        if 32 <= byte_val <= 126:
                            ascii_chars.append(chr(byte_val))
                        else:
                            ascii_chars.append(".")
                    else: # Manejar objetos no-enteros en memoria si se diera el caso
                        hex_bytes.append("??")
                        ascii_chars.append("?")
                else:
                    hex_bytes.append("  ")
                    ascii_chars.append(" ")

            hex_line = " ".join(hex_bytes[:8]) + "  " + " ".join(hex_bytes[8:])
            ascii_line = "".join(ascii_chars)

            # Mostrar línea si tiene algún dato
            if any(b != "  " for b in hex_bytes):
                print(f"{addr_str} {hex_line}  |{ascii_line}|")

        if self._memory_size - max_used > 1024:
            free_kb = (self._memory_size - max_used) // 1024
            print(f"... ~{free_kb}KB libres ...")

    def _cells(self):
        if self.stack:
            self.stack.append(self.stack.pop() * 4)

    # Nuevas operaciones de memoria útiles
    def _plus_store(self):
        """( n addr -- ) Añade n al valor en addr (funciona con variables y memoria)"""
        if len(self.stack) < 2:
            print("Error: +! requiere 2 parámetros (n addr)")
            return

        address_or_name = self.stack.pop()
        n = self.stack.pop()

        # Caso 1: Es una variable (address_or_name es string)
        if address_or_name in self.variables:
            current = self.variables[address_or_name]
            if isinstance(current, (int, float)):
                self.variables[address_or_name] = current + n
            else:
                print(f"Error: +! solo funciona con números, encontró {type(current)}")
                self.stack.extend([n, address_or_name])
        # Caso 3: Es un value
        elif address_or_name in self.values:
            current = self.values[address_or_name]
            if isinstance(current, (int, float)):
                self.values[address_or_name] = current + n
            else:
                print(f"Error: +! solo funciona con números, encontró {type(current)}")
                self.stack.extend([n, address_or_name])
        # Caso 2: Es una dirección de memoria (address es int)
        elif isinstance(address_or_name, int):
            address = address_or_name
            if address < 0 or address >= self._memory_size:
                print(f"Error: dirección de memoria inválida: {address}")
                self.stack.extend([n, address])
                return

            current = self.memory[address]
            if isinstance(current, (int, float)):
                self.memory[address] = current + n
            else:
                print(f"Error: +! solo funciona con números en memoria, encontró {type(current)}")
                self.stack.extend([n, address])
        else:
            print(f"Error: '{address_or_name}' no es una variable, value o dirección válida")
            self.stack.extend([n, address_or_name])

    def _question(self):
        """( addr -- ) Imprime el valor en addr (funciona con variables y memoria)"""
        if len(self.stack) < 1:
            print("Error: ? requiere una dirección")
            return

        address_or_name = self.stack.pop()

        # Caso 1: Es una variable (address_or_name es string)
        if address_or_name in self.variables:
            print(self.variables[address_or_name])
        # Caso 2: Es un value
        elif address_or_name in self.values:
            print(self.values[address_or_name])
        # Caso 3: Es una dirección de memoria (address es int)
        elif isinstance(address_or_name, int):
            address = address_or_name
            if address < 0 or address >= self._memory_size:
                print(f"Error: dirección de memoria inválida: {address}")
                return
            print(self.memory[address])
        else:
            print(f"Error: '{address_or_name}' no es una variable, value o dirección válida")

    def _fill(self):
        """( addr u char -- ) Llena u bytes con char"""
        if len(self.stack) < 3:
            print("Error: fill requiere 3 parámetros (addr u char)")
            return

        char = self.stack.pop()
        u = self.stack.pop()
        addr = self.stack.pop()

        try:
            char = int(char) & 0xFF
            u = int(u)
            addr = int(addr)
        except (ValueError, TypeError):
            print("Error: FILL requiere números para addr, u, y char")
            self.stack.extend([addr, u, char])
            return

        if addr < 0 or addr + u > self._memory_size:
            print(f"Error: rango de memoria inválido: {addr} + {u}")
            self.stack.extend([addr, u, char])
            return

        for i in range(u):
            self.memory[addr + i] = char

    def _erase(self):
        """( addr u -- ) Borra u bytes (pone a 0)"""
        if len(self.stack) < 2:
            print("Error: erase requiere 2 parámetros (addr u)")
            return

        u = self.stack.pop()
        addr = self.stack.pop()

        try:
            u = int(u)
            addr = int(addr)
        except (ValueError, TypeError):
            print("Error: ERASE requiere números para addr y u")
            self.stack.extend([addr, u])
            return

        if addr < 0 or addr + u > self._memory_size:
            print(f"Error: rango de memoria inválido: {addr} + {u}")
            self.stack.extend([addr, u])
            return

        for i in range(u):
            self.memory[addr + i] = 0

    def _move(self):
        """( addr1 addr2 u -- ) Copia u bytes desde addr1 a addr2
        Detecta automáticamente la dirección correcta para evitar problemas con overlapping
        """
        if len(self.stack) < 3:
            print("Error: MOVE requiere 3 parámetros (addr1 addr2 u)")
            return

        u = int(self.stack.pop())
        addr2 = int(self.stack.pop())
        addr1 = int(self.stack.pop())

        # Validar rangos
        if addr1 < 0 or addr1 + u > self._memory_size:
            print(f"Error: rango origen inválido: {addr1} + {u}")
            self.stack.extend([addr1, addr2, u])
            return

        if addr2 < 0 or addr2 + u > self._memory_size:
            print(f"Error: rango destino inválido: {addr2} + {u}")
            self.stack.extend([addr1, addr2, u])
            return

        # Detectar dirección de copia para manejar overlapping
        if addr2 <= addr1:
            # Copiar hacia adelante (ascendente)
            for i in range(u):
                self.memory[addr2 + i] = self.memory[addr1 + i]
        else:
            # Copiar hacia atrás (descendente) para evitar sobrescribir
            for i in range(u - 1, -1, -1):
                self.memory[addr2 + i] = self.memory[addr1 + i]

    def _cmove(self):
        """( addr1 addr2 u -- ) Copia u bytes desde addr1 a addr2 de forma ascendente
        Seguro cuando addr2 > addr1 (destino después del origen)
        """
        if len(self.stack) < 3:
            print("Error: CMOVE requiere 3 parámetros (addr1 addr2 u)")
            return

        u = int(self.stack.pop())
        addr2 = int(self.stack.pop())
        addr1 = int(self.stack.pop())

        # Validar rangos
        if addr1 < 0 or addr1 + u > self._memory_size:
            print(f"Error: rango origen inválido: {addr1} + {u}")
            self.stack.extend([addr1, addr2, u])
            return

        if addr2 < 0 or addr2 + u > self._memory_size:
            print(f"Error: rango destino inválido: {addr2} + {u}")
            self.stack.extend([addr1, addr2, u])
            return

        # Copiar de forma ascendente (forward)
        for i in range(u):
            self.memory[addr2 + i] = self.memory[addr1 + i]

    def _cmove_up(self):
        """( addr1 addr2 u -- ) Copia u bytes desde addr1 a addr2 de forma descendente
        Seguro cuando addr2 < addr1 (destino antes del origen)
        Palabra: CMOVE> en Forth estándar
        """
        if len(self.stack) < 3:
            print("Error: CMOVE> requiere 3 parámetros (addr1 addr2 u)")
            return

        u = int(self.stack.pop())
        addr2 = int(self.stack.pop())
        addr1 = int(self.stack.pop())

        # Validar rangos
        if addr1 < 0 or addr1 + u > self._memory_size:
            print(f"Error: rango origen inválido: {addr1} + {u}")
            self.stack.extend([addr1, addr2, u])
            return

        if addr2 < 0 or addr2 + u > self._memory_size:
            print(f"Error: rango destino inválido: {addr2} + {u}")
            self.stack.extend([addr1, addr2, u])
            return

        # Copiar de forma descendente (backward)
        for i in range(u - 1, -1, -1):
            self.memory[addr2 + i] = self.memory[addr1 + i]

    def _cell_plus(self):
        """( addr -- addr+4 ) Avanza una celda (4 bytes)"""
        if len(self.stack) < 1:
            print("Error: cell+ requiere una dirección")
            return

        self.stack.append(self.stack.pop() + 4)

    # Operaciones de bytes
    def _c_fetch(self):
        if len(self.stack) < 1:
            print("Error: faltan parámetros para c@")
            return

        address_or_name = self.stack.pop()

        if address_or_name in self.variables:
            value = self.variables[address_or_name]
            byte_value = value & 0xFF
            self.stack.append(byte_value)
        else:
            try:
                address = int(address_or_name)
                if address in range(self._memory_size):
                    value = self.memory[address]
                    byte_value = value & 0xFF
                    self.stack.append(byte_value)
                else:
                    print(f"Error: dirección {address} fuera de rango")
                    self.stack.append(address_or_name)
            except (ValueError, TypeError):
                print(f"Error: '{address_or_name}' no es una variable o dirección válida")
                self.stack.append(address_or_name)


    def _c_store(self):
        if len(self.stack) < 2:
            print("Error: faltan parámetros para c!")
            return

        address_or_name = self.stack.pop()
        value = self.stack.pop()

        if address_or_name in self.variables:
            byte_value = int(value) & 0xFF
            self.variables[address_or_name] = byte_value
            #print(f"Almacenado byte {byte_value} en variable '{address_or_name}'")
        else:
            try:
                address = int(address_or_name)
                if address in range(self._memory_size):
                    byte_value = int(value) & 0xFF
                    self.memory[address] = byte_value
                    #print(f"Almacenado byte {byte_value} en dirección {address}")
                else:
                    print(f"Error: dirección {address} fuera de rango")
                    self.stack.extend([value, address_or_name])
            except (ValueError, TypeError):
                print(f"Error: '{address_or_name}' no es una variable o dirección válida")
                self.stack.extend([value, address_or_name])

    def _mc_fetch(self):
        if len(self.stack) < 1:
            print("Error: faltan parámetros para mc@")
            return

        address = self.stack.pop()

        try:
            address = int(address)
        except (ValueError, TypeError):
            print(f"Error: mc@ requiere una dirección numérica, recibió {type(address)}")
            self.stack.append(address)
            return

        if address < 0 or address >= self._memory_size:
            print(f"Error: dirección de memoria inválida: {address}")
            self.stack.append(address)
            return

        value = self.memory[address]
        byte_value = value & 0xFF
        self.stack.append(byte_value)

    def _mc_store(self):
        if len(self.stack) < 2:
            print("Error: faltan parámetros para mc!")
            return

        address = self.stack.pop()
        value = self.stack.pop()

        try:
            address = int(address)
        except (ValueError, TypeError):
            print(f"Error: mc! requiere una dirección numérica, recibió {type(address)}")
            self.stack.extend([value, address])
            return

        if address < 0 or address >= self._memory_size:
            print(f"Error: dirección de memoria inválida: {address}")
            self.stack.extend([value, address])
            return

        byte_value = int(value) & 0xFF
        self.memory[address] = byte_value
        #print(f"Almacenado byte {byte_value} en dirección {address}")

    def _c_comma(self):
        if len(self.stack) < 1:
            print("Error: faltan parámetros para c,")
            return

        value = self.stack.pop()

        if self.here >= self._memory_size:
            print("Error: memoria llena")
            self.stack.append(value)
            return

        byte_value = int(value) & 0xFF
        self.memory[self.here] = byte_value
        #print(f"Almacenado byte {byte_value} en dirección {self.here}")
        self.here += 1

    def _emit(self):
        if not self.stack:
            print("Error: faltan parámetros para emit")
            return

        char_code = self.stack.pop()
        try:
            char_code = int(char_code) & 0xFF
            print(chr(char_code), end='')
            sys.stdout.flush()
        except (ValueError, OverflowError):
            print(f"Error: código de carácter inválido: {char_code}")

    def _key(self):
        """Lee un carácter del teclado y pone su código ASCII en la pila"""
        try:
            # Leer un solo carácter
            # Usar sys.stdin.buffer.read(1) para evitar problemas de codificación
            # y luego decodificar.
            char_byte = sys.stdin.buffer.read(1)
            if char_byte:
                self.stack.append(char_byte[0]) # El código ASCII es el primer byte
            else:
                # EOF o error
                self.stack.append(0)
        except Exception as e:
            print(f"Error leyendo tecla: {e}")
            self.stack.append(0)

    def _key_question(self):
        """Verifica si hay tecla disponible"""
        try:
            # Usar select para verificar si hay datos disponibles en stdin
            # timeout de 0 = no bloqueante
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                self.stack.append(-1)  # -1 = hay tecla disponible (TRUE en Forth)
            else:
                self.stack.append(0)   # 0 = no hay tecla disponible (FALSE en Forth)
        except Exception:
            # Si select no está disponible (ej: Windows sin compatibilidad), siempre retornar 0
            self.stack.append(0)

    def _accept(self):
        """ACCEPT ( addr len -- len' )
        Lee una línea de entrada del usuario y la almacena en la dirección especificada.
        addr: dirección donde almacenar la entrada
        len: máximo número de caracteres a leer
        len': número de caracteres realmente leídos
        """
        if len(self.stack) < 2:
            print("Error: ACCEPT requiere addr y len en la pila")
            return
        
        max_len = self.stack.pop()
        addr = self.stack.pop()
        
        try:
            # Leer una línea del usuario
            user_input = input()
            
            # Limitar al máximo especificado
            user_input = user_input[:max_len]
            
            # Almacenar cada carácter en memoria
            for i, char in enumerate(user_input):
                if addr + i >= self._memory_size:
                    break
                self.memory[addr + i] = ord(char)
            
            # Retornar la longitud real leída
            self.stack.append(len(user_input))
            
        except Exception as e:
            print(f"Error en ACCEPT: {e}")
            self.stack.append(0)

    def _pad(self):
        """PAD ( -- addr )
        Retorna la dirección del área temporal PAD (primeros 256 bytes de memoria).
        PAD es un área de memoria temporal para operaciones con cadenas.
        """
        # PAD tradicional está en los primeros 256 bytes
        self.stack.append(0)

    # Bucles DO/LOOP
    def _loop_i(self):
        """Obtiene el índice del bucle actual"""
        if len(self._loop_stack) >= 2:
            # El índice está en la última posición
            self.stack.append(self._loop_stack[-1])
        else:
            print("Error: I usado fuera de bucle DO/LOOP")

    def _loop_j(self):
        """Obtiene el índice del bucle externo (para bucles anidados)"""
        if len(self._loop_stack) >= 4:
            # En bucles anidados: [limit_outer, index_outer, limit_inner, index_inner]
            # El índice del bucle externo está 3 posiciones desde el final
            self.stack.append(self._loop_stack[-3])
        else:
            print("Error: J usado fuera de bucle anidado")

    def _loop_k(self):
        """Obtiene el índice del tercer nivel de bucle (para triple anidación)"""
        if len(self._loop_stack) >= 6:
            # En triple anidación: [limit_3, index_3, limit_2, index_2, limit_1, index_1]
            # El índice del tercer nivel está 5 posiciones desde el final
            self.stack.append(self._loop_stack[-5])
        else:
            print("Error: K usado fuera de bucle triple anidado")

    def _loop_leave(self):
        """Marca para salir del bucle actual"""
        self._leave_flag = True

    def _exit_word(self):
        """EXIT - Sale de la ejecución de la palabra actual inmediatamente
        Como un 'return' en otros lenguajes
        Ejemplo: : test 10 . exit 20 . ; → solo imprime 10
        """
        self._exit_flag = True

    def _recurse(self):
        """RECURSE - Compila una llamada recursiva a la palabra actual
        Solo puede usarse dentro de una definición (entre : y ;)
        Palabra inmediata estándar ANS Forth
        Ejemplo: : factorial ( n -- n! ) dup 1 <= if drop 1 else dup 1 - recurse * then ;
        """
        if not self._defining or self._current_name is None:
            print("Error: RECURSE solo puede usarse dentro de una definición")
            sys.stdout.flush()
            return
        
        # Agregar el nombre de la palabra actual a su propia definición
        self._current_definition.append(self._current_name)

    def _do_marker(self):
        """Marcador para DO - manejado especialmente en execute()"""
        pass

    def _loop_marker(self):
        """Marcador para LOOP - manejado especialmente en execute()"""
        pass

    def _plusloop_marker(self):
        """Marcador para +LOOP - manejado especialmente en execute()"""
        pass

    def _if_marker(self):
        """Marcador para IF - manejado especialmente en execute()"""
        pass

    def _else_marker(self):
        """Marcador para ELSE - manejado especialmente en execute()"""
        pass

    def _then_marker(self):
        """Marcador para THEN - manejado especialmente en execute()"""
        pass

    def _begin_marker(self):
        """Marcador para BEGIN - manejado especialmente en execute()"""
        pass

    def _until_marker(self):
        """Marcador para UNTIL - manejado especialmente en execute()"""
        pass

    def _again_marker(self):
        """Marcador para AGAIN - manejado especialmente en execute()"""
        pass

    def _while_marker(self):
        """Marcador para WHILE - manejado especialmente en execute()"""
        pass

    def _repeat_marker(self):
        """Marcador para REPEAT - manejado especialmente en execute()"""
        pass

    # Ejecución diferida
    def _tick(self):
        if not self.stack:
            print("Error: falta nombre de palabra para '")
            return

        word_name = self.stack.pop()

        if word_name in self.words:
            self.stack.append(('word', word_name, self.words[word_name]))
        elif word_name in self.immediate_words:
            self.stack.append(('immediate', word_name, self.immediate_words[word_name]))
        elif word_name in self.variables:
            self.stack.append(('variable', word_name, self.words[word_name])) # Empuja la función que empuja el nombre de la variable
        elif word_name in self.constants:
            self.stack.append(('constant', word_name, self.words[word_name])) # Empuja la función que empuja el valor
        elif word_name in self.values:
            self.stack.append(('value', word_name, self.words[word_name])) # Empuja la función que empuja el valor
        else:
            print(f"Error: palabra '{word_name}' no definida")
            self.stack.append(word_name)

    def _find_word_function(self, word_name):
        if word_name in self.words:
            return self.words[word_name]
        elif word_name in self.immediate_words:
            return self.immediate_words[word_name]
        elif word_name in self.variables:
            return self.words[word_name] # Devuelve la función que empuja el nombre de la variable
        elif word_name in self.constants:
            return self.words[word_name] # Devuelve la función que empuja el valor
        elif word_name in self.values:
            return self.words[word_name] # Devuelve la función que empuja el valor
        return None

    def _execute_word(self):
        if not self.stack:
            print("Error: falta función para execute")
            return

        item = self.stack.pop()

        if isinstance(item, tuple) and len(item) == 3:
            # Formato ('type', name, function)
            _, _, func = item
            func()
        elif isinstance(item, str):
            # Es un nombre de palabra
            func = self._find_word_function(item)
            if func:
                func()
            else:
                print(f"Error: no se puede ejecutar '{item}' - palabra no encontrada")
        elif callable(item):
            # Es una función directamente
            item()
        else:
            print(f"Error: elemento no ejecutable: {item}")

    def _bracket_tick(self):
        if not self._defining:
            print("Error: ['] solo se puede usar durante compilación")
            return

        # _compiling_tick se maneja en _execute_token y _compile_definition
        # Esta palabra sólo se activa cuando se encuentra '[' y luego '' en modo compilación.
        # El parser ya habrá tokenizado [']. Aquí sólo marcamos el modo.
        self._compiling_tick = True


    def _compile_tick_definition(self, word_name):
        def tick_compiled():
            func = self._find_word_function(word_name)
            if func:
                # Empujar el tipo, nombre y función para que execute la resuelva
                self.stack.append(('word', word_name, func))
            else:
                print(f"Error en ejecución: palabra '{word_name}' no encontrada")
        return tick_compiled

    # Sistema de cadenas en memoria
    def _store_string(self, string, address):
        for i, char in enumerate(string):
            if address + i >= self._memory_size:
                print(f"Error: memoria insuficiente para almacenar cadena en {address}")
                return False
            self.memory[address + i] = ord(char)
        # Añadir terminador nulo si hay espacio
        if address + len(string) < self._memory_size:
            self.memory[address + len(string)] = 0
        return True

    def _load_string(self, address, max_length=None):
        if max_length is None:
            max_length = self._memory_size - address

        chars = []
        for i in range(max_length):
            if address + i >= self._memory_size:
                break
            byte_val = self.memory[address + i]
            if byte_val == 0: # Terminador nulo
                break
            chars.append(chr(byte_val))
        return "".join(chars)

    # Tokenizador y ejecución
    def _simple_tokenize(self, code):
        tokens = []
        i = 0
        length = len(code)
        base = self.variables.get('base', 10)
        
        while i < length:
            if code[i].isspace():
                i += 1
                continue

            # Comentarios de línea
            if code[i] == '\\':
                while i < length and code[i] != '\n':
                    i += 1
                continue

            # Comentarios de bloque (...)
            if code[i] == '(':
                i += 1
                while i < length and code[i] != ')':
                    i += 1
                if i < length:
                    i += 1  # saltar el )
                else:
                    print('Error: comentario sin cerrar (falta ")")')
                    break
                continue

            # Strings ." y s"
            if i + 1 < length and code[i:i+2] == '."':
                i += 2
                start = i
                while i < length and code[i] != '"':
                    i += 1
                if i < length:
                    string_content = code[start:i]
                    tokens.append('."')
                    tokens.append(string_content)
                    i += 1
                else:
                    print('Error: cadena sin cerrar después de ."')
                    break
                continue

            elif i + 1 < length and code[i:i+2] == 's"':
                i += 2
                start = i
                while i < length and code[i] != '"':
                    i += 1
                if i < length:
                    string_content = code[start:i].strip() # strip() es común para s"
                    tokens.append('s"')
                    tokens.append(string_content)
                    i += 1
                else:
                    print('Error: cadena sin cerrar después de s"')
                    break
                continue

            # Palabras especiales como [char], ['], etc.
            if code[i] == '[':
                if i + 1 < length and code[i+1] == "'":
                    if i + 2 < length and code[i+2] == ']':
                        tokens.append("[']")
                        i += 3
                        continue
                elif i + 1 < length and code[i+1] == 'c' and i + 2 < length and code[i+2] == 'h' and i + 3 < length and code[i+3] == 'a' and i + 4 < length and code[i+4] == 'r':
                    if i + 5 < length and code[i+5] == ']':
                        tokens.append("[char]")
                        i += 6
                        continue
                # Si no es ningún caso especial, es simplemente '['
                tokens.append('[')
                i += 1
                continue
            
            # Manejar ] como token individual
            if code[i] == ']':
                tokens.append(']')
                i += 1
                continue

            # Parsear números con base
            start = i
            token_candidate = ""
            j = i
            while j < length and not code[j].isspace() and code[j] != '\\':
                token_candidate += code[j]
                j += 1

            parsed_num = self._parse_number_with_base(token_candidate)
            if parsed_num is not None:
                tokens.append(str(parsed_num)) # Devolver como string para que execute_token lo maneje
                i = j
                continue

            # Si no es número especial, parsear como token normal
            start = i
            while i < length and not code[i].isspace() and code[i] != '\\':
                # Detener si encontramos inicio de string o comentario
                if (i + 1 < length and code[i:i+2] == '."' ) or \
                   (i + 1 < length and code[i:i+2] == 's"' ) or \
                   (code[i] == '(' ) or \
                   (code[i] == '[' ):
                    break
                i += 1

            if i > start:
                token = code[start:i]
                tokens.append(token)

        return tokens

    def _parse_number_with_base(self, token):
        """Intenta parsear un token como número según la base actual"""
        base = self.variables.get('base', 10)

        # Primero intentar como entero en la base actual
        try:
            # Manejar números negativos
            if token.startswith('-'):
                return -int(token[1:], base)
            else:
                return int(token, base)
        except ValueError:
            pass

        # Si falla y estamos en decimal, intentar como float
        if base == 10:
            try:
                return float(token)
            except ValueError:
                pass

        return None

    def _execute_token_runtime(self, token):
        """Ejecuta un token inmediatamente (para modo interpretación o bracket_mode)"""
        # Cuando ejecutamos palabras durante bracket mode, necesitamos temporalmente
        # desactivar _defining para que esas palabras se ejecuten correctamente
        saved_defining = self._defining
        saved_bracket_mode = self._bracket_mode
        
        try:
            # Temporalmente salir de modo compilación
            self._defining = False
            self._bracket_mode = False
            
            # Intenta como palabra del sistema
            if token in self.immediate_words:
                self.immediate_words[token]()
            elif token in self.words:
                self.words[token]()
            else:
                # Intenta parsear como número
                parsed_num = self._parse_number_with_base(token)
                if parsed_num is not None:
                    self.stack.append(parsed_num)
                else:
                    print(f"Palabra no definida: {token}")
        finally:
            # Restaurar estado de compilación
            self._defining = saved_defining
            self._bracket_mode = saved_bracket_mode

    def _execute_token(self, token):
        # Verificar si es un token especial para ser manejado
        # Manejar la palabra LITERAL
        if token == 'literal' and self._defining:
            # LITERAL toma un valor de la pila y lo compila como un literal
            if len(self.stack) >= 1:
                value = self.stack.pop()
                self._current_definition.append(('literal', value))
            else:
                print("Error: LITERAL requiere un valor en la pila")

        elif token == 'variable':
            if self._defining and self._current_definition is not None and self._input_index + 1 < len(self._input_tokens):
                var_name = self._input_tokens[self._input_index + 1]
                self._current_definition.append(('variable', var_name))
                self._input_index += 1 # Consumir el nombre
            else:
                print("Error: 'variable' solo en modo de compilación o sin nombre")

        elif token == 'constant':
            if self._defining and self._current_definition is not None and self._input_index + 1 < len(self._input_tokens) and len(self.stack) >= 1:
                const_name = self._input_tokens[self._input_index + 1]
                const_value = self.stack.pop()
                self._current_definition.append(('constant', const_name, const_value))
                self._input_index += 1
            else:
                print("Error: 'constant' requiere nombre y valor en la pila, y modo de compilación")

        elif token == 'value':
             if self._defining and self._current_definition is not None and self._input_index + 1 < len(self._input_tokens) and len(self.stack) >= 1:
                value_name = self._input_tokens[self._input_index + 1]
                value_value = self.stack.pop()
                self._current_definition.append(('value', value_name, value_value))
                self._input_index += 1
             else:
                print("Error: 'value' requiere nombre y valor en la pila, y modo de compilación")

        elif token == 'to':
            if self._defining and self._current_definition is not None and self._input_index + 1 < len(self._input_tokens) and len(self.stack) >= 1:
                value_name = self._input_tokens[self._input_index + 1]
                new_value = self.stack.pop()
                self._current_definition.append(('set_value', value_name, new_value))
                self._input_index += 1
            else:
                print("Error: 'to' requiere nombre y valor en la pila, y modo de compilación")

        # Manejar char y [char] que necesitan el siguiente token
        elif token in ('char', '[char]'):
            is_compiling = self._defining # Determinar si estamos en modo compilación

            if self._input_index + 1 < len(self._input_tokens):
                next_token_str = self._input_tokens[self._input_index + 1]
                if next_token_str and len(next_token_str) > 0:
                    char_code = ord(next_token_str[0])
                    if is_compiling: # [char]
                        self._current_definition.append(('literal', char_code)) # Compilar el código ASCII como literal
                    else: # char
                        self.stack.append(char_code)
                    self._input_index += 1 # Consumir el carácter
                else:
                    print(f"Error: token vacío después de {token}")
            else:
                print(f"Error: falta carácter después de {token}")

        elif token == 'forget':
             # forget debe leer el nombre del siguiente token
            if self._input_index + 1 < len(self._input_tokens):
                target_name = self._input_tokens[self._input_index + 1]
                if self._is_system_word(target_name):
                    print(f"Error: '{target_name}' es una palabra del sistema y no puede ser olvidada")
                else:
                    target_index = None
                    for j, (def_type, name) in enumerate(self._definition_order):
                        if name == target_name:
                            target_index = j
                            break

                    if target_index is None:
                        print(f"Error: '{target_name}' no encontrada en definiciones de usuario")
                    else:
                        definitions_to_remove = self._definition_order[target_index:]
                        for def_type, name in definitions_to_remove:
                            self._remove_definition(def_type, name)
                        self._definition_order = self._definition_order[:target_index]
                        print(f"Olvidadas {len(definitions_to_remove)} definiciones desde '{target_name}'")
                self._input_index += 1 # Consumir el nombre de la palabra
            else:
                print("Error: falta nombre después de forget")

        elif token == 'see':
            # see debe leer el nombre del siguiente token
            if self._input_index + 1 < len(self._input_tokens):
                word_name = self._input_tokens[self._input_index + 1]
                self._see_word(word_name)
                self._input_index += 1 # Consumir el nombre de la palabra
            else:
                print("Error: falta nombre de palabra después de see")

        elif token == 'measure':
            # measure debe leer el nombre de la palabra a medir
            if self._input_index + 1 < len(self._input_tokens):
                word_name = self._input_tokens[self._input_index + 1]
                
                # Medir tiempo de ejecución
                start_time = time.perf_counter()
                
                # Ejecutar la palabra
                if word_name in self.immediate_words:
                    self.immediate_words[word_name]()
                elif word_name in self.words:
                    self.words[word_name]()
                elif word_name in self.variables:
                    self.stack.append(self.variables[word_name])
                elif word_name in self.constants:
                    self.stack.append(self.constants[word_name])
                elif word_name in self.values:
                    self.stack.append(self.values[word_name])
                else:
                    print(f"Error: palabra '{word_name}' no encontrada")
                    self._input_index += 1
                    return
                
                end_time = time.perf_counter()
                elapsed = end_time - start_time
                
                # Formatear automáticamente según el tiempo
                time_str, time_value = self._format_time(elapsed)
                
                # Poner el tiempo en la pila (en segundos)
                self.stack.append(elapsed)
                
                # Mostrar resultado formateado
                print(f"Tiempo de '{word_name}': {time_str}")
                
                self._input_index += 1 # Consumir el nombre de la palabra
            else:
                print("Error: falta nombre de palabra después de measure")

        elif token == 'code':
            # CODE inicia la definición de una primitiva en Python
            if self._input_index + 1 < len(self._input_tokens):
                code_name = self._input_tokens[self._input_index + 1]
                
                # Validar nombre (debe contener / para grupo/nombre)
                if '/' not in code_name:
                    print(f"Error: nombre CODE debe incluir grupo, ej: 'utils/double' no '{code_name}'")
                    self._input_index += 1
                    return
                
                # Sanitizar el path
                try:
                    code_name = self._sanitize_code_path(code_name)
                except ValueError as e:
                    print(f"Error: path inválido '{code_name}': {e}")
                    self._input_index += 1
                    return
                
                # Verificar que no sea palabra del sistema
                word_only = code_name.split('/')[-1]
                if self._is_system_word(word_only):
                    print(f"Error: '{word_only}' es una palabra del sistema y no puede ser redefinida con CODE")
                    self._input_index += 1
                    return
                
                # Activar modo captura de código
                self._code_mode = True
                self._code_name = code_name
                self._code_buffer = []
                
                print(f"Capturando código Python para '{code_name}' (use ENDCODE para finalizar)...")
                self._input_index += 1  # Consumir el nombre
            else:
                print("Error: CODE requiere un nombre (ej: CODE utils/double)")

        elif token == 'endcode':
            # ENDCODE finaliza la captura y crea la palabra
            if not self._code_mode:
                print("Error: ENDCODE sin CODE previo")
                return
            
            # Procesar el código capturado
            code_text = '\n'.join(self._code_buffer)
            self._create_code_word(self._code_name, code_text)
            
            # Resetear estado
            self._code_mode = False
            self._code_name = None
            self._code_buffer = []

        elif token == 'import':
            # IMPORT carga una palabra CODE desde extended-code/
            if self._input_index + 1 < len(self._input_tokens):
                import_name = self._input_tokens[self._input_index + 1]
                
                # Validar nombre (debe contener / para separar path)
                if '/' not in import_name:
                    print(f"Error: nombre IMPORT debe incluir path, ej: 'utils/double' o 'sensors/temp/read'")
                    self._input_index += 1
                    return
                
                # Sanitizar el path
                try:
                    import_name = self._sanitize_code_path(import_name)
                except ValueError as e:
                    print(f"Error: path inválido '{import_name}': {e}")
                    self._input_index += 1
                    return
                
                # Separar path completo y nombre de la palabra
                # Soporta paths anidados: sensors/temp/read → palabra "read"
                parts = import_name.split('/')
                word_name = parts[-1]  # Última parte es el nombre de la palabra
                relative_path = '/'.join(parts[:-1])  # Resto es el path relativo
                
                # Construir ruta del archivo
                base_dir = os.path.join(self._base_dir, 'extended-code')
                file_path = os.path.join(base_dir, relative_path, f"{word_name}.py")
                
                # Verificar que el archivo existe
                if not os.path.exists(file_path):
                    print(f"Error: archivo no encontrado: extended-code/{import_name}.py")
                    print(f"Usa LSCODE para ver palabras disponibles")
                    self._input_index += 1
                    return
                
                try:
                    # Cargar el módulo dinámicamente
                    # Crear nombre único de módulo reemplazando / con _
                    module_name = import_name.replace('/', '_')
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Verificar que tiene la función execute
                    if not hasattr(module, 'execute'):
                        print(f"Error: {file_path} no tiene función execute()")
                        self._input_index += 1
                        return
                    
                    # Crear wrapper que llama a execute(forth)
                    def imported_word():
                        try:
                            module.execute(self)
                        except Exception as e:
                            print(f"Error ejecutando '{word_name}': {e}")
                    
                    # Registrar la palabra
                    self.words[word_name] = imported_word
                    self._definition_order.append(('code', word_name))
                    self._definition_source[word_name] = f"IMPORT {import_name}"
                    
                    print(f"✓ Palabra '{word_name}' importada desde {import_name}.py")
                    
                except Exception as e:
                    print(f"Error importando {import_name}: {e}")
                
                self._input_index += 1  # Consumir el nombre
            else:
                print("Error: IMPORT requiere un nombre (ej: IMPORT utils/double)")

        elif token == 'rmcode':
            # RMCODE elimina un archivo CODE de extended-code/
            if self._input_index + 1 < len(self._input_tokens):
                import_name = self._input_tokens[self._input_index + 1]
                
                # Validar nombre (debe contener / para separar path)
                if '/' not in import_name:
                    print(f"Error: nombre RMCODE debe incluir path, ej: 'utils/double' o 'sensors/temp/read'")
                    self._input_index += 1
                    return
                
                # Sanitizar el path
                try:
                    import_name = self._sanitize_code_path(import_name)
                except ValueError as e:
                    print(f"Error: path inválido '{import_name}': {e}")
                    self._input_index += 1
                    return
                
                # Separar path completo y nombre de la palabra
                parts = import_name.split('/')
                word_name = parts[-1]  # Última parte es el nombre de la palabra
                relative_path = '/'.join(parts[:-1])  # Resto es el path relativo
                
                # Construir ruta del archivo
                base_dir = os.path.join(self._base_dir, 'extended-code')
                file_path = os.path.join(base_dir, relative_path, f"{word_name}.py")
                
                # Verificar que el archivo existe
                if not os.path.exists(file_path):
                    print(f"Error: archivo no encontrado: extended-code/{import_name}.py")
                    print(f"Usa LSCODE para ver palabras disponibles")
                    self._input_index += 1
                    return
                
                try:
                    # Eliminar el archivo
                    os.remove(file_path)
                    print(f"✓ Archivo eliminado: extended-code/{import_name}.py")
                    
                    # Limpiar directorios vacíos
                    if relative_path:
                        dir_path = os.path.abspath(os.path.join(base_dir, relative_path))
                        base_dir_abs = os.path.abspath(base_dir)
                        
                        try:
                            # Intentar eliminar directorios vacíos de forma recursiva
                            while dir_path != base_dir_abs:
                                # Verificar contención en cada iteración (seguridad crítica)
                                try:
                                    common = os.path.commonpath([base_dir_abs, dir_path])
                                    if common != base_dir_abs:
                                        # dir_path está fuera de base_dir, detener
                                        break
                                except ValueError:
                                    # Paths en diferentes drives, detener
                                    break
                                
                                # Verificar si está vacío o solo tiene __pycache__
                                if os.path.isdir(dir_path):
                                    contents = os.listdir(dir_path)
                                    
                                    # Si solo tiene __pycache__, eliminarlo también
                                    if contents == ['__pycache__']:
                                        pycache_dir = os.path.join(dir_path, '__pycache__')
                                        if os.path.isdir(pycache_dir):
                                            # Eliminar contenido de __pycache__
                                            for item in os.listdir(pycache_dir):
                                                os.remove(os.path.join(pycache_dir, item))
                                            os.rmdir(pycache_dir)
                                        contents = []
                                    
                                    # Si ahora está vacío, eliminar
                                    if not contents:
                                        os.rmdir(dir_path)
                                        dir_path = os.path.dirname(dir_path)
                                    else:
                                        break
                                else:
                                    break
                        except OSError:
                            # Ignorar errores de limpieza (directorio no vacío, permisos, etc.)
                            pass
                    
                    # Si la palabra está cargada, hacer FORGET
                    if word_name in self.words or word_name in self.immediate_words:
                        print(f"  (La palabra '{word_name}' sigue en memoria - usa FORGET {word_name} para eliminarla)")
                    
                except Exception as e:
                    print(f"Error eliminando {import_name}: {e}")
                
                self._input_index += 1  # Consumir el nombre
            else:
                print("Error: RMCODE requiere un nombre (ej: rmcode utils/double)")

        elif token == 'seecode':
            # SEECODE muestra el código Forth original de una palabra CODE
            if self._input_index + 1 < len(self._input_tokens):
                import_name = self._input_tokens[self._input_index + 1]
                
                # Validar nombre (debe contener / para separar path)
                if '/' not in import_name:
                    print(f"Error: nombre SEECODE debe incluir path, ej: 'utils/double' o 'sensors/temp/read'")
                    self._input_index += 1
                    return
                
                # Sanitizar el path
                try:
                    import_name = self._sanitize_code_path(import_name)
                except ValueError as e:
                    print(f"Error: path inválido '{import_name}': {e}")
                    self._input_index += 1
                    return
                
                # Separar path completo y nombre de la palabra
                parts = import_name.split('/')
                word_name = parts[-1]  # Última parte es el nombre de la palabra
                relative_path = '/'.join(parts[:-1])  # Resto es el path relativo
                
                # Construir ruta del archivo
                base_dir = os.path.join(self._base_dir, 'extended-code')
                file_path = os.path.join(base_dir, relative_path, f"{word_name}.py")
                
                # Verificar que el archivo existe
                if not os.path.exists(file_path):
                    print(f"Error: archivo no encontrado: extended-code/{import_name}.py")
                    print(f"Usa LSCODE para ver palabras disponibles")
                    self._input_index += 1
                    return
                
                try:
                    # Leer el archivo y extraer el código Forth original
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Buscar las marcas de inicio y fin del código Forth
                    start_marker = "# === CÓDIGO FORTH ORIGINAL ==="
                    end_marker = "# === FIN CÓDIGO FORTH ==="
                    
                    forth_code = []
                    capturing = False
                    
                    for line in lines:
                        if start_marker in line:
                            capturing = True
                            continue
                        elif end_marker in line:
                            break
                        elif capturing:
                            # Remover el "# " del inicio
                            if line.startswith('# '):
                                forth_code.append(line[2:].rstrip())
                            elif line.strip() == '#':
                                forth_code.append('')
                    
                    if forth_code:
                        print(f"\n=== CÓDIGO FORTH ORIGINAL: {import_name} ===\n")
                        for line in forth_code:
                            print(line)
                        print(f"\n=== FIN ===\n")
                    else:
                        print(f"Advertencia: no se encontró código Forth original en {import_name}.py")
                        print("(Puede ser un archivo CODE antiguo sin comentarios)")
                    
                except Exception as e:
                    print(f"Error leyendo {import_name}: {e}")
                
                self._input_index += 1  # Consumir el nombre
            else:
                print("Error: SEECODE requiere un nombre (ej: seecode utils/double)")

        elif token == "'" and not self._defining:
            # ' palabra en interpretación
            if self._input_index + 1 < len(self._input_tokens):
                word_name = self._input_tokens[self._input_index + 1]
                self._tick_interpret(word_name)
                self._input_index += 1
            else:
                print("Error: falta nombre de palabra después de '")

        elif token == "[']" and self._defining:
            # ['] palabra en compilación
            if self._input_index + 1 < len(self._input_tokens):
                word_name = self._input_tokens[self._input_index + 1]
                tick_func = self._compile_tick_definition(word_name)
                self._current_definition.append(('tick', word_name, tick_func))
                self._input_index += 1
            else:
                print("Error: falta palabra después de [']")

        elif token == 'postpone' and self._defining:
            # POSTPONE compila la siguiente palabra, incluso si es inmediata
            if self._input_index + 1 < len(self._input_tokens):
                next_word = self._input_tokens[self._input_index + 1]
                # Marcar como palabra que debe compilarse, no ejecutarse
                self._current_definition.append(('compile', next_word))
                self._input_index += 1
            else:
                print("Error: falta palabra después de postpone")

        elif token == 'create' and not self._defining:
            # CREATE fuera de definiciones - crear palabra inmediatamente
            if self._input_index + 1 < len(self._input_tokens):
                name = self._input_tokens[self._input_index + 1]

                if name in self.words or name in self.immediate_words:
                    print(f"Error: '{name}' ya está definida")
                else:
                    # Reservar espacio en memoria
                    if self.here + 1 >= self._memory_size: # +1 por si acaso
                        print("Error: memoria insuficiente para CREATE")
                    else:
                        created_address = self.here

                        # Crear una función que empuje la dirección
                        def push_address(addr=created_address):
                            self.stack.append(addr)

                        self.words[name] = push_address
                        self._definition_order.append(('created', name))
                        self._last_created_word = name
                        self._last_created_address = created_address
                        self.here += 1 # Reservar espacio para la dirección
                        #print(f"Palabra CREATE '{name}' creada en dirección {created_address}")

                self._input_index += 1 # Consumir el nombre

        elif token == 'create' and self._defining:
            # CREATE dentro de una definición - compilar instrucción especial
            # que leerá el nombre cuando se ejecute
            self._current_definition.append(('runtime-create',))

        elif token == 'does>' and self._defining:
            # DOES> se compila como una marca especial
            self._current_definition.append(('does>',))

        elif token == 'immediate':
            # Marcar la última palabra definida como inmediata
            self._immediate()

        elif token == 'if':
            # Manejar IF en modo de compilación (se procesará luego)
            self._current_definition.append('if')

        elif token == 'else':
             self._current_definition.append('else')

        elif token == 'then':
             self._current_definition.append('then')

        elif token == 'do':
             self._current_definition.append('do')

        elif token == 'loop':
             self._current_definition.append('loop')

        elif token == '+loop':
             self._current_definition.append('+loop')

        elif token == 'begin':
            self._current_definition.append('begin')

        elif token == 'until':
            self._current_definition.append('until')

        elif token == 'again':
            self._current_definition.append('again')

        elif token == 'while':
            self._current_definition.append('while')

        elif token == 'repeat':
            self._current_definition.append('repeat')

        elif token == 'postpone':
            # POSTPONE compila la siguiente palabra, incluso si es inmediata
            if self._input_index + 1 < len(self._input_tokens):
                next_word = self._input_tokens[self._input_index + 1]
                # Marcar como palabra que debe compilarse, no ejecutarse
                self._current_definition.append(('compile', next_word))
                self._input_index += 1
            else:
                print("Error: falta palabra después de postpone")

        elif token == '."':
            # Compilar ." con su string
            if self._input_index + 1 < len(self._input_tokens):
                self._current_definition.append(('print-string', self._input_tokens[self._input_index + 1]))
                self._input_index += 1
            else:
                print("Error: cadena faltante después de .\"")

        elif token == 's"':
            # Compilar s" con su string
            if self._input_index + 1 < len(self._input_tokens):
                self._current_definition.append(('push-string', self._input_tokens[self._input_index + 1]))
                self._input_index += 1
            else:
                print("Error: cadena faltante después de s\"")

        # Manejar RECURSE explícitamente (ejecuta durante compilación)
        elif token == 'recurse' and token in self.immediate_words:
            self.immediate_words[token]()
        
        # Si es palabra inmediata (y no estamos definiendo, o es una palabra de control)
        elif token in self.immediate_words and (not self._defining or token in ('if', 'else', 'then', 'do', 'loop', '+loop', 'begin', 'until', 'again', 'while', 'repeat')):
            if self._defining:
                # Las palabras de control se agregan directamente a la definición
                self._current_definition.append(token)
            else:
                # Ejecutar palabra inmediata en modo interpretación
                self.immediate_words[token]()

        # Si es una palabra normal
        elif token in self.words:
            if self._defining:
                # Compilar la palabra
                self._current_definition.append(token)
            else:
                # Ejecutar palabra normal en modo interpretación
                self.words[token]()

        # Si estamos compilando y es un literal (número)
        elif self._defining:
            parsed_num = self._parse_number_with_base(token)
            if parsed_num is not None:
                self._current_definition.append(('literal', parsed_num))
            else:
                 print(f"Error: Palabra no definida o mal formada durante compilación: '{token}'")

        # Si estamos interpretando y es un literal (número)
        else:
            parsed_num = self._parse_number_with_base(token)
            if parsed_num is not None:
                self.stack.append(parsed_num)
            else:
                print(f"Palabra no definida: {token}")


    def execute(self, code):
        if not code or code.isspace():
            return

        # Si estamos en modo CODE, capturar líneas de código Python
        if self._code_mode:
            # Verificar si la línea contiene ENDCODE
            if code.strip().lower() == 'endcode':
                # Procesar el código capturado
                code_text = '\n'.join(self._code_buffer)
                self._create_code_word(self._code_name, code_text)
                
                # Resetear estado
                self._code_mode = False
                self._code_name = None
                self._code_buffer = []
            else:
                # Acumular línea en buffer
                self._code_buffer.append(code)
            return

        tokens = self._simple_tokenize(code)
        if not tokens:
            return

        # Guardar tokens y código original para palabras como PARSE
        self._input_tokens = tokens
        self._input_code = code
        self._input_index = 0
        self._code_position = 0  # Posición en el código original
        self._skip_remaining_tokens = False  # Flag para PARSE y palabras similares

        i = 0
        while i < len(tokens):
            # Si una palabra pidió saltar tokens restantes, terminar
            if self._skip_remaining_tokens:
                self._skip_remaining_tokens = False
                break
                
            self._input_index = i # Actualizar índice global para uso por palabras como CREATE
            token = tokens[i]
            token_lower = token.lower()  # Normalizar para comparaciones

            if token_lower == ':' and not self._bracket_mode: # Solo iniciar definición si no estamos en modo [ ]
                if i + 1 < len(tokens):
                    name = tokens[i + 1]
                    self._defining = True
                    self._current_name = name
                    self._current_definition = []
                    self._definition_start_index = i  # Guardar dónde empieza la definición
                    # Actualizar STATE a modo compilación
                    self.variables['state'] = -1
                    i += 2
                else:
                    print("Error: nombre de palabra faltante después de :")
                    i += 1

            elif token_lower == ';' and self._defining and not self._bracket_mode: # Solo terminar definición si no estamos en modo [ ]
                if self._current_name:
                    self.words[self._current_name] = self._compile_definition()
                    self._definition_order.append(('word', self._current_name))
                    # Guardar el código fuente original si es posible
                    source_code = ' '.join(tokens[self._definition_start_index:i+1])
                    self._definition_source[self._current_name] = source_code
                    self._last_defined_word = self._current_name
                    self._defining = False
                    self._current_name = None
                    # Actualizar STATE a modo interpretación
                    self.variables['state'] = 0
                    i += 1
                else:
                    print("Error: ';' sin definición en progreso")
                    i += 1
            # Manejar [ y ] para cambiar modo de compilación/interpretación
            elif token_lower == '[' and not self._defining: # Si estamos en modo de interpretación y vemos [
                 print("Error: [ no se puede usar en modo de interpretación")
                 i += 1
            elif token_lower == '[' and self._defining: # Si estamos en modo de compilación y vemos [
                 self._open_bracket()
                 i += 1
            elif token_lower == ']' and self._defining and self._bracket_mode: # Si estamos en compilación Y en bracket_mode vemos ]
                 self._close_bracket()
                 i += 1
            elif token_lower == ']' and not self._bracket_mode:  # ] fuera de lugar
                 print("Error: ] sin [ correspondiente")
                 i += 1

            # Si estamos en modo compilación (y no en modo bracket temporal)
            elif self._defining and not self._bracket_mode:
                old_index = self._input_index
                self._execute_token(token)
                # Si _execute_token consumió tokens adicionales (ej: .", s"), actualizar i
                tokens_consumed = self._input_index - old_index
                i += 1 + tokens_consumed  # +1 para el token actual + tokens adicionales consumidos

            # Si estamos en modo de interpretación o en modo bracket temporal
            else:
                # Manejar palabras que no son parte de una definición
                if token_lower == 'variable':
                    if i + 1 < len(tokens):
                        var_name = tokens[i + 1]
                        self._create_variable(var_name)
                        i += 2
                    else:
                        print("Error: nombre de variable faltante")
                        i += 1

                elif token_lower == 'constant':
                    if i + 1 < len(tokens) and len(self.stack) >= 1:
                        const_name = tokens[i + 1]
                        const_value = self.stack.pop()
                        self._create_constant(const_name, const_value)
                        i += 2
                    else:
                        print("Error: nombre de constante faltante o stack vacío")
                        i += 1

                elif token_lower == 'value':
                    if i + 1 < len(tokens) and len(self.stack) >= 1:
                        value_name = tokens[i + 1]
                        value_value = self.stack.pop()
                        self._create_value(value_name, value_value)
                        i += 2
                    else:
                        print("Error: nombre de value faltante o stack vacío")
                        i += 1

                elif token_lower == 'to':
                    if i + 1 < len(tokens) and len(self.stack) >= 1:
                        value_name = tokens[i + 1]
                        new_value = self.stack.pop()
                        self._set_value(value_name, new_value)
                        i += 2
                    else:
                        print("Error: nombre de value faltante o stack vacío para to")
                        i += 1

                elif token_lower == 'mvariable':
                    if i + 1 < len(tokens):
                        var_name = tokens[i + 1]
                        initial_value = 0
                        if len(self.stack) >= 1:
                            initial_value = self.stack.pop()
                        self._create_memory_variable(var_name, initial_value)
                        i += 2
                    else:
                        print("Error: nombre de mvariable faltante")
                        i += 1

                elif token_lower == 'cr':
                    print()
                    i += 1

                elif token_lower == '."':
                    if i + 1 < len(tokens):
                        print(tokens[i + 1], end=' ')
                        sys.stdout.flush()
                        i += 2
                    else:
                        print("Error: cadena faltante después de .\"")
                        i += 1

                elif token_lower == 's"':
                    if i + 1 < len(tokens):
                        self.stack.append(tokens[i + 1])
                        i += 2
                    else:
                        print("Error: cadena faltante después de s\"")
                        i += 1

                elif token_lower == 'evaluate':
                    self._evaluate()
                    i += 1

                elif token_lower == 'do':
                    # Ejecutar DO/LOOP en modo inmediato
                    loop_depth = 1
                    loop_end = -1
                    loop_type = None

                    # Encontrar el LOOP o +LOOP correspondiente
                    for j in range(i + 1, len(tokens)):
                        if tokens[j] == 'do':
                            loop_depth += 1
                        elif tokens[j] in ('loop', '+loop'):
                            loop_depth -= 1
                            if loop_depth == 0:
                                loop_end = j
                                loop_type = tokens[j]
                                break

                    if loop_end == -1:
                        print("Error: DO sin LOOP o +LOOP correspondiente")
                        i += 1
                    else:
                        # Capturar start y limit ANTES de compilar (compilar limpia la pila)
                        if len(self.stack) < 2:
                            print("Error: DO requiere dos valores en la pila (límite inicio)")
                            i = loop_end + 1
                        else:
                            start = self.stack.pop()
                            limit = self.stack.pop()
                            
                            # Extraer cuerpo del bucle
                            loop_body_tokens = tokens[i+1:loop_end]
                            # Compilar el cuerpo del bucle para ejecución
                            compiled_loop_body = self._compile_inline_definition(loop_body_tokens)

                            # Ejecutar el bucle con los valores capturados
                            # Restaurar start/limit a la pila para _execute_do_loop
                            self.stack.append(limit)
                            self.stack.append(start)
                            self._execute_do_loop(compiled_loop_body, loop_type == '+loop')
                            i = loop_end + 1

                # Si estamos en modo de interpretación o en modo bracket temporal y encontramos un token que no es especial
                elif token not in ('[', ']', 'if', 'else', 'then', 'do', 'loop', '+loop', 'begin', 'until', 'again', 'while', 'repeat'):
                    # Si estamos en bracket_mode durante compilación, ejecutar inmediatamente
                    if self._bracket_mode and self._defining:
                        self._execute_token_runtime(token)
                        i += 1
                    else:
                        self._execute_token(token)
                        # Sincronizar i basado en si _execute_token consumió tokens adicionales
                        if self._input_index > i:
                            i = self._input_index + 1
                        else:
                            i += 1
                else: # Si es un marcador de control en modo interpretación (ej: if, begin, etc.)
                    i += 1

    def _tick_interpret(self, word_name):
        if word_name in self.words:
            self.stack.append(('word', word_name, self.words[word_name]))
        elif word_name in self.immediate_words:
            self.stack.append(('immediate', word_name, self.immediate_words[word_name]))
        elif word_name in self.variables:
            # Empuja la función que empuja el nombre de la variable
            self.stack.append(('variable', word_name, self.words[word_name]))
        elif word_name in self.constants:
             # Empuja la función que empuja el valor de la constante
            self.stack.append(('constant', word_name, self.words[word_name]))
        elif word_name in self.values:
             # Empuja la función que empuja el valor del value
            self.stack.append(('value', word_name, self.words[word_name]))
        else:
            print(f"Error: palabra '{word_name}' no definida")
            self.stack.append(word_name)

    def _create_memory_variable(self, name, initial_value=0):
        if self.here + 1 >= self._memory_size: # +1 para asegurar espacio
            print("Error: memoria insuficiente para crear variable")
            return False

        address = self.here
        self.memory[address] = initial_value
        self.here += 1

        def push_variable_address():
            self.stack.append(address)

        self.words[name] = push_variable_address
        self._definition_order.append(('memory_variable', name))

        print(f"Variable '{name}' creada en memoria @{address} = {initial_value}")
        return True

    def _process_conditionals(self, definition):
        """Procesa estructuras IF/THEN/ELSE en la definición y las convierte en tuplas especiales"""
        processed = []
        i = 0

        while i < len(definition):
            item = definition[i]

            if isinstance(item, tuple): # Si ya es una tupla procesada (literal, tick, etc.)
                processed.append(item)
                i += 1
            elif item == 'if':
                # Encontrar el THEN correspondiente (y posiblemente ELSE)
                depth = 1
                else_pos = -1
                then_pos = -1

                for j in range(i + 1, len(definition)):
                    sub_item = definition[j]
                    if sub_item == 'if':
                        depth += 1
                    elif sub_item == 'else' and depth == 1:
                        else_pos = j
                    elif sub_item == 'then':
                        depth -= 1
                        if depth == 0:
                            then_pos = j
                            break

                if then_pos == -1:
                    print("Error: IF sin THEN correspondiente")
                    processed.append(item) # Dejar 'if' como está si no hay THEN
                    i += 1
                else:
                    # Extraer ramas
                    if else_pos != -1:
                        # IF...ELSE...THEN
                        true_branch_tokens = definition[i+1:else_pos]
                        false_branch_tokens = definition[else_pos+1:then_pos]
                        # Procesar recursivamente las ramas
                        true_branch = self._process_conditionals(true_branch_tokens)
                        false_branch = self._process_conditionals(false_branch_tokens)
                        processed.append(('if', true_branch, false_branch))
                    else:
                        # IF...THEN (sin ELSE)
                        true_branch_tokens = definition[i+1:then_pos]
                        # Procesar recursivamente la rama
                        true_branch = self._process_conditionals(true_branch_tokens)
                        processed.append(('if', true_branch, None))

                    i = then_pos + 1 # Saltar hasta después del THEN
            else:
                # Conservar otros elementos (palabras, etc.)
                processed.append(item)
                i += 1

        return processed

    def _process_do_loops(self, definition):
        """Procesa estructuras DO/LOOP en la definición y las convierte en tuplas especiales"""
        processed = []
        i = 0

        while i < len(definition):
            item = definition[i]
            if isinstance(item, tuple): # Si ya es una tupla procesada
                processed.append(item)
                i += 1
            elif item == 'do':
                # Encontrar el LOOP o +LOOP correspondiente
                loop_depth = 1
                loop_end = -1
                loop_type = None

                for j in range(i + 1, len(definition)):
                    sub_item = definition[j]
                    if sub_item == 'do':
                        loop_depth += 1
                    elif sub_item in ('loop', '+loop'):
                        loop_depth -= 1
                        if loop_depth == 0:
                            loop_end = j
                            loop_type = sub_item
                            break

                if loop_end == -1:
                    print("Error: DO sin LOOP o +LOOP correspondiente")
                    processed.append(item) # Dejar 'do' si no hay cierre
                    i += 1
                else:
                    # Extraer cuerpo del bucle
                    loop_body_tokens = definition[i+1:loop_end]
                    # Procesar recursivamente por si hay bucles anidados o condicionales
                    processed_loop_body = self._process_conditionals(loop_body_tokens)
                    processed_loop_body = self._process_do_loops(processed_loop_body) # Recursión para bucles anidados

                    # Crear tupla do_loop: (tipo, cuerpo, es_+loop)
                    is_plusloop = (loop_type == '+loop')
                    processed.append(('do_loop', processed_loop_body, is_plusloop))
                    i = loop_end + 1 # Saltar hasta después del LOOP/+LOOP
            else:
                # Conservar otros elementos
                processed.append(item)
                i += 1

        return processed

    def _process_begin_loops(self, definition):
        """Procesa estructuras BEGIN/UNTIL/AGAIN/WHILE/REPEAT y las convierte en tuplas especiales"""
        processed = []
        i = 0

        while i < len(definition):
            item = definition[i]
            if isinstance(item, tuple): # Si ya es una tupla procesada
                processed.append(item)
                i += 1
            elif item == 'begin':
                # Encontrar el final del bucle (UNTIL, AGAIN, o REPEAT)
                begin_depth = 1
                loop_end = -1
                loop_type = None
                while_pos = -1 # Posición del WHILE si existe
                while i + 1 < len(definition): # Iterar hasta el final de la definición
                    j = i + 1
                    sub_item = definition[j]
                    if sub_item == 'begin':
                        begin_depth += 1
                    elif sub_item in ('until', 'again', 'repeat'):
                        if begin_depth == 1: # Cierre del BEGIN actual
                            loop_end = j
                            loop_type = sub_item
                            break
                        else: # Es un BEGIN anidado, solo decrementamos la profundidad
                            begin_depth -= 1
                    elif sub_item == 'while' and begin_depth == 1 and while_pos == -1:
                        # Encontrado WHILE en el nivel superior
                        while_pos = j
                    i += 1 # Avanzar el índice de la definición externa
                else: # Si el bucle while termina sin break (no encontró cierre)
                    print("Error: BEGIN sin UNTIL, AGAIN o REPEAT correspondiente")
                    processed.append(item) # Dejar 'begin' si no hay cierre
                    continue # Pasar al siguiente item

                if loop_end == -1:
                    # Esto no debería ocurrir si el bucle while anterior funcionó correctamente
                    print("Error interno: No se encontró el final del bucle BEGIN")
                    processed.append(item)
                    i += 1
                elif loop_type == 'until':
                    # BEGIN ... UNTIL
                    body_tokens = definition[i+1:loop_end]
                    processed_body = self._process_conditionals(body_tokens) # Procesar condicionales internos
                    processed_body = self._process_do_loops(processed_body) # Procesar bucles DO/LOOP internos
                    processed_body = self._process_begin_loops(processed_body) # Recursión para bucles BEGIN anidados
                    processed.append(('begin_until', processed_body))
                    i = loop_end + 1
                elif loop_type == 'again':
                    # BEGIN ... AGAIN (bucle infinito)
                    body_tokens = definition[i+1:loop_end]
                    processed_body = self._process_conditionals(body_tokens)
                    processed_body = self._process_do_loops(processed_body)
                    processed_body = self._process_begin_loops(processed_body)
                    processed.append(('begin_again', processed_body))
                    i = loop_end + 1
                elif loop_type == 'repeat':
                    # BEGIN ... WHILE ... REPEAT
                    if while_pos == -1:
                        print("Error: BEGIN ... REPEAT sin WHILE")
                        processed.append(item) # Dejar 'begin' si falta WHILE
                        i += 1
                    else:
                        body_before_while_tokens = definition[i+1:while_pos]
                        body_after_while_tokens = definition[while_pos+1:loop_end]

                        # Procesar recursivamente ambas partes
                        processed_before = self._process_conditionals(body_before_while_tokens)
                        processed_before = self._process_do_loops(processed_before)
                        processed_before = self._process_begin_loops(processed_before)

                        processed_after = self._process_conditionals(body_after_while_tokens)
                        processed_after = self._process_do_loops(processed_after)
                        processed_after = self._process_begin_loops(processed_after)

                        processed.append(('begin_while_repeat', processed_before, processed_after))
                        i = loop_end + 1
                else:
                    # Si no es ninguno de los casos anteriores, solo añadir el item
                    processed.append(item)
                    i += 1
            else:
                # Conservar otros elementos
                processed.append(item)
                i += 1

        return processed

    def _compile_inline_definition(self, tokens):
        """Compila una lista de tokens como si fuera una definición interna
           para su uso inmediato (ej. cuerpo de bucle).
           Retorna una lista de tuplas procesadas.
        """
        # Simular el proceso de compilación para los tokens del cuerpo
        temp_definition = []
        temp_i = 0
        while temp_i < len(tokens):
            token = tokens[temp_i]

            if token == 'if':
                temp_definition.append('if')
            elif token == 'else':
                temp_definition.append('else')
            elif token == 'then':
                temp_definition.append('then')
            elif token == 'do':
                temp_definition.append('do')
            elif token == 'loop':
                temp_definition.append('loop')
            elif token == '+loop':
                temp_definition.append('+loop')
            elif token == 'begin':
                temp_definition.append('begin')
            elif token == 'until':
                temp_definition.append('until')
            elif token == 'again':
                temp_definition.append('again')
            elif token == 'while':
                temp_definition.append('while')
            elif token == 'repeat':
                temp_definition.append('repeat')
            elif token == 'postpone':
                if temp_i + 1 < len(tokens):
                    next_word = tokens[temp_i + 1]
                    temp_definition.append(('compile', next_word))
                    temp_i += 1
                else:
                    print("Error: falta palabra después de postpone en definición inline")
            elif token == '."':
                 if temp_i + 1 < len(tokens):
                    temp_definition.append(('print-string', tokens[temp_i + 1]))
                    temp_i += 1
                 else:
                    print("Error: cadena faltante después de .\" en definición inline")
            elif token == 's"':
                 if temp_i + 1 < len(tokens):
                    temp_definition.append(('push-string', tokens[temp_i + 1]))
                    temp_i += 1
                 else:
                    print("Error: cadena faltante después de s\" en definición inline")
            elif token == "'":
                if temp_i + 1 < len(tokens):
                    word_name = tokens[temp_i + 1]
                    tick_func = self._compile_tick_definition(word_name)
                    temp_definition.append(('tick', word_name, tick_func))
                    temp_i += 1
                else:
                    print("Error: falta palabra después de ' en definición inline")
            elif token == "[']":
                 if temp_i + 1 < len(tokens):
                    word_name = tokens[temp_i + 1]
                    tick_func = self._compile_tick_definition(word_name)
                    temp_definition.append(('tick', word_name, tick_func))
                    temp_i += 1
                 else:
                    print("Error: falta palabra después de ['] en definición inline")
            elif token == 'literal': # Manejar LITERAL
                if temp_i + 1 < len(tokens):
                    next_token_str = tokens[temp_i + 1]
                    parsed_num = self._parse_number_with_base(next_token_str)
                    if parsed_num is not None:
                        temp_definition.append(('literal', parsed_num))
                        temp_i += 1
                    else:
                        print(f"Error: '{next_token_str}' no es un número válido después de LITERAL")
                else:
                    print("Error: falta número después de LITERAL")

            else:
                # Intentar parsear como literal
                parsed_num = self._parse_number_with_base(token)
                if parsed_num is not None:
                    temp_definition.append(('literal', parsed_num))
                else:
                    # Si no es literal, añadir como string (nombre de palabra)
                    temp_definition.append(token)
            temp_i += 1

        # Procesar estructuras de control después de tokenizar
        processed_definition = self._process_conditionals(temp_definition)
        processed_definition = self._process_do_loops(processed_definition)
        processed_definition = self._process_begin_loops(processed_definition)

        return processed_definition

    def _compile_definition(self):
        # Procesar condicionales, DO/LOOP y BEGIN/UNTIL antes de compilar
        definition = self._current_definition.copy()
        definition = self._process_conditionals(definition)
        definition = self._process_do_loops(definition)
        definition = self._process_begin_loops(definition)

        def compiled():
            # Resetear _exit_flag al iniciar ejecución de palabra
            self._exit_flag = False
            # NO limpiar _loop_stack aquí - causaría problemas con loops anidados
            # Cada DO/LOOP limpia sus propios elementos en su bloque finally

            try:
                i = 0
                while i < len(definition):
                    # Verificar si EXIT fue llamado
                    if self._exit_flag:
                        break

                    item = definition[i]

                    if isinstance(item, tuple):
                        # Manejar tuplas especiales (literales, tick, condicionales, bucles, etc.)
                        if item[0] == 'literal':
                            _, value = item
                            self.stack.append(value)
                            i += 1
                        elif item[0] == 'tick':
                            _, _, tick_func = item
                            tick_func() # Ejecuta la función que empuja ('word', name, func)
                            i += 1
                        elif item[0] == 'do_loop':
                            _, loop_body, is_plusloop = item
                            self._execute_do_loop(loop_body, is_plusloop)
                            i += 1
                        elif item[0] == 'begin_until':
                            _, loop_body = item
                            self._execute_begin_until(loop_body)
                            i += 1
                        elif item[0] == 'begin_again':
                            _, loop_body = item
                            self._execute_begin_again(loop_body)
                            i += 1
                        elif item[0] == 'begin_while_repeat':
                            _, body_before, body_after = item
                            self._execute_begin_while_repeat(body_before, body_after)
                            i += 1
                        elif item[0] == 'if':
                            _, true_branch, false_branch = item
                            if not self.stack:
                                print("Error: IF requiere un valor en la pila")
                                i += 1
                                continue
                            condition = self.stack.pop()
                            # En Forth, 0 es falso, cualquier otro valor es verdadero
                            if condition != 0:
                                self._execute_branch(true_branch)
                            elif false_branch is not None:
                                self._execute_branch(false_branch)
                            i += 1
                        elif item[0] == 'compile':
                            # POSTPONE: compilar la palabra en la definición actual
                            _, word_to_compile = item
                            # Re-ejecutar el tokenizador para la palabra a compilar
                            # y añadirla a la definición actual
                            compiled_token = self._compile_inline_definition([word_to_compile])
                            if compiled_token:
                                # Insertar los tokens compilados en la definición actual
                                # self._current_definition ya no se usa aquí, trabajamos sobre 'definition'
                                # La inserción debe ocurrir en la posición correcta de la ejecución
                                # Por ahora, asumimos que esto se maneja adecuadamente en _execute_branch
                                # O se compila como una llamada a _execute_token con la palabra
                                for compiled_item in compiled_token:
                                     # Si es una sola palabra, la añadimos directamente
                                     if isinstance(compiled_item, str):
                                        self._execute_token(compiled_item) # Ejecutarla inmediatamente
                                     else: # Si es una tupla (literal, tick, etc.), ejecutarla
                                         # Esto es complejo, para POSTPONE usualmente se compila la palabra
                                         # tal cual, así que la llamamos directamente
                                         if compiled_item[0] == 'tick':
                                             _, _, tick_func = compiled_item
                                             tick_func()
                                         # Otros casos como 'literal' o 'compile' anidado requerirían
                                         # una lógica más elaborada para insertarlos en la ejecución
                                         # Por simplicidad, asumimos que POSTPONE se usa con palabras simples
                                         else:
                                              print(f"Advertencia: POSTPONE con item complejo '{compiled_item[0]}' no completamente soportado en ejecución")
                            i += 1
                        elif item[0] == 'runtime-create':
                            # CREATE runtime - leer nombre del input stream
                            if self._input_index + 1 < len(self._input_tokens):
                                self._input_index += 1
                                name = self._input_tokens[self._input_index]

                                # Reservar espacio en memoria
                                if self.here >= self._memory_size:
                                    print("Error: memoria insuficiente para CREATE")
                                else:
                                    created_address = self.here
                                    # Crear función que empuje la dirección
                                    def push_address(addr=created_address):
                                        self.stack.append(addr)

                                    self.words[name] = push_address
                                    self._definition_order.append(('created', name))
                                    self._last_created_word = name
                                    self._last_created_address = created_address
                                    self.here += 1 # Incrementar here para la dirección
                            else:
                                print("Error: falta nombre después de CREATE")
                            i += 1
                        elif item[0] == 'print-string':
                            _, text = item
                            print(text, end=' ')
                            sys.stdout.flush()
                            i += 1
                        elif item[0] == 'push-string':
                            _, text = item
                            self.stack.append(text)
                            i += 1
                        elif item[0] == 'does>':
                            # DOES> modifica la última palabra creada con CREATE
                            if not self._last_created_word:
                                print("Error: DOES> requiere una palabra CREATE previa")
                                i += 1
                                continue

                            # El resto de la definición es el nuevo comportamiento
                            does_code = definition[i+1:]
                            word_name = self._last_created_word
                            addr = self._last_created_address # Dirección original

                            # Crear nueva función para la palabra
                            def new_behavior(code=does_code, address=addr, fw=self):
                                # Primero empujar la dirección
                                fw.stack.append(address)
                                # Luego ejecutar el código DOES>
                                # Compilar el cuerpo de DOES>
                                compiled_does_code = fw._compile_inline_definition(code)
                                fw._execute_branch(compiled_does_code) # Ejecutar el código compilado

                            # Reemplazar la palabra creada
                            if word_name in self.words:
                                self.words[word_name] = new_behavior
                                # Actualizar registro si es necesario (aunque CREATE ya está registrado)
                                # Guardar el código fuente original de DOES> si lo hubiera
                                source_code_does = ' '.join(tokens[self._definition_start_index:i+1]) # Aproximado
                                if word_name in self._definition_source:
                                    self._definition_source[word_name] = source_code_does

                            # Salir del loop, ya procesamos todo el cuerpo de DOES>
                            break
                        else:
                            i += 1
                    elif isinstance(item, int) or isinstance(item, float):
                        # Literales numéricos compilados (ej: de [char])
                        self.stack.append(item)
                        i += 1
                    elif isinstance(item, str):
                        token = item
                        # Ejecutar palabras normales o inmediatas
                        self._execute_token(token)
                        i += 1
                    else:
                        i += 1
            finally:
                # Siempre resetear flags al terminar ejecución de palabra
                self._exit_flag = False
                # NO limpiar _loop_stack aquí - cada DO/LOOP limpia sus propios elementos
                # Limpiar todo el stack causaría problemas con loops anidados

        return compiled

    def _execute_do_loop(self, loop_body, is_plusloop):
        """Ejecuta un bucle DO/LOOP compilado"""
        if len(self.stack) < 2:
            print("Error: DO requiere dos valores en la pila (límite inicio)")
            return

        start = self.stack.pop()
        limit = self.stack.pop()

        # Guardar índice y límite en loop_stack
        self._loop_stack.append(limit)
        self._loop_stack.append(start)
        self._leave_flag = False # Resetear flag LEAVE para cada bucle

        try:
            while True:
                # Verificar condición de salida
                current_index = self._loop_stack[-1]
                current_limit = self._loop_stack[-2]

                # Condición de salida: índice >= límite O LEAVE fue llamado O EXIT fue llamado
                if current_index >= current_limit or self._leave_flag or self._exit_flag:
                    break

                # Ejecutar cuerpo del bucle
                self._execute_branch(loop_body)

                # Si EXIT fue llamado dentro del cuerpo, salir del bucle
                if self._exit_flag:
                    break

                # Incrementar índice
                if is_plusloop:
                    if not self.stack:
                        print("Error: +LOOP requiere valor de incremento en la pila")
                        break
                    inc_value = self.stack.pop()
                    self._loop_stack[-1] += inc_value
                else: # LOOP
                    self._loop_stack[-1] += 1
        finally:
            # Limpiar loop_stack al salir del bucle
            if len(self._loop_stack) >= 2:
                self._loop_stack.pop()
                self._loop_stack.pop()
            self._leave_flag = False # Asegurar que LEAVE se resetee

    def _execute_begin_until(self, loop_body):
        """Ejecuta un bucle BEGIN ... UNTIL (ejecuta hasta que condición sea TRUE)"""
        while True:
            # Ejecutar el cuerpo del bucle token por token
            self._execute_branch(loop_body)

            # Si EXIT fue llamado dentro del cuerpo, salir
            if self._exit_flag:
                break

            # Verificar condición en el tope de la pila
            if not self.stack:
                print("Error: UNTIL requiere un valor en la pila")
                break

            condition = self.stack.pop()
            # UNTIL sale cuando la condición es TRUE (!=0)
            if condition != 0:
                break

    def _execute_begin_again(self, loop_body):
        """Ejecuta un bucle BEGIN ... AGAIN (bucle infinito, solo sale con LEAVE o EXIT)"""
        iteration_count = 0
        max_iterations = 1000000  # límite de seguridad para evitar cuelgues

        while True:
            iteration_count += 1
            if iteration_count > max_iterations:
                print(f"Error: BEGIN...AGAIN excedió {max_iterations} iteraciones (posible bucle infinito)")
                break

            # Ejecutar el cuerpo del bucle
            self._execute_branch(loop_body)

            # Salir si EXIT fue llamado
            if self._exit_flag:
                break
            # Salir si LEAVE fue llamado (esto debería ser manejado por el cuerpo del bucle si es necesario)
            # Por ahora, solo verificamos EXIT

    def _execute_begin_while_repeat(self, body_before_while, body_after_while):
        """Ejecuta un bucle BEGIN ... WHILE ... REPEAT

        Ejecuta body_before_while, luego verifica condición
        Si es TRUE, ejecuta body_after_while y repite
        Si es FALSE, sale del bucle
        """
        while True:
            # Ejecutar código antes de WHILE
            self._execute_branch(body_before_while)

            # Si EXIT fue llamado dentro de body_before_while, salir
            if self._exit_flag:
                break

            # Verificar condición en el tope de la pila
            if not self.stack:
                print("Error: WHILE requiere un valor en la pila")
                break

            condition = self.stack.pop()
            # WHILE continúa si la condición es TRUE (!=0)
            if condition == 0:
                break

            # Ejecutar código después de WHILE (antes de REPEAT)
            self._execute_branch(body_after_while)

            # Si EXIT fue llamado dentro de body_after_while, salir
            if self._exit_flag:
                break

    def _execute_branch(self, branch):
        """Ejecuta una rama de IF/THEN/ELSE o cuerpo de bucle compilada"""
        i = 0
        while i < len(branch):
            token = branch[i]

            if isinstance(token, tuple):
                # Manejar tuplas especiales (literales, tick, condicionales, bucles, etc.)
                if token[0] == 'literal':
                    _, value = token
                    self.stack.append(value)
                elif token[0] == 'tick':
                    _, _, tick_func = token
                    tick_func()
                elif token[0] == 'do_loop':
                    _, nested_body, is_plusloop = token
                    self._execute_do_loop(nested_body, is_plusloop)
                elif token[0] == 'begin_until':
                    _, loop_body = token
                    self._execute_begin_until(loop_body)
                elif token[0] == 'begin_again':
                    _, loop_body = token
                    self._execute_begin_again(loop_body)
                elif token[0] == 'begin_while_repeat':
                    _, body_before, body_after = token
                    self._execute_begin_while_repeat(body_before, body_after)
                elif token[0] == 'if':
                    # IF anidado
                    _, true_branch, false_branch = token
                    if not self.stack:
                        print("Error: IF requiere un valor en la pila")
                        i += 1
                        continue
                    condition = self.stack.pop()
                    if condition != 0:
                        self._execute_branch(true_branch)
                    elif false_branch is not None:
                        self._execute_branch(false_branch)
                elif token[0] == 'compile':
                    # POSTPONE: Ejecutar la palabra compilada
                    _, word_to_compile = token
                    # Re-ejecutar el tokenizador para la palabra a compilar
                    # y añadirla a la definición actual
                    compiled_token = self._compile_inline_definition([word_to_compile])
                    if compiled_token:
                        for compiled_item in compiled_token:
                            if isinstance(compiled_item, str):
                                self._execute_token(compiled_item)
                            else: # Tupla ('literal', valor), etc.
                                if compiled_item[0] == 'tick':
                                    _, _, tick_func = compiled_item
                                    tick_func()
                                elif compiled_item[0] == 'literal':
                                    self.stack.append(compiled_item[1])
                                # Otros casos como 'compile' anidado no se manejan aquí
                                else:
                                    print(f"Advertencia: POSTPONE con item complejo '{compiled_item[0]}' no completamente soportado en ejecución")
                    i += 1 # Avanzar i después de procesar el compile
                    continue # Continuar el bucle while
                elif token[0] == 'print-string':
                    _, text = token
                    print(text, end=' ')
                    sys.stdout.flush()
                elif token[0] == 'push-string':
                    _, text = token
                    self.stack.append(text)
                i += 1
            elif isinstance(token, int) or isinstance(token, float):
                # Literales numéricos
                self.stack.append(token)
                i += 1
            elif isinstance(token, str):
                # Manejar char y [char] (si se compilaron como strings)
                if token in ('char', '[char]'):
                    # Esto debería ser manejado por la tupla 'literal', pero como fallback:
                    if i + 1 < len(branch):
                        next_token = branch[i + 1]
                        if isinstance(next_token, str) and len(next_token) > 0:
                            self.stack.append(ord(next_token[0]))
                        else:
                            print("Error: token inválido después de char")
                        i += 2
                    else:
                        print(f"Error: falta carácter después de {token}")
                        i += 1
                else:
                    # Ejecutar palabras normales o inmediatas
                    self._execute_token(token)
                    i += 1
            else:
                i += 1

    # DSL fluido
    def __call__(self, *values):
        self.stack.extend(values)
        return self

    def push(self, *values):
        self.stack.extend(values)
        return self

    def pop(self):
        """Saca y retorna el valor superior de la pila (TOS)"""
        if self.stack:
            return self.stack.pop()
        else:
            raise IndexError("Stack underflow: no hay elementos en la pila")

    def cls(self):
        """Limpia la pantalla (equivalente a page en Forth)"""
        self._page()
        return self

    def constant(self, name, value=None):
        """DSL para crear constantes Forth"""
        if value is not None:
            self.stack.append(value)

        if not self.stack:
            print(f"Error: no hay valor para la constante '{name}'")
            return self

        const_value = self.stack.pop()
        self._create_constant(name, const_value)
        return self

    def __getattr__(self, name):
        if name in self.words:
            def wrapper(*args):
                if args:
                    self.stack.extend(args)
                self.words[name]()
                return self
            return wrapper
        elif name in self.immediate_words: # Permitir llamar palabras inmediatas directamente
            def wrapper(*args):
                if args:
                    self.stack.extend(args)
                self.immediate_words[name]()
                return self
            return wrapper
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def _save_words(self):
        """Guarda todas las definiciones de usuario en un archivo
        Uso: s" filename.fth" SAVE  o  s" carpeta/nombre.fth" SAVE
        """
        if len(self.stack) < 1:
            print("Error: SAVE requiere nombre de archivo en la pila")
            return

        filename = self.stack.pop()
        if not isinstance(filename, str):
            print(f"Error: SAVE requiere un string, recibió {type(filename)}")
            return

        # Sanitizar el path
        try:
            sanitized = self._sanitize_save_path(filename)
        except ValueError as e:
            print(f"Error: ruta inválida '{filename}': {e}")
            self.stack.append(filename)
            return

        try:
            # Crear carpetas si es necesario
            dir_path = os.path.dirname(sanitized)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            with open(sanitized, 'w', encoding='utf-8') as f:
                f.write("\\ Definiciones Forth guardadas automáticamente\n")
                f.write(f"\\ Archivo: {sanitized}\n\n")

                # Variables del sistema que no deben guardarse
                system_vars = {'base', 'state'}
                
                for def_type, name in self._definition_order:
                    # Saltar variables del sistema
                    if name in system_vars:
                        continue
                    if def_type == 'word' and name in self._definition_source:
                        # Palabra definida con :
                        f.write(f"{self._definition_source[name]}\n")
                    elif def_type == 'immediate' and name in self._definition_source:
                        # Palabra inmediata
                        f.write(f"{self._definition_source[name]}\n")
                    elif def_type == 'variable':
                        # Variable estándar
                        f.write(f"variable {name}\n")
                    elif def_type == 'memory_variable':
                         # Variable en memoria
                         if name in self.words: # Check if word exists
                            addr_val = self.words[name]() # Get address
                            val = self.memory[addr_val] if addr_val < self._memory_size else '?'
                            f.write(f"{val} mvariable {name}\n") # Store value during load
                    elif def_type == 'constant' and name in self.constants:
                        # Constante
                        f.write(f"{self.constants[name]} constant {name}\n")
                    elif def_type == 'value' and name in self.values:
                        # Value
                        f.write(f"{self.values[name]} value {name}\n")
                    elif def_type == 'created' and name in self._definition_source:
                        # Palabras CREATE/DOES>
                        f.write(f"{self._definition_source[name]}\n")

                # Contar solo definiciones de usuario (excluyendo variables del sistema)
                user_defs = len([n for _, n in self._definition_order if n not in system_vars])
                f.write(f"\n\\ Fin del archivo - {user_defs} definiciones guardadas\n")

            user_defs = len([n for _, n in self._definition_order if n not in {'base', 'state'}])
            print(f"✓ {user_defs} definiciones guardadas en '{sanitized}'")

        except Exception as e:
            print(f"Error al guardar archivo: {e}")
            self.stack.append(filename)  # Devolver el nombre a la pila

    def _load_file(self):
        """Carga y ejecuta un archivo de definiciones Forth
        Uso: s" filename.fth" LOAD  o  s" carpeta/nombre.fth" LOAD
        """
        if len(self.stack) < 1:
            print("Error: LOAD requiere nombre de archivo en la pila")
            return

        filename = self.stack.pop()
        if not isinstance(filename, str):
            print(f"Error: LOAD requiere un string, recibió {type(filename)}")
            return

        # Sanitizar el path
        try:
            sanitized = self._sanitize_save_path(filename)
        except ValueError as e:
            print(f"Error: ruta inválida '{filename}': {e}")
            self.stack.append(filename)
            return

        try:
            with open(sanitized, 'r', encoding='utf-8') as f:
                code = f.read()

            # Ejecutar el código cargado
            print(f"Cargando '{sanitized}'...")
            self.execute(code)
            print(f"✓ Archivo '{sanitized}' cargado exitosamente")

        except FileNotFoundError:
            cwd = os.getcwd()
            print(f"Error: archivo '{sanitized}' no encontrado")
            print(f"Directorio actual: {cwd}")
            # Mostrar archivos .fth disponibles
            try:
                fth_files = [f for f in os.listdir(cwd) if f.endswith('.fth')]
                if fth_files:
                    print(f"Archivos .fth disponibles: {', '.join(fth_files)}")
                else:
                    print("No hay archivos .fth en el directorio actual")
            except:
                pass
            self.stack.append(filename)
        except Exception as e:
            print(f"Error al cargar archivo: {e}")
            self.stack.append(filename)

    def _rmsave(self):
        """Elimina un archivo .fth
        Uso: s" filename.fth" RMSAVE  o  s" carpeta/nombre.fth" RMSAVE
        """
        if len(self.stack) < 1:
            print("Error: RMSAVE requiere nombre de archivo en la pila")
            print("Uso: s\" archivo.fth\" rmsave")
            return

        filename = self.stack.pop()
        if not isinstance(filename, str):
            print(f"Error: RMSAVE requiere un string, recibió {type(filename)}")
            return

        # Sanitizar el path
        try:
            sanitized = self._sanitize_save_path(filename)
        except ValueError as e:
            print(f"Error: ruta inválida '{filename}': {e}")
            self.stack.append(filename)
            return

        # Verificar que el archivo existe
        if not os.path.exists(sanitized):
            cwd = os.getcwd()
            print(f"Error: archivo '{sanitized}' no encontrado")
            # Mostrar archivos .fth disponibles
            try:
                fth_files = [f for f in os.listdir(cwd) if f.endswith('.fth')]
                if fth_files:
                    print(f"Archivos .fth disponibles: {', '.join(fth_files)}")
            except:
                pass
            self.stack.append(filename)
            return

        try:
            # Eliminar el archivo
            os.remove(sanitized)
            print(f"✓ Archivo '{sanitized}' eliminado")

            # Limpiar directorios vacíos si era un path con carpetas
            dir_path = os.path.dirname(sanitized)
            if dir_path and os.path.isdir(dir_path):
                try:
                    # Intentar eliminar directorio si está vacío
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except OSError:
                    pass  # Ignorar errores (directorio no vacío, etc.)

        except Exception as e:
            print(f"Error eliminando '{sanitized}': {e}")
            self.stack.append(filename)

    def _pwd(self):
        """Muestra el directorio de trabajo actual"""
        import os
        print(f"Directorio actual: {os.getcwd()}")

class MathForth(Forth):
    def __init__(self):
        super().__init__()
        self._register_math_words()

    def _register_math_words(self):
        self.words['**'] = self._power
        self.words['mod'] = self._mod
        self.words['abs'] = self._abs
        self.words['negate'] = self._negate

    def _power(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a ** b)

    def _mod(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a % b)

    def _abs(self):
        if self.stack:
            self.stack.append(abs(self.stack.pop()))

    def _negate(self):
        if self.stack:
            self.stack.append(-self.stack.pop())

class ExtendedMathForth(MathForth):
    def __init__(self):
        super().__init__()
        self._register_extended_math()

    def _register_extended_math(self):
        self.words['sin'] = self._sin
        self.words['cos'] = self._cos
        self.words['tan'] = self._tan
        self.words['asin'] = self._asin
        self.words['acos'] = self._acos
        self.words['atan'] = self._atan
        self.words['log'] = self._log
        self.words['ln'] = self._ln
        self.words['exp'] = self._exp
        self.words['sqrt'] = self._sqrt
        self.words['pi'] = self._pi
        self.words['e'] = self._e
        self.words['floor'] = self._floor
        self.words['ceil'] = self._ceil
        self.words['round'] = self._round
        self.words['max'] = self._max
        self.words['min'] = self._min
        self.words['and'] = self._and
        self.words['or'] = self._or
        self.words['not'] = self._not
        self.words['xor'] = self._xor
        self.words['='] = self._equal
        self.words['<>'] = self._not_equal
        self.words['<'] = self._less
        self.words['>'] = self._greater
        self.words['<='] = self._less_equal
        self.words['>='] = self._greater_equal
        self.words['lshift'] = self._lshift
        self.words['rshift'] = self._rshift
        self.words['invert'] = self._invert

    def _sin(self):
        if self.stack:
            self.stack.append(math.sin(self.stack.pop()))

    def _cos(self):
        if self.stack:
            self.stack.append(math.cos(self.stack.pop()))

    def _tan(self):
        if self.stack:
            self.stack.append(math.tan(self.stack.pop()))

    def _asin(self):
        if self.stack:
            self.stack.append(math.asin(self.stack.pop()))

    def _acos(self):
        if self.stack:
            self.stack.append(math.acos(self.stack.pop()))

    def _atan(self):
        if self.stack:
            self.stack.append(math.atan(self.stack.pop()))

    def _log(self):
        if self.stack:
            self.stack.append(math.log10(self.stack.pop()))

    def _ln(self):
        if self.stack:
            self.stack.append(math.log(self.stack.pop()))

    def _exp(self):
        if self.stack:
            self.stack.append(math.exp(self.stack.pop()))

    def _sqrt(self):
        if self.stack:
            value = self.stack.pop()
            if value >= 0:
                self.stack.append(math.sqrt(value))
            else:
                print("Error: raíz cuadrada de número negativo")
                self.stack.append(value)

    def _pi(self):
        self.stack.append(math.pi)

    def _e(self):
        self.stack.append(math.e)

    def _floor(self):
        if self.stack:
            self.stack.append(math.floor(self.stack.pop()))

    def _ceil(self):
        if self.stack:
            self.stack.append(math.ceil(self.stack.pop()))

    def _round(self):
        if self.stack:
            self.stack.append(round(self.stack.pop()))

    def _max(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(max(a, b))

    def _min(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(min(a, b))

    def _and(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a and b else 0)

    def _or(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a or b else 0)

    def _not(self):
        if self.stack:
            self.stack.append(0 if self.stack.pop() else 1)

    def _xor(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if bool(a) != bool(b) else 0)

    def _equal(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a == b else 0)

    def _not_equal(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a != b else 0)

    def _less(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a < b else 0)

    def _greater(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a > b else 0)

    def _less_equal(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a <= b else 0)

    def _greater_equal(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(1 if a >= b else 0)

    def _lshift(self):
        if len(self.stack) >= 2:
            n = self.stack.pop()
            x = self.stack.pop()
            self.stack.append(x << n)

    def _rshift(self):
        if len(self.stack) >= 2:
            n = self.stack.pop()
            x = self.stack.pop()
            self.stack.append(x >> n)

    def _invert(self):
        if self.stack:
            self.stack.append(~self.stack.pop())

class StackExtendedForth(ExtendedMathForth):
    def __init__(self):
        super().__init__()
        self._register_stack_operations()

    def _register_stack_operations(self):
        self.words['rot'] = self._rot
        self.words['-rot'] = self._rot_back
        self.words['nip'] = self._nip
        self.words['tuck'] = self._tuck
        self.words['pick'] = self._pick
        self.words['roll'] = self._roll
        self.words['depth'] = self._depth
        self.words['2dup'] = self._two_dup
        self.words['2drop'] = self._two_drop
        self.words['2swap'] = self._two_swap
        self.words['2over'] = self._two_over

    def _rot(self):
        if len(self.stack) >= 3:
            c, b, a = self.stack.pop(), self.stack.pop(), self.stack.pop()
            self.stack.extend([b, c, a])

    def _rot_back(self):
        if len(self.stack) >= 3:
            c, b, a = self.stack.pop(), self.stack.pop(), self.stack.pop()
            self.stack.extend([c, a, b])

    def _nip(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            self.stack.pop()
            self.stack.append(b)

    def _tuck(self):
        if len(self.stack) >= 2:
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.extend([b, a, b])

    def _pick(self):
        if self.stack:
            n = self.stack.pop()
            try:
                n = int(n)
                if 0 <= n < len(self.stack):
                    self.stack.append(self.stack[-(n+1)])
                else:
                    print(f"Error: índice pick fuera de rango: {n}")
                    self.stack.append(n)
            except (ValueError, TypeError):
                print(f"Error: PICK requiere un índice numérico, recibió {type(n)}")
                self.stack.append(n)


    def _roll(self):
        if self.stack:
            n = self.stack.pop()
            try:
                n = int(n)
                if 0 <= n < len(self.stack):
                    idx = len(self.stack) - n - 1
                    value = self.stack.pop(idx)
                    self.stack.append(value)
                else:
                    print(f"Error: índice roll fuera de rango: {n}")
                    self.stack.append(n)
            except (ValueError, TypeError):
                print(f"Error: ROLL requiere un índice numérico, recibió {type(n)}")
                self.stack.append(n)


    def _depth(self):
        self.stack.append(len(self.stack))

    def _two_dup(self):
        if len(self.stack) >= 2:
            b, a = self.stack[-1], self.stack[-2]
            self.stack.extend([a, b])

    def _two_drop(self):
        if len(self.stack) >= 2:
            self.stack.pop()
            self.stack.pop()

    def _two_swap(self):
        if len(self.stack) >= 4:
            d, c, b, a = self.stack.pop(), self.stack.pop(), self.stack.pop(), self.stack.pop()
            self.stack.extend([c, d, a, b])

    def _two_over(self):
        if len(self.stack) >= 4:
            a, b = self.stack[-4], self.stack[-3]
            self.stack.extend([a, b])

class InteractiveForth(StackExtendedForth):
    def __init__(self):
        super().__init__()
        self._register_interactive_words()
        # self._register_byte_words() # Byte words are already registered in Forth base class
        # Auto-cargar palabras primitivas al iniciar
        self._auto_load_code_primitives()
        self._auto_load_forth_primitives()

    def __repr__(self):
        """Evita que Python muestre el objeto cuando se usa DSL en el REPL"""
        return ""

    def _register_interactive_words(self):
        # NOTA: '?' ya está registrado en Forth como fetch-dot (imprime valor de dirección)
        # La ayuda está disponible con el comando 'help' en el REPL
        self.words['immediate-words'] = self._list_immediate_words
        self.words['definitions'] = self.show_definitions
        self.words['mem'] = self._dump
        self.words['reset-mem'] = self._reset_memory
        self.words['memory'] = self._show_memory_status
        self.words['resize-memory'] = self._resize_memory
        self.words['store-string'] = self._store_string_to_memory
        self.words['load-string'] = self._load_string_from_memory
        # char es ahora una palabra especial parseada en execute()
        self.words['tick-demo'] = self._tick_demo

        # Palabras para cambiar BASE
        self.immediate_words['decimal'] = self._set_base_decimal
        self.immediate_words['hex'] = self._set_base_hex
        self.immediate_words['binary'] = self._set_base_binary

    def _register_byte_words(self):
        pass # Ya registrados en Forth

    def _auto_load_code_primitives(self):
        """Auto-carga todas las palabras CODE de extended-code/code-prim/ al iniciar"""
        import os
        code_prim_dir = os.path.join(self._base_dir, 'extended-code', 'code-prim')
        
        if not os.path.exists(code_prim_dir):
            return
        
        # Buscar archivos .py en code-prim
        py_files = []
        try:
            for file in os.listdir(code_prim_dir):
                if file.endswith('.py') and not file.startswith('_'):
                    py_files.append(file[:-3])  # Remover .py
        except:
            return
        
        if not py_files:
            return
        
        # Cargar cada palabra CODE
        loaded = 0
        for word_name in py_files:
            try:
                import_path = f'code-prim/{word_name}'
                self.execute(f'import {import_path}')
                loaded += 1
            except:
                pass
        
        if loaded > 0:
            print(f"✓ Cargadas {loaded} palabra(s) CODE desde code-prim/")

    def _auto_load_forth_primitives(self):
        """Auto-carga forth-prim.fth al iniciar si existe"""
        import os
        forth_prim_file = os.path.join(self._base_dir, 'forth-prim.fth')
        
        if not os.path.exists(forth_prim_file):
            return
        
        # Verificar si el archivo tiene contenido
        try:
            with open(forth_prim_file, 'r') as f:
                content = f.read().strip()
            
            if not content:
                return  # Archivo vacío, no cargar
            
            # Cargar el archivo
            self.stack.append('forth-prim.fth')
            self._load_file()
        except:
            pass

    def _set_base_decimal(self):
        self.variables['base'] = 10
        #print("Base cambiada a Decimal")

    def _set_base_hex(self):
        self.variables['base'] = 16
        #print("Base cambiada a Hexadecimal")

    def _set_base_binary(self):
        self.variables['base'] = 2
        #print("Base cambiada a Binario")

    def _reset_memory(self):
        self.memory = [0] * self._memory_size
        self.here = self._pad_size  # Resetear HERE después de PAD
        print(f"Memoria resetada (HERE en {self.here}, PAD protegido: 0-{self._pad_size-1})")
        return self

    def _show_memory_status(self):
        used = self.here
        free = self._memory_size - self.here
        usage_percent = (used / self._memory_size) * 100 if self._memory_size > 0 else 0
        user_used = self.here - self._pad_size  # Memoria realmente usada por el usuario

        print(f"\n=== ESTADO DE MEMORIA ===")
        print(f"Tamaño total: {self._memory_size} bytes ({self._memory_size//1024}KB)")
        print(f"PAD (protegido): 0-{self._pad_size-1} ({self._pad_size} bytes)")
        print(f"HERE actual: {self.here}")
        print(f"Usada por usuario: {user_used} bytes")
        print(f"Memoria libre: {free} bytes ({free//1024}KB)")
        print(f"Uso total: {usage_percent:.1f}%")

        if free > 0:
            print(f"Puedes almacenar aproximadamente {free} números más")

        return self

    def _resize_memory(self):
        if len(self.stack) < 1:
            print("Error: falta tamaño en KB para resize-memory")
            return

        new_size_kb = self.stack.pop()
        min_size_kb = 1  # Mínimo 1KB para acomodar PAD (256 bytes)
        
        if new_size_kb < min_size_kb:
            print(f"Error: el tamaño debe ser al menos {min_size_kb}KB (para acomodar PAD de {self._pad_size} bytes)")
            self.stack.append(new_size_kb)
            return

        new_size_bytes = new_size_kb * 1024

        old_memory = self.memory
        old_here = self.here

        self.memory = [0] * new_size_bytes
        self._memory_size = new_size_bytes

        copy_count = min(old_here, new_size_bytes)
        for i in range(copy_count):
            self.memory[i] = old_memory[i]

        self.here = min(old_here, new_size_bytes)

        print(f"Memoria redimensionada a {new_size_kb}KB ({new_size_bytes} bytes)")
        print(f"Se preservaron {copy_count} valores")
        self._show_memory_status()

    def _char(self):
        """DSL para char - debe usarse con un carácter"""
        if len(self.stack) < 1:
            print("Error: falta carácter para char")
            return self

        char_str = self.stack.pop()
        if isinstance(char_str, str) and len(char_str) == 1:
            self.stack.append(ord(char_str))
        else:
            print(f"Error: '{char_str}' no es un carácter válido")
            self.stack.append(char_str)
        return self

    def _store_string_to_memory(self):
        if len(self.stack) < 2:
            print("Error: faltan parámetros para store-string")
            return

        address = self.stack.pop()
        string = self.stack.pop()

        if not isinstance(string, str):
            print("Error: el primer parámetro debe ser una cadena")
            self.stack.extend([string, address])
            return

        if self._store_string(string, address):
            print(f"Cadena '{string}' almacenada en dirección {address}")

    def _load_string_from_memory(self):
        if len(self.stack) < 1:
            print("Error: falta dirección para load-string")
            return

        address = self.stack.pop()
        string = self._load_string(address)
        self.stack.append(string)

    def _tick_demo(self):
        print("\n=== DEMOSTRACIÓN ' Y EXECUTE ===")
        print("Stack actual:", self.stack)

        all_words = [w for w in list(self.words.keys()) + list(self.immediate_words.keys())
                    if not w.startswith('_') and w not in ['tick-demo']]
        print("Palabras disponibles:", all_words[:10])

        return self

    def _help(self):
        print("\n" + "=" * 70)
        print("                        FORTH INTERACTIVO")
        print("=" * 70)
        print("Stack:", self.stack)
        if self.rstack:
            print("Return Stack:", self.rstack)
        all_normal_words = list(self.words.keys())
        user_normal_words = [w for w in all_normal_words if not w.startswith('_')]
        immediate_words = list(self.immediate_words.keys())

        print("Palabras normales:", len(user_normal_words))
        print("Palabras inmediatas:", len(immediate_words))
        print("Variables:", list(self.variables.keys()))
        print("Constants:", list(self.constants.keys()))
        print("Values:", list(self.values.keys()))

        print("\n" + "─" * 70)
        print("COMANDOS REPL")
        print("─" * 70)
        print("  bye, help, abort, words, stack, clear, cls, page")
        print("  immediate-words, definitions")
        print("  mem, reset-mem, memory")

        print("\n" + "─" * 70)
        print("MODO NUMÉRICO")
        print("─" * 70)
        print("  decimal     - Establece BASE a 10 (por defecto)")
        print("  hex         - Establece BASE a 16")
        print("  binary      - Establece BASE a 2")
        print("  Ejemplo: HEX 10 20 . → 14 (10 en hex es 20)")
        print("           DECIMAL")

        print("\n" + "─" * 70)
        print("COMENTARIOS")
        print("─" * 70)
        print("  ( comentario )  - Comentarios estándar Forth (ignorados)")
        print("  \\ comentario    - Comentario hasta fin de línea")
        print("  Convención: ( entrada -- salida ) para stack effects")
        print("  Ejemplo: : cuadrado ( n -- n*n ) dup * ;")

        print("\n" + "─" * 70)
        print("INTROSPECCIÓN Y DEBUGGING")
        print("─" * 70)
        print("  see palabra     - Muestra definición de una palabra")
        print("  words           - Lista todas las palabras disponibles")
        print("  .s              - Muestra el contenido de la pila")
        print("  definitions     - Muestra historial de definiciones")
        print("  measure palabra - Mide tiempo de ejecución de una palabra")
        print("                    Pone tiempo en pila y lo muestra en unidades apropiadas")
        print("                    Ejemplo: measure fibonacci  → '5.234 ms' (tiempo en pila)")

        print("\n" + "─" * 70)
        print("ARITMÉTICA Y COMPARACIONES ÚTILES")
        print("─" * 70)
        print("  n 1+            - Incrementa en 1 (n+1)")
        print("  n 1-            - Decrementa en 1 (n-1)")
        print("  n1 n2 /mod      - División con resto (→ resto cociente)")
        print("  n 0=            - Verdadero si n=0 (retorna -1 o 0)")
        print("  n 0<            - Verdadero si n<0 (retorna -1 o 0)")
        print("  n 0>            - Verdadero si n>0 (retorna -1 o 0)")
        print("  Nota: Muy comunes en contadores, índices, bucles y condiciones")
        print("  Flags: -1 = TRUE, 0 = FALSE (estándar Forth)")
        print("  Ejemplo /mod: 17 5 /mod → [2 3] (resto=2, cociente=3)")

        print("\n" + "─" * 70)
        print("MEMORIA BÁSICA")
        print("─" * 70)
        print("  here            - Muestra dirección actual")
        print("  n allot         - Reserva n bytes")
        print("  n buffer        - Reserva n bytes y retorna addr (mantiene n en pila)")
        print("  n ,             - Almacena n en memoria (incrementa here)")
        print("  addr m@         - Lee de dirección (objetos)")
        print("  val addr m!     - Escribe en dirección (objetos)")
        print("  addr @          - Lee entero de dirección")
        print("  val addr !      - Escribe entero en dirección")
        print("  n cells         - Convierte celdas a bytes (n * 4)")
        print("  mvariable       - Crea variable en memoria")

        print("\n" + "─" * 70)
        print("MEMORIA AVANZADA")
        print("─" * 70)
        print("  n addr +!       - Incrementa valor en dirección (+= n)")
        print("  addr ?          - Fetch-dot: muestra valor en dirección")
        print("  count addr fill  - Llena 'count' bytes con 'val'")
        print("  count addr erase     - Borra 'count' bytes (pone a 0)")
        print("  addr cell+      - Siguiente celda (addr + 4)")
        print("  addr dump       - Muestra contenido de memoria")
        print("\n  COPIAR DATOS EN MEMORIA:")
        print("  addr1 addr2 u move   - Copia u bytes (detecta dirección automáticamente)")
        print("  addr1 addr2 u cmove  - Copia u bytes ascendente (seguro si addr2>addr1)")
        print("  addr1 addr2 u cmove> - Copia u bytes descendente (seguro si addr2<addr1)")
        print("    Ejemplo: s\" Hola\" drop dup 100 swap 5 move   (copia a addr 100)")
        print("    Uso: Copiar strings, arrays, bloques de datos en memoria")

        print("\n" + "─" * 70)
        print("BYTES Y CARACTERES")
        print("─" * 70)
        print("  var c@          - Lee byte de variable")
        print("  val var c!      - Escribe byte en variable")
        print("  addr mc@        - Lee byte de memoria")
        print("  val addr mc!    - Escribe byte en memoria")
        print("  val c,          - Almacena byte en memoria")
        print("  char A          - Obtiene código ASCII (inmediato)")
        print("  [char] A        - Obtiene código ASCII (compilado)")
        print("  code emit       - Muestra carácter desde código ASCII")
        print("  space           - Imprime un espacio")
        print("  bl              - Pone ASCII del espacio (32) en pila")
        print("  key             - Lee carácter del teclado (bloqueante)")
        print("  key?            - Verifica si hay tecla disponible")
        print("  addr len accept - Lee línea del usuario, guarda en addr (máx len chars)")
        print("                    Retorna número de caracteres leídos")
        print("  pad             - Retorna dirección del área temporal PAD (256 bytes)")
        print("                    Ejemplo: pad 80 accept → lee hasta 80 chars en PAD")

        print("\n" + "─" * 70)
        print("STRINGS Y FORMATEO")
        print("─" * 70)
        print("  .\" texto\"       - Imprime texto directamente")
        print("  s\" texto\"       - Coloca string en la pila")
        print("  type            - Imprime string de la pila")
        print("  evaluate        - Ejecuta código Forth desde string")
        print("    Ejemplo: s\" 5 3 + .\" evaluate → ejecuta el código")
        print("    También acepta: addr len evaluate (desde memoria)")
        print("  s>mem           - Copia string a memoria y retorna addr len")
        print("    Ejemplo: s\" 10 20 + .\" s>mem evaluate")
        print("    Útil para: guardar código y ejecutarlo después")
        print("  cr              - Imprime nueva línea")
        print("  n width .r      - Imprime n justificado a derecha en ancho 'width'")
        print("    Ejemplo: 42 5 .r → '   42 ' (3 espacios + 42)")

        print("\n" + "─" * 70)
        print("VARIABLES DE SISTEMA")
        print("─" * 70)
        print("  state @         - Muestra estado compilación (0=interp, -1=compil)")
        print("    Durante ejecución de palabra, siempre muestra 0")
        print("    Útil para palabras que necesitan saber su contexto")

        print("\n" + "─" * 70)
        print("BUCLES DO/LOOP")
        print("─" * 70)
        print("  lim start DO ... LOOP    - Bucle con incremento 1")
        print("  lim start DO ... +LOOP   - Bucle con incremento del stack")
        print("  I               - Índice bucle actual (más interno)")
        print("  J               - Índice bucle externo (2do nivel)")
        print("  K               - Índice bucle tercer nivel")
        print("  LEAVE           - Sale del bucle inmediatamente")
        print("  EXIT            - Sale de la palabra actual (early return)")
        print("    Ejemplo: : test 10 . exit 20 . ; → solo imprime 10")

        print("\n" + "─" * 70)
        print("BUCLES BEGIN/UNTIL/WHILE/REPEAT")
        print("─" * 70)
        print("  BEGIN ... UNTIL          - Loop hasta que condición sea TRUE")
        print("    Ejemplo: : countdown begin dup . 1- dup 0< until drop ;")
        print("    10 countdown → 10 9 8 7 6 5 4 3 2 1 0")
        print("  BEGIN ... AGAIN          - Loop infinito (con límite seguridad)")
        print("  BEGIN ... WHILE ... REPEAT  - Loop mientras condición sea TRUE")
        print("    Ejemplo: : suma-n 0 swap begin dup 0> while")
        print("             swap over + swap 1- repeat drop ;")
        print("    10 suma-n → 55 (suma de 1..10)")
        print("  Nota: Útil cuando no se conoce # iteraciones de antemano")
        print("  Flags: UNTIL sale si TRUE (≠0), WHILE continúa si TRUE (≠0)")

        print("\n" + "─" * 70)
        print("CONDICIONALES IF/THEN/ELSE")
        print("─" * 70)
        print("  IF ... THEN     - Ejecuta si stack top ≠ 0")
        print("  IF ... ELSE ... THEN  - Bifurcación completa")
        print("  Nota: Solo en modo compilación (dentro de : ; )")
        print("  Soporta anidamiento ilimitado")

        print("\n" + "─" * 70)
        print("EJECUCIÓN DIFERIDA")
        print("─" * 70)
        print("  ' palabra       - Obtiene referencia a palabra")
        print("  execute         - Ejecuta referencia de la pila")
        print("  ['] palabra     - Versión compilada de '")

        print("\n" + "─" * 70)
        print("META-PROGRAMACIÓN")
        print("─" * 70)
        print("  POSTPONE palabra  - Compila palabra inmediata")
        print("  CREATE nombre     - Crea palabra que pone dirección en pila")
        print("  DOES>             - Define comportamiento de CREATE")
        print("  IMMEDIATE         - Marca última palabra como inmediata")

        print("\n" + "─" * 70)
        print("PERSISTENCIA")
        print("─" * 70)
        print("  s\" file.fth\" save  - Guarda definiciones en archivo")
        print("  s\" file.fth\" load  - Carga y ejecuta archivo")
        print("  pwd               - Muestra directorio actual")

        print("\n" + "─" * 70)
        print("EJEMPLOS")
        print("─" * 70)
        print("  Memoria:")
        print("    100 , 200 , dump")
        print("    mvariable x  100 x m!  x m@ .")
        print("    variable contador  42 contador !  contador ?")
        print("  ")
        print("  Bucles DO/LOOP:")
        print("    10 0 DO I . LOOP              → 0 1 2 3 4 5 6 7 8 9")
        print("    10 0 DO I . 2 +LOOP           → 0 2 4 6 8")
        print("    5 0 DO 3 0 DO I J + . LOOP LOOP  → bucles anidados")
        print("  ")
        print("  Bucles BEGIN:")
        print("    : countdown begin dup . 1- dup 0< until drop ;")
        print("    10 countdown                  → 10 9 8 7 6 5 4 3 2 1 0")
        print("    : suma-n 0 swap begin dup 0> while swap over + swap 1- repeat drop ;")
        print("    10 suma-n .                   → 55")
        print("  ")
        print("  Condicionales:")
        print("    : positivo? 0 > if .\" Positivo\" else .\" Negativo\" then ;")
        print("    : par? 2 mod 0 = if .\" Par\" then ;")
        print("  ")
        print("  Introspección:")
        print("    see dup           → muestra cómo está definido dup")
        print("    see contador      → muestra tipo y valor")
        print("  ")
        print("  Meta-programación:")
        print("    : CONSTANT CREATE , DOES> m@ ;")
        print("    42 CONSTANT RESPUESTA")
        print("  ")
        print("  Persistencia:")
        print("    s\" micodigo.fth\" save")
        print("    s\" micodigo.fth\" load")

        print("\n" + "=" * 70)
        print("Total de palabras: ~145+ | Usa 'words' para ver todas")
        print("=" * 70)
        return self

    # CORREGIDO: Cambiar execute por execute_word en el DSL
    def execute_word(self):
        """DSL para execute (evita conflicto con execute de interpretación)"""
        self.words['execute']()
        return self

    # Métodos DSL
    def immediate(self):
        self.words['immediate']()
        return self

    def forget(self, name=None):
        if name is not None:
            self.stack.append(name)
        self.words['forget']()
        return self

    def plus(self):
        self.words['+']()
        return self

    def minus(self):
        self.words['-']()
        return self

    def mult(self):
        self.words['*']()
        return self

    def div(self):
        self.words['/']()
        return self

    def dot(self):
        self.words['.']()
        return self

    def dot_s(self):
        self.words['.s']()
        return self

    def power(self):
        self.words['**']()
        return self

    def space(self):
        """DSL para space - imprime un espacio"""
        self.words['space']()
        return self

    def bl(self):
        """DSL para bl - pone el valor ASCII del espacio en la pila"""
        self.words['bl']()
        return self

    def help(self):
        return self._help()

    def list_words(self):
        return self._list_words()

    def type(self):
        self.words['type']()
        return self

    def cr(self):
        self.words['cr']()
        return self

    def page(self):
        self.words['page']()
        return self

    def emit(self):
        self.words['emit']()
        return self

    def key(self):
        self.words['key']()
        return self

    def key_question(self):
        self.words['key?']()
        return self

    def accept(self, addr=None, length=None):
        if addr is not None and length is not None:
            self.stack.extend([addr, length])
        elif addr is not None:
            self.stack.append(addr)
        self.words['accept']()
        return self

    def pad(self):
        self.words['pad']()
        return self

    def to_r(self):
        self.words['>r']()
        return self

    def from_r(self):
        self.words['r>']()
        return self

    def r_fetch(self):
        self.words['r@']()
        return self

    def sin(self):
        self.words['sin']()
        return self

    def cos(self):
        self.words['cos']()
        return self

    def tan(self):
        self.words['tan']()
        return self

    def sqrt(self):
        self.words['sqrt']()
        return self

    def log(self):
        self.words['log']()
        return self

    def ln(self):
        self.words['ln']()
        return self

    def rot(self):
        self.words['rot']()
        return self

    def nip(self):
        self.words['nip']()
        return self

    def tuck(self):
        self.words['tuck']()
        return self

    def depth(self):
        self.words['depth']()
        return self

    def lshift(self):
        self.words['lshift']()
        return self

    def rshift(self):
        self.words['rshift']()
        return self

    def invert(self):
        self.words['invert']()
        return self

    def here(self):
        self.words['here']()
        return self

    def allot(self, n=None):
        if n is not None:
            self.stack.append(n)
        self.words['allot']()
        return self

    def comma(self, value=None):
        if value is not None:
            self.stack.append(value)
        self.words[',']()
        return self

    def memory_fetch(self, address=None):
        if address is not None:
            self.stack.append(address)
        self.words['m@']()
        return self

    def memory_store(self, value=None, address=None):
        if value is not None and address is not None:
            self.stack.extend([value, address])
        elif value is not None:
            self.stack.append(value)
        self.words['m!']()
        return self

    def dump_memory(self):
        self.words['dump']()
        return self

    def c_fetch(self, address=None):
        if address is not None:
            self.stack.append(address)
        self.words['c@']()
        return self

    def c_store(self, value=None, address=None):
        if value is not None and address is not None:
            self.stack.extend([value, address])
        elif value is not None:
            self.stack.append(value)
        self.words['c!']()
        return self

    def mc_fetch(self, address=None):
        if address is not None:
            self.stack.append(address)
        self.words['mc@']()
        return self

    def mc_store(self, value=None, address=None):
        if value is not None and address is not None:
            self.stack.extend([value, address])
        elif value is not None:
            self.stack.append(value)
        self.words['mc!']()
        return self

    def c_comma(self, value=None):
        if value is not None:
            self.stack.append(value)
        self.words['c,']()
        return self

    def tick(self, word_name=None):
        if word_name is not None:
            self.stack.append(word_name)
        self.words["'"]()
        return self

    def bracket_tick(self, word_name=None):
        if word_name is not None:
            self.stack.append(word_name)
        self.immediate_words["[']"]()
        return self

    def negativo(self, value):
        self.stack.append(-value)
        return self

    def measure(self, word_name):
        """Mide el tiempo de ejecución de una palabra
        Uso: f.measure('palabra')
        Retorna el tiempo en la pila (en segundos) y lo muestra formateado
        """
        start_time = time.perf_counter()
        
        # Ejecutar la palabra
        if word_name in self.immediate_words:
            self.immediate_words[word_name]()
        elif word_name in self.words:
            self.words[word_name]()
        elif word_name in self.variables:
            self.stack.append(self.variables[word_name])
        elif word_name in self.constants:
            self.stack.append(self.constants[word_name])
        elif word_name in self.values:
            self.stack.append(self.values[word_name])
        else:
            print(f"Error: palabra '{word_name}' no encontrada")
            return self
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        # Formatear y mostrar
        time_str, _ = self._format_time(elapsed)
        self.stack.append(elapsed)
        print(f"Tiempo de '{word_name}': {time_str}")
        
        return self

    def repl(self, auto_space=True):
        """Inicia el REPL interactivo de Forth con esta instancia"""
        # Llamar a la función repl() standalone pasando esta instancia
        repl(forth_instance=self, auto_space=auto_space)
        return self

def create_forth(memory_size_kb=64):
    forth = InteractiveForth()
    
    # Validar tamaño mínimo (debe acomodar PAD de 256 bytes)
    min_size_kb = 1  # 1KB = 1024 bytes > 256 bytes de PAD
    if memory_size_kb < min_size_kb:
        print(f"Advertencia: tamaño mínimo es {min_size_kb}KB (para acomodar PAD), usando {min_size_kb}KB")
        memory_size_kb = min_size_kb
    
    forth._memory_size = memory_size_kb * 1024
    forth.memory = [0] * forth._memory_size
    forth.here = forth._pad_size  # Empieza después de PAD (protegido)
    # Asegurarse de que BASE esté configurada correctamente al crear instancia
    forth.variables['base'] = 10 # Por defecto decimal
    return forth

def clear_screen():
    """Limpia la pantalla del terminal"""
    os.system('clear' if os.name != 'nt' else 'cls')

def repl(forth_instance=None, auto_space=True):
    """REPL interactivo para Forth"""
    if forth_instance is None:
        forth_instance = create_forth()

    print("\n=== FORTH REPL ===")
    print("Escribe 'help' para ayuda, 'bye' para salir")
    print("Comandos: words, .s, clear, definitions")
    print()

    while True:
        try:
            # Mostrar prompt basado en la base actual
            base = forth_instance.variables.get('base', 10)
            base_str = {10: 'DEC', 16: 'HEX', 2: 'BIN'}.get(base, str(base))
            prompt = f"{base_str}> "
            line = input(prompt).strip()

            if not line:
                continue

            if line.lower() == 'bye':
                print("¡Hasta luego!")
                break

            if line.lower() == 'help':
                forth_instance._help()
                print()
                continue

            if line.lower() == 'abort':
                forth_instance.stack.clear()
                forth_instance.rstack.clear()
                print("Pilas limpiadas")
                print()
                continue

            if line.lower() == 'stack':
                print(f"Stack: {forth_instance.stack}")
                if forth_instance.rstack:
                    print(f"RStack: {forth_instance.rstack}")
                print()
                continue

            if line.lower() == 'cls' or line.lower() == 'page':
                clear_screen()
                print()
                continue

            # Ejecutar código Forth
            forth_instance.execute(line)

            # Agregar salto de línea para que el próximo prompt esté en nueva línea
            # Esto previene que el prompt se solape con la salida de .r, ., etc.
            print()

        except KeyboardInterrupt:
            print("\n¡Hasta luego!")
            break
        except EOFError:
            print("\n¡Hasta luego!")
            break
        except Exception as e:
            # Imprimir el error y continuar el REPL
            print(f"Error: {e}")
            # Limpiar flags de control en caso de error grave
            forth_instance._exit_flag = False
            forth_instance._leave_flag = False
            forth_instance._loop_stack.clear()
            print()

    return forth_instance

if __name__ == "__main__":
    f = create_forth()
    print("=== DEMOSTRACIÓN FORTH PYTHON COMPLETO ===")

    print('\n1. Operaciones básicas:')
    f.execute('5 3 + .')  # 8

    print('\n2. Memoria dinámica:')
    f.execute('100 , 200 ,')
    f.execute('0 m@ . 1 m@ .')  # 100 200

    print('\n3. Operaciones de bytes:')
    f.execute('65 0 mc!')
    f.execute('0 mc@ emit')  # A

    print('\n4. Ejecución diferida:')
    f.execute("' dup .s")
    f.execute('drop')

    print('\n5. Nuevas palabras space y bl:')
    f.execute('space bl .')  # Imprime un espacio y luego 32

    print('\n6. Cambio de BASE:')
    f.execute('HEX 10 20 .') # Debe imprimir 30 (20 en hex es 32)
    f.execute('DECIMAL') # Volver a decimal
    f.execute('16 2 .') # Debe imprimir 16

    print('\n¿Quieres usar el REPL interactivo? (s/n)')
    if input().lower().startswith('s'):
        f = repl(f)
        print("\nContinuando en modo programático...")
        f.execute('." Instancia preservada" cr')