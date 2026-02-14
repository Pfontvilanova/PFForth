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
    
    def _emit(self):
        if self.stack:
            code = int(self.stack.pop())
            print(chr(code), end='')
            sys.stdout.flush()
    
    def _key(self):
        try:
            char = sys.stdin.read(1)
            self.stack.append(ord(char) if char else 0)
        except:
            self.stack.append(0)
    
    def _key_question(self):
        try:
            if sys.platform == 'win32':
                import msvcrt
                self.stack.append(-1 if msvcrt.kbhit() else 0)
            else:
                readable, _, _ = select.select([sys.stdin], [], [], 0)
                self.stack.append(-1 if readable else 0)
        except:
            self.stack.append(0)
    
    def _accept(self):
        if len(self.stack) >= 2:
            max_len = int(self.stack.pop())
            addr = int(self.stack.pop())
            try:
                line = input()[:max_len]
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
            print(string, end='')
            sys.stdout.flush()
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
            print(''.join(chars), end='')
            sys.stdout.flush()
    
    def _cr(self):
        print()
    
    def _page(self):
        from .core import clear_screen
        clear_screen()
        sys.stdout.flush()
    
    def _space(self):
        print(' ', end='')
        sys.stdout.flush()
    
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
