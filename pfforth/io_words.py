"""
PFForth I/O - Input/output operations and File Wordset
"""

import sys
import os
import select


class ForthIO:
    """Mixin providing I/O operations"""
    
    def _register_io_words(self):
        """Register I/O words"""
        self.words['emit'] = self._emit
        self.words['key'] = self._key
        self.words['key?'] = self._key_question
        self.words['key-ios-mode'] = self._key_force_ios
        self.words['key-mac-mode'] = self._key_force_mac
        self.words['key-mode?'] = self._key_show_mode
        self.words['accept'] = self._accept
        self.words['type'] = self._type
        self.words['cr'] = self._cr
        self.words['page'] = self._page
        self.words['space'] = self._space
        self.words['bl'] = self._bl
        self.words['evaluate'] = self._evaluate
        self.words['s>mem'] = self._s_to_mem
        self.words['mem>s'] = self._mem_to_s
        self.words['parse'] = self._parse
        self.words['pwd'] = self._pwd
        self.words['dir'] = self._dir
        self.words['cd'] = self._cd
        self.words['>str'] = self._to_str
        self.words['str>'] = self._str_to_num
        
        self.immediate_words['char'] = self._char_immediate
        self.immediate_words['[char]'] = self._bracket_char
        self.immediate_words['."'] = self._dot_quote
        self.immediate_words['s"'] = self._s_quote
        self.immediate_words["s'"] = self._s_quote
        self.immediate_words["r|"] = self._s_quote
        self.immediate_words['py"'] = self._py_quote
        self.immediate_words['py{'] = self._py_block
        self.immediate_words['}py'] = self._py_block
        self.immediate_words['py['] = self._py_inline
        self.immediate_words[']py'] = self._py_inline
        
        self.words['open-file'] = self._open_file
        self.words['close-file'] = self._close_file
        self.words['create-file'] = self._create_file
        self.words['delete-file'] = self._delete_file
        self.words['read-file'] = self._read_file
        self.words['read-line'] = self._read_line
        self.words['write-file'] = self._write_file
        self.words['write-line'] = self._write_line
        self.words['file-position'] = self._file_position
        self.words['reposition-file'] = self._reposition_file
        self.words['file-size'] = self._file_size
        self.words['file-exists?'] = self._file_exists
        self.words['flush-file'] = self._flush_file
        self.words['rename-file'] = self._rename_file
        
        self.words['decimal'] = self._decimal
        self.words['hex'] = self._hex
        self.words['binary'] = self._binary
        
        self.words['number'] = self._number
        self.words['>number'] = self._to_number
        self.words['.dec'] = self._dot_dec

        self.words['output-to']         = self._output_to
        self.words['output-to-console'] = self._output_to_console
        self.words['output-to-string']  = self._output_to_string
        self.words['output-get-string'] = self._output_get_string
        self.words['input-from-string'] = self._input_from_string
        self.words['input-from-console']= self._input_from_console
        self.words['input-to']          = self._input_to
        self.words['output-stream?']    = self._output_stream_query
        self.words['input-stream?']     = self._input_stream_query

        self._original_stdin  = sys.stdin
        self._string_buffer   = None
        self._forth_output    = sys.stdout
        self._forth_input     = sys.stdin

    def _emit(self):
        if self.stack:
            code = int(self.stack.pop())
            self._forth_output.write(chr(code))
            self._forth_output.flush()
    
    # ------------------------------------------------------------------ #
    #  Detección de plataforma para key / key?                           #
    # ------------------------------------------------------------------ #

    def _raw_mode_supported(self):
        """Devuelve True si el modo raw/cbreak funciona sin romper el PTY.
        En iOS (a-Shell) el cambio de modo del PTY provoca que el teclado
        deje de responder — se usa modo línea como fallback seguro."""
        if not hasattr(self, '_raw_mode_ok'):
            try:
                import platform as _pl
                is_ios = False

                # 1) HOME de a-Shell está dentro del sandbox: /var/mobile/...
                home = os.environ.get('HOME', '')
                if '/var/mobile/' in home:
                    is_ios = True

                # 2) TERM_PROGRAM que a-Shell puede poner
                if os.environ.get('TERM_PROGRAM', '').lower() in ('a-shell', 'a_shell'):
                    is_ios = True

                # 3) Machine devuelve modelo de dispositivo iOS (iPhone/iPad)
                machine = _pl.machine()
                if any(d in machine for d in ('iPhone', 'iPad', 'iPod')):
                    is_ios = True

                # 4) Ruta del sistema iOS (puede no ser accesible desde el sandbox,
                #    pero vale como cuarta salvaguarda)
                try:
                    if (os.path.exists('/private/var/mobile') and
                            not os.path.exists('/Applications')):
                        is_ios = True
                except Exception:
                    pass

                fd_ok = hasattr(sys.stdin, 'fileno') and os.isatty(sys.stdin.fileno())
                self._raw_mode_ok = fd_ok and not is_ios
            except Exception:
                self._raw_mode_ok = False
        return self._raw_mode_ok

    def _key_force_ios(self):
        """key-ios-mode — fuerza modo línea (a-Shell/iOS), por si la detección falla."""
        self._raw_mode_ok = False
        print("key: modo línea (iOS/a-Shell) activado")

    def _key_force_mac(self):
        """key-mac-mode — fuerza modo raw (Mac/Linux)."""
        self._raw_mode_ok = True
        print("key: modo raw (Mac/Linux) activado")

    def _key_show_mode(self):
        """key-mode? — muestra qué modo usa key en esta plataforma."""
        mode = "raw (sin Enter)" if self._raw_mode_supported() else "línea (requiere Enter)"
        print(f"key mode: {mode}")
        home = os.environ.get('HOME', '?')
        print(f"  HOME={home}")

    def _key_line_buf(self):
        """Lee un carácter del buffer interno. Si está vacío lee una línea
        completa de stdin (requiere Enter) y carga todos sus caracteres.
        Modo seguro para plataformas donde el modo raw rompe el PTY."""
        if not hasattr(self, '_key_buf'):
            self._key_buf = []
        if self._key_buf:
            self.stack.append(self._key_buf.pop(0))
            return
        try:
            line = sys.stdin.readline()
            chars = [ord(c) for c in line.rstrip('\n\r')]
            if chars:
                self.stack.append(chars[0])
                self._key_buf = chars[1:]
            else:
                self.stack.append(13)   # Enter sin texto → CR
        except Exception:
            self.stack.append(0)

    # ------------------------------------------------------------------ #
    #  key  ( -- char )                                                   #
    # ------------------------------------------------------------------ #

    def _key(self):
        try:
            if self._forth_input is not sys.stdin:
                # Stream redirigido — carácter a carácter, sin cambios de modo
                char = self._forth_input.read(1)
                self.stack.append(ord(char) if char else 0)

            elif sys.platform == 'win32':
                # Windows: getwch() es raw nativo, sin Enter
                import msvcrt
                char = msvcrt.getwch()
                self.stack.append(ord(char) if char else 0)

            elif self._raw_mode_supported():
                # Mac / Linux: cbreak temporal, lectura directa del fd
                import tty, termios
                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                self._tty_canonical = old
                self._tty_needs_restore = True
                ch = b''
                try:
                    tty.setcbreak(fd, termios.TCSANOW)
                    ch = os.read(fd, 1)
                finally:
                    try:
                        termios.tcsetattr(fd, termios.TCSANOW, old)
                        self._tty_needs_restore = False
                    except Exception:
                        pass
                self.stack.append(ch[0] if ch else 0)

            else:
                # iOS / a-Shell y otros PTY que no soportan raw sin romperse:
                # modo línea con buffer interno (requiere Enter tras la tecla)
                self._key_line_buf()

        except Exception:
            self.stack.append(0)

    # ------------------------------------------------------------------ #
    #  key?  ( -- flag )                                                  #
    # ------------------------------------------------------------------ #

    def _key_question(self):
        try:
            if self._forth_input is not sys.stdin:
                import io
                if isinstance(self._forth_input, io.StringIO):
                    pos = self._forth_input.tell()
                    has_data = bool(self._forth_input.read(1))
                    self._forth_input.seek(pos)
                    self.stack.append(-1 if has_data else 0)
                else:
                    self.stack.append(-1)

            elif sys.platform == 'win32':
                import msvcrt
                self.stack.append(-1 if msvcrt.kbhit() else 0)

            elif self._raw_mode_supported():
                # Mac / Linux: cbreak temporal para que select funcione
                import tty, termios
                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                try:
                    tty.setcbreak(fd, termios.TCSANOW)
                    readable, _, _ = select.select([sys.stdin], [], [], 0)
                    self.stack.append(-1 if readable else 0)
                finally:
                    termios.tcsetattr(fd, termios.TCSANOW, old)

            else:
                # iOS / a-Shell: si el buffer interno tiene chars, hay datos
                buf = getattr(self, '_key_buf', [])
                self.stack.append(-1 if buf else 0)

        except Exception:
            self.stack.append(0)

    def _accept(self):
        if len(self.stack) >= 2:
            max_len = int(self.stack.pop())
            addr = int(self.stack.pop())
            try:
                line = self._forth_input.readline().rstrip('\n')[:max_len]
                for i, char in enumerate(line):
                    if 0 <= addr + i < self._memory_size:
                        self.memory[addr + i] = ord(char)
                self.stack.append(len(line))
            except:
                self.stack.append(0)
    
    def _type(self):
        """TYPE ( addr len -- ) o ( string -- ) Imprime texto
        Acepta dos formatos:
        1. addr len: lee caracteres de memoria e imprime
        2. string: imprime string Python directamente (de s")
        """
        if not self.stack:
            print("Error: TYPE requiere argumentos en la pila")
            return

        if isinstance(self.stack[-1], str):
            string = self.stack.pop()
            self._forth_output.write(string)
            self._forth_output.flush()
            return

        if len(self.stack) >= 2:
            try:
                length = int(self.stack.pop())
                addr = int(self.stack.pop())
            except (ValueError, TypeError):
                print("Error: TYPE requiere (addr len) o un string")
                return

            chars = []
            for i in range(length):
                if 0 <= addr + i < self._memory_size:
                    val = self.memory[addr + i]
                    if isinstance(val, int) and 0 < val < 128:
                        chars.append(chr(val))
            self._forth_output.write(''.join(chars))
            self._forth_output.flush()

    def _cr(self):
        self._forth_output.write('\n')
        self._forth_output.flush()

    def _page(self):
        from .core import clear_screen
        clear_screen()
        sys.stdout.flush()

    def _space(self):
        self._forth_output.write(' ')
        self._forth_output.flush()
    
    def _bl(self):
        self.stack.append(32)
    
    def _evaluate(self):
        if self.stack:
            code = self.stack.pop()
            if isinstance(code, str):
                self.execute(code)
    
    def _s_to_mem(self):
        if self.stack:
            s = self.stack.pop()
            if isinstance(s, str):
                addr = self.here
                for i, char in enumerate(s):
                    if addr + i < self._memory_size:
                        self.memory[addr + i] = ord(char)
                self.stack.append(addr)
                self.stack.append(len(s))
    
    def _mem_to_s(self):
        """( addr len -- str ) Lee bytes consecutivos de memoria y deja un string en la pila"""
        if len(self.stack) < 2:
            print("Error: mem>s requiere addr len")
            return
        length = self.stack.pop()
        addr = self.stack.pop()
        chars = []
        for i in range(length):
            if addr + i < self._memory_size:
                chars.append(chr(self.memory[addr + i]))
        self.stack.append(''.join(chars))

    def _parse(self):
        """( char "ccc<char>" -- addr len ) Lee texto hasta encontrar delimitador"""
        if len(self.stack) < 1:
            print("Error: parse requiere un delimitador en la pila")
            return

        delimiter_code = self.stack.pop()
        
        try:
            delimiter_code = int(delimiter_code)
        except (ValueError, TypeError):
            print(f"Error: parse requiere un código ASCII, recibió {type(delimiter_code)}")
            return
        
        try:
            delimiter = chr(delimiter_code)
        except ValueError:
            print(f"Error: código ASCII inválido: {delimiter_code}")
            return

        if not hasattr(self, '_input_tokens') or not hasattr(self, '_input_index'):
            self.stack.extend([self.here, 0])
            return
        
        parsed_parts = []
        start_idx = self._input_index + 1
        found_delimiter = False
        
        while start_idx < len(self._input_tokens):
            token = self._input_tokens[start_idx]
            
            if delimiter in token:
                before_delim = token.split(delimiter)[0]
                if before_delim:
                    parsed_parts.append(before_delim)
                found_delimiter = True
                self._input_index = start_idx
                break
            else:
                parsed_parts.append(token)
            start_idx += 1
        
        if not found_delimiter:
            self._input_index = len(self._input_tokens) - 1
        
        parsed_text = ' '.join(parsed_parts)

        length = len(parsed_text)
        if length == 0:
            self.stack.extend([self.here, 0])
            return

        new_here = self.here + length
        if new_here > self._memory_size:
            print(f"Error: memoria insuficiente (texto: {length} bytes)")
            self.stack.append(delimiter_code)
            return

        buffer_addr = self.here

        for i, char in enumerate(parsed_text):
            self.memory[self.here + i] = ord(char)

        self.here = new_here

        self.stack.extend([buffer_addr, length])
    
    def _pwd(self):
        print(os.getcwd())

    def _dir(self):
        """DIR ( -- ) o ( path -- )  Lista el directorio actual o el indicado"""
        if self.stack and isinstance(self.stack[-1], str):
            path = os.path.expanduser(self.stack.pop())
        else:
            path = os.getcwd()

        try:
            entries = sorted(os.listdir(path))
        except Exception as e:
            print(f"Error DIR: {e}")
            return

        dirs  = [e for e in entries if os.path.isdir(os.path.join(path, e))]
        files = [e for e in entries if not os.path.isdir(os.path.join(path, e))]

        print(f"  {path}")
        print(f"  {'─' * min(len(path), 60)}")
        for d in dirs:
            print(f"  [{d}]")
        for f in files:
            try:
                size = os.path.getsize(os.path.join(path, f))
                if size >= 1_048_576:
                    sz = f"{size/1_048_576:.1f} MB"
                elif size >= 1024:
                    sz = f"{size/1024:.1f} KB"
                else:
                    sz = f"{size} B"
            except Exception:
                sz = "?"
            print(f"  {f:<40} {sz:>9}")
        total = len(dirs) + len(files)
        print(f"  {'─' * 50}")
        print(f"  {len(dirs)} carpetas, {len(files)} ficheros  ({total} entradas)")

    def _cd(self):
        """CD ( path -- )  Cambia el directorio actual"""
        if not self.stack or not isinstance(self.stack[-1], str):
            print(f"Directorio actual: {os.getcwd()}")
            print("Uso: s\" ruta\" cd")
            return

        path = os.path.expanduser(self.stack.pop())
        try:
            os.chdir(path)
            print(f"  -> {os.getcwd()}")
        except FileNotFoundError:
            print(f"Error CD: directorio no encontrado — '{path}'")
        except NotADirectoryError:
            print(f"Error CD: no es un directorio — '{path}'")
        except PermissionError:
            print(f"Error CD: sin permiso — '{path}'")

    def _to_str(self):
        """( n -- str ) Convierte numero a string"""
        if self.stack:
            n = self.stack.pop()
            if isinstance(n, float) and n == int(n):
                self.stack.append(str(int(n)))
            else:
                self.stack.append(str(n))
    
    def _str_to_num(self):
        """( str -- n ) Convierte string a numero"""
        if self.stack:
            s = self.stack.pop()
            try:
                if '.' in str(s):
                    self.stack.append(float(s))
                else:
                    self.stack.append(int(s))
            except:
                print(f"Error: no se puede convertir '{s}' a numero")
                self.stack.append(0)
    
    def _char_immediate(self):
        pass
    
    def _bracket_char(self):
        pass
    
    def _dot_quote(self):
        pass
    
    def _s_quote(self):
        pass
    
    def _py_quote(self):
        pass
    
    def _py_block(self):
        pass
    
    def _py_inline(self):
        pass
    
    def _decimal(self):
        self.variables['base'] = 10
    
    def _hex(self):
        self.variables['base'] = 16
    
    def _binary(self):
        self.variables['base'] = 2
    
    def _number(self):
        """( c-addr u -- n true | false ) or ( string -- n true | false )
        Convert a string to a number using current base.
        Returns the number and true if successful, or just false if not.
        Accepts either addr+count or a Python string directly.
        """
        if len(self.stack) < 1:
            print("Error: NUMBER requiere una cadena")
            return
        
        top = self.stack[-1]
        if isinstance(top, str):
            string = self.stack.pop()
        elif len(self.stack) >= 2:
            count = int(self.stack.pop())
            addr = int(self.stack.pop())
            chars = []
            for i in range(count):
                if 0 <= addr + i < self._memory_size:
                    val = self.memory[addr + i]
                    if isinstance(val, int):
                        chars.append(chr(val))
            string = ''.join(chars)
        else:
            print("Error: NUMBER requiere (addr u) o una cadena")
            return
        
        try:
            num = self._parse_number(string)
            self.stack.append(num)
            self.stack.append(-1)
        except (ValueError, SyntaxError):
            self.stack.append(0)
    
    def _to_number(self):
        """( ud1 c-addr1 u1 -- ud2 c-addr2 u2 ) or ( ud string -- ud2 string2 u2 )
        ANS Forth >NUMBER: Accumulate digits from string into ud1.
        Converts characters using current base until non-digit found.
        Returns updated number, address past last converted char, remaining count.
        Accepts either (ud addr count) or (ud string) format.
        """
        if len(self.stack) < 2:
            print("Error: >NUMBER requiere (ud string) o (ud c-addr u)")
            return
        
        top = self.stack[-1]
        if isinstance(top, str):
            string = self.stack.pop()
            ud = self.stack.pop()
            is_string = True
            count = len(string)
        elif len(self.stack) >= 3:
            count = int(self.stack.pop())
            addr = self.stack.pop()
            ud = self.stack.pop()
            if isinstance(addr, str):
                string = addr[:count] if count < len(addr) else addr
                is_string = True
            else:
                addr = int(addr)
                chars = []
                for i in range(count):
                    if 0 <= addr + i < self._memory_size:
                        val = self.memory[addr + i]
                        if isinstance(val, int):
                            chars.append(chr(val))
                string = ''.join(chars)
                is_string = False
        else:
            print("Error: >NUMBER requiere (ud string) o (ud c-addr u)")
            return
        
        base = self.variables.get('base', 10)
        
        converted = 0
        for char in string:
            if char.isdigit():
                digit = ord(char) - ord('0')
            elif char.upper() >= 'A' and char.upper() <= 'Z':
                digit = ord(char.upper()) - ord('A') + 10
            else:
                break
            
            if digit >= base:
                break
            
            ud = ud * base + digit
            converted += 1
        
        remaining = count - converted
        if is_string:
            new_addr = string[converted:] if converted < len(string) else ""
        else:
            new_addr = addr + converted
        
        self.stack.append(ud)
        self.stack.append(new_addr)
        self.stack.append(remaining)
    
    def _dot_dec(self):
        """( n decimals -- ) Imprime número con cantidad específica de decimales
        Ejemplo: 4.24747 2 .dec  imprime 4.24
        """
        if len(self.stack) < 2:
            print("Error: .DEC requiere (n decimales)")
            return
        
        decimals = int(self.stack.pop())
        num = self.stack.pop()
        
        if decimals < 0:
            decimals = 0
        
        formatted = f"{num:.{decimals}f}"
        print(formatted, end=' ')
        sys.stdout.flush()
    
    def _get_filename(self):
        """Get filename from stack (string or addr u)"""
        if not self.stack:
            return None
        
        item = self.stack[-1]
        if isinstance(item, str):
            self.stack.pop()
            return item
        elif len(self.stack) >= 2:
            count = int(self.stack.pop())
            addr = int(self.stack.pop())
            chars = []
            for i in range(count):
                if 0 <= addr + i < self._memory_size:
                    val = self.memory[addr + i]
                    if isinstance(val, int):
                        chars.append(chr(val))
            return ''.join(chars)
        return None
    
    def _open_file(self):
        if len(self.stack) < 2:
            print("Error: OPEN-FILE requiere (addr u fam)")
            return
        
        fam = int(self.stack.pop())
        filename = self._get_filename()
        
        if not filename:
            self.stack.extend([0, -1])
            return
        
        mode_map = {0: 'r', 1: 'w', 2: 'r+'}
        mode = mode_map.get(fam, 'r')
        
        try:
            f = open(filename, mode)
            fileid = self._next_fileid
            self._file_handles[fileid] = f
            self._next_fileid += 1
            self.stack.extend([fileid, 0])
        except:
            self.stack.extend([0, -1])
    
    def _close_file(self):
        if not self.stack:
            print("Error: CLOSE-FILE requiere fileid")
            return
        
        fileid = self.stack.pop()
        
        if fileid in self._file_handles:
            try:
                self._file_handles[fileid].close()
                del self._file_handles[fileid]
                self.stack.append(0)
            except:
                self.stack.append(-1)
        else:
            self.stack.append(-1)
    
    def _create_file(self):
        if len(self.stack) < 2:
            print("Error: CREATE-FILE requiere (addr u fam)")
            return
        
        fam = int(self.stack.pop())
        filename = self._get_filename()
        
        if not filename:
            self.stack.extend([0, -1])
            return
        
        try:
            f = open(filename, 'w+')
            fileid = self._next_fileid
            self._file_handles[fileid] = f
            self._next_fileid += 1
            self.stack.extend([fileid, 0])
        except:
            self.stack.extend([0, -1])
    
    def _delete_file(self):
        filename = self._get_filename()
        
        if not filename:
            self.stack.append(-1)
            return
        
        try:
            os.remove(filename)
            self.stack.append(0)
        except:
            self.stack.append(-1)
    
    def _read_file(self):
        if len(self.stack) < 3:
            print("Error: READ-FILE requiere (addr u fileid)")
            return
        
        fileid = self.stack.pop()
        count = int(self.stack.pop())
        addr = int(self.stack.pop())
        
        if fileid not in self._file_handles:
            self.stack.extend([0, -1])
            return
        
        try:
            f = self._file_handles[fileid]
            data = f.read(count)
            for i, char in enumerate(data):
                if 0 <= addr + i < self._memory_size:
                    self.memory[addr + i] = ord(char)
            self.stack.extend([len(data), 0])
        except:
            self.stack.extend([0, -1])
    
    def _read_line(self):
        if len(self.stack) < 3:
            print("Error: READ-LINE requiere (addr u fileid)")
            return
        
        fileid = self.stack.pop()
        max_len = int(self.stack.pop())
        addr = int(self.stack.pop())
        
        if fileid not in self._file_handles:
            self.stack.extend([0, 0, -1])
            return
        
        try:
            f = self._file_handles[fileid]
            line = f.readline(max_len)
            if line.endswith('\n'):
                line = line[:-1]
            for i, char in enumerate(line):
                if 0 <= addr + i < self._memory_size:
                    self.memory[addr + i] = ord(char)
            flag = -1 if line else 0
            self.stack.extend([len(line), flag, 0])
        except:
            self.stack.extend([0, 0, -1])
    
    def _write_file(self):
        if len(self.stack) < 3:
            print("Error: WRITE-FILE requiere (addr u fileid)")
            return
        
        fileid = self.stack.pop()
        count = int(self.stack.pop())
        addr = int(self.stack.pop())
        
        if fileid not in self._file_handles:
            self.stack.append(-1)
            return
        
        try:
            f = self._file_handles[fileid]
            chars = []
            for i in range(count):
                if 0 <= addr + i < self._memory_size:
                    val = self.memory[addr + i]
                    if isinstance(val, int):
                        chars.append(chr(val))
            f.write(''.join(chars))
            self.stack.append(0)
        except:
            self.stack.append(-1)
    
    def _write_line(self):
        if len(self.stack) < 3:
            print("Error: WRITE-LINE requiere (addr u fileid)")
            return
        
        fileid = self.stack.pop()
        count = int(self.stack.pop())
        addr = int(self.stack.pop())
        
        if fileid not in self._file_handles:
            self.stack.append(-1)
            return
        
        try:
            f = self._file_handles[fileid]
            chars = []
            for i in range(count):
                if 0 <= addr + i < self._memory_size:
                    val = self.memory[addr + i]
                    if isinstance(val, int):
                        chars.append(chr(val))
            f.write(''.join(chars) + '\n')
            self.stack.append(0)
        except:
            self.stack.append(-1)
    
    def _file_position(self):
        if not self.stack:
            print("Error: FILE-POSITION requiere fileid")
            return
        
        fileid = self.stack.pop()
        
        if fileid not in self._file_handles:
            self.stack.extend([0, 0, -1])
            return
        
        try:
            f = self._file_handles[fileid]
            pos = f.tell()
            self.stack.extend([pos, 0, 0])
        except:
            self.stack.extend([0, 0, -1])
    
    def _reposition_file(self):
        if len(self.stack) < 3:
            print("Error: REPOSITION-FILE requiere (ud-low ud-high fileid)")
            return
        
        fileid = self.stack.pop()
        ud_high = self.stack.pop()
        ud_low = self.stack.pop()
        pos = ud_low + (ud_high << 32)
        
        if fileid not in self._file_handles:
            self.stack.append(-1)
            return
        
        try:
            f = self._file_handles[fileid]
            f.seek(pos)
            self.stack.append(0)
        except:
            self.stack.append(-1)
    
    def _file_size(self):
        if not self.stack:
            print("Error: FILE-SIZE requiere fileid")
            return
        
        fileid = self.stack.pop()
        
        if fileid not in self._file_handles:
            self.stack.extend([0, 0, -1])
            return
        
        try:
            f = self._file_handles[fileid]
            current = f.tell()
            f.seek(0, 2)
            size = f.tell()
            f.seek(current)
            self.stack.extend([size, 0, 0])
        except:
            self.stack.extend([0, 0, -1])
    
    def _file_exists(self):
        filename = self._get_filename()
        
        if not filename:
            self.stack.append(0)
            return
        
        self.stack.append(-1 if os.path.exists(filename) else 0)
    
    def _flush_file(self):
        if not self.stack:
            print("Error: FLUSH-FILE requiere fileid")
            return
        
        fileid = self.stack.pop()
        
        if fileid not in self._file_handles:
            self.stack.append(-1)
            return
        
        try:
            self._file_handles[fileid].flush()
            self.stack.append(0)
        except:
            self.stack.append(-1)
    
    def _rename_file(self):
        if len(self.stack) < 2:
            print("Error: RENAME-FILE requiere dos nombres")
            return
        
        new_name = self._get_filename()
        old_name = self._get_filename()
        
        if not old_name or not new_name:
            self.stack.append(-1)
            return
        
        try:
            os.rename(old_name, new_name)
            self.stack.append(0)
        except:
            self.stack.append(-1)

    def _output_to(self):
        """Redirige la salida Forth al objeto Python en la cima de la pila.
        El objeto debe tener un método write(str) y flush().
        El REPL (prompts, errores) sigue en la consola."""
        if not self.stack:
            print("Error: output-to requiere un objeto en la pila")
            return
        obj = self.stack.pop()
        if not hasattr(obj, 'write'):
            print("Error: output-to — el objeto no tiene método write()")
            return
        self._string_buffer = None
        self._forth_output = obj

    def _output_to_console(self):
        """Restaura la salida Forth a la consola."""
        self._forth_output = sys.stdout
        self._string_buffer = None

    def _output_to_string(self):
        """Captura toda la salida Forth en un buffer interno.
        Usar output-get-string para recuperar el texto."""
        import io
        self._string_buffer = io.StringIO()
        self._forth_output = self._string_buffer

    def _output_get_string(self):
        """Recupera el texto capturado y restaura la salida a la consola.
        ( -- str )"""
        if self._string_buffer is not None:
            result = self._string_buffer.getvalue()
            self._forth_output = sys.stdout
            self._string_buffer = None
        else:
            result = ''
        self.stack.append(result)

    def _input_from_string(self):
        """Redirige el input Forth a un string. Las siguientes llamadas a
        key, key? y accept leerán de ese string. El REPL sigue en el teclado.
        ( str -- )"""
        import io
        if not self.stack:
            print("Error: input-from-string requiere un string en la pila")
            return
        text = str(self.stack.pop())
        self._forth_input = io.StringIO(text)

    def _input_from_console(self):
        """Restaura el input Forth al teclado original."""
        self._forth_input = self._original_stdin

    def _input_to(self):
        """Redirige el input Forth a cualquier objeto Python con read().
        ( obj -- )"""
        if not self.stack:
            print("Error: input-to requiere un objeto en la pila")
            return
        obj = self.stack.pop()
        if not hasattr(obj, 'read'):
            print("Error: input-to — el objeto no tiene método read()")
            return
        self._forth_input = obj

    def _output_stream_query(self):
        """Devuelve el objeto stream de salida Forth actual.
        ( -- obj )"""
        self.stack.append(self._forth_output)

    def _input_stream_query(self):
        """Devuelve el objeto stream de entrada Forth actual.
        ( -- obj )"""
        self.stack.append(self._forth_input)

