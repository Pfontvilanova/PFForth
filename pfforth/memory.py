"""
PFForth Memory - Memory management, variables, constants
"""

import os


class ForthMemory:
    """Mixin providing memory management operations"""
    
    def _register_memory_words(self):
        """Register memory words"""
        self.words['@'] = self._fetch
        self.words['!'] = self._store
        self.words['c@'] = self._c_fetch
        self.words['c!'] = self._c_store
        self.words['m@'] = self._m_fetch
        self.words['m!'] = self._m_store
        self.words['mc@'] = self._mc_fetch
        self.words['mc!'] = self._mc_store
        
        self.words['+!'] = self._plus_store
        self.words['?'] = self._question
        self.words['fill'] = self._fill
        self.words['erase'] = self._erase
        self.words['move'] = self._move
        self.words['cmove'] = self._cmove
        self.words['cmove>'] = self._cmove_up
        self.words['place'] = self._place
        self.words['count'] = self._count
        self.words['cell+'] = self._cell_plus
        self.words['cells'] = self._cells
        
        self.words['here'] = self._here
        self.words['allot'] = self._allot
        self.words['buffer'] = self._buffer
        self.words[','] = self._comma
        self.words['c,'] = self._c_comma
        self.words['dump'] = self._dump
        self.words['mem'] = self._dump
        self.words['pad'] = self._pad
        
        self.words['variable'] = self._variable_stub
        self.words['constant'] = self._constant_stub
        self.words['value'] = self._value_stub
        self.words['to'] = self._to_stub
        
        self.words['reset-mem'] = self._reset_memory
        self.words['memory'] = self._show_memory_status
        self.words['resize-memory'] = self._resize_memory
        self.words['store-string'] = self._store_string_to_memory
        self.words['load-string'] = self._load_string_from_memory
    
    def _fetch(self):
        if self.stack:
            name_or_addr = self.stack.pop()
            if isinstance(name_or_addr, str):
                if name_or_addr in self.variables:
                    self.stack.append(self.variables[name_or_addr])
                elif name_or_addr in self.values:
                    self.stack.append(self.values[name_or_addr])
                else:
                    print(f"Error: variable/value '{name_or_addr}' no existe")
            else:
                addr = int(name_or_addr)
                if 0 <= addr < self._memory_size:
                    self.stack.append(self.memory[addr])
    
    def _store(self):
        if len(self.stack) >= 2:
            name_or_addr = self.stack.pop()
            value = self.stack.pop()
            if isinstance(name_or_addr, str):
                if name_or_addr in self.variables:
                    self.variables[name_or_addr] = value
                else:
                    print(f"Error: variable '{name_or_addr}' no existe")
            else:
                addr = int(name_or_addr)
                if 0 <= addr < self._memory_size:
                    self.memory[addr] = value
    
    def _c_fetch(self):
        if self.stack:
            addr = int(self.stack.pop())
            if 0 <= addr < self._memory_size:
                val = self.memory[addr]
                if isinstance(val, int):
                    self.stack.append(val & 0xFF)
                else:
                    self.stack.append(val)
    
    def _c_store(self):
        if len(self.stack) >= 2:
            addr = int(self.stack.pop())
            value = int(self.stack.pop()) & 0xFF
            if 0 <= addr < self._memory_size:
                self.memory[addr] = value
    
    def _m_fetch(self):
        if self.stack:
            addr = int(self.stack.pop())
            if 0 <= addr < self._memory_size:
                self.stack.append(self.memory[addr])
    
    def _m_store(self):
        if len(self.stack) >= 2:
            addr = int(self.stack.pop())
            value = self.stack.pop()
            if 0 <= addr < self._memory_size:
                self.memory[addr] = value
    
    def _mc_fetch(self):
        self._c_fetch()
    
    def _mc_store(self):
        self._c_store()
    
    def _plus_store(self):
        if len(self.stack) >= 2:
            name_or_addr = self.stack.pop()
            value = self.stack.pop()
            if isinstance(name_or_addr, str):
                if name_or_addr in self.variables:
                    self.variables[name_or_addr] += value
            else:
                addr = int(name_or_addr)
                if 0 <= addr < self._memory_size:
                    self.memory[addr] += value
    
    def _question(self):
        if self.stack:
            name_or_addr = self.stack.pop()
            if isinstance(name_or_addr, str):
                if name_or_addr in self.variables:
                    print(self.variables[name_or_addr], end=' ')
                elif name_or_addr in self.values:
                    print(self.values[name_or_addr], end=' ')
            else:
                addr = int(name_or_addr)
                if 0 <= addr < self._memory_size:
                    print(self.memory[addr], end=' ')
    
    def _fill(self):
        if len(self.stack) >= 3:
            value = int(self.stack.pop()) & 0xFF
            count = int(self.stack.pop())
            addr = int(self.stack.pop())
            for i in range(count):
                if 0 <= addr + i < self._memory_size:
                    self.memory[addr + i] = value
    
    def _erase(self):
        if len(self.stack) >= 2:
            count = int(self.stack.pop())
            addr = int(self.stack.pop())
            for i in range(count):
                if 0 <= addr + i < self._memory_size:
                    self.memory[addr + i] = 0
    
    def _move(self):
        if len(self.stack) >= 3:
            count = int(self.stack.pop())
            dest = int(self.stack.pop())
            src = int(self.stack.pop())
            data = [self.memory[src + i] for i in range(count) if 0 <= src + i < self._memory_size]
            for i, val in enumerate(data):
                if 0 <= dest + i < self._memory_size:
                    self.memory[dest + i] = val
    
    def _cmove(self):
        if len(self.stack) >= 3:
            count = int(self.stack.pop())
            dest = int(self.stack.pop())
            src = int(self.stack.pop())
            for i in range(count):
                if 0 <= src + i < self._memory_size and 0 <= dest + i < self._memory_size:
                    self.memory[dest + i] = self.memory[src + i]
    
    def _cmove_up(self):
        if len(self.stack) >= 3:
            count = int(self.stack.pop())
            dest = int(self.stack.pop())
            src = int(self.stack.pop())
            for i in range(count - 1, -1, -1):
                if 0 <= src + i < self._memory_size and 0 <= dest + i < self._memory_size:
                    self.memory[dest + i] = self.memory[src + i]
    
    def _place(self):
        """( addr1 len addr2 -- ) Copia counted string a destino
        Copia len bytes desde addr1 a addr2+1, y guarda len en addr2[0]
        """
        if len(self.stack) < 3:
            print("Error: PLACE requiere addr1 len addr2")
            return

        addr2 = int(self.stack.pop())
        length = int(self.stack.pop())
        addr1 = int(self.stack.pop())

        if addr1 < 0 or addr1 + length > self._memory_size:
            print(f"Error: rango origen inválido: {addr1} + {length}")
            return

        if addr2 < 0 or addr2 + length + 1 > self._memory_size:
            print(f"Error: rango destino inválido: {addr2} + {length + 1}")
            return

        self.memory[addr2] = length & 0xFF

        for i in range(length):
            self.memory[addr2 + 1 + i] = self.memory[addr1 + i]
    
    def _count(self):
        if self.stack:
            addr = int(self.stack.pop())
            if 0 <= addr < self._memory_size:
                count = self.memory[addr]
                self.stack.append(addr + 1)
                self.stack.append(count)
    
    def _cell_plus(self):
        if self.stack:
            self.stack.append(self.stack.pop() + 1)
    
    def _cells(self):
        if self.stack:
            self.stack.append(self.stack.pop())
    
    def _here(self):
        self.stack.append(self.here)
    
    def _allot(self):
        if self.stack:
            n = int(self.stack.pop())
            self.here += n
    
    def _buffer(self):
        if self.stack:
            n = int(self.stack.pop())
            self.stack.append(self.here)
            self.here += n
    
    def _comma(self):
        if self.stack:
            value = self.stack.pop()
            if self.here < self._memory_size:
                self.memory[self.here] = value
                self.here += 1
    
    def _c_comma(self):
        if self.stack:
            value = int(self.stack.pop()) & 0xFF
            if self.here < self._memory_size:
                self.memory[self.here] = value
                self.here += 1
    
    def _dump(self):
        if len(self.stack) >= 2:
            count = int(self.stack.pop())
            addr = int(self.stack.pop())
            print(f"\nMemory dump from {addr} ({count} bytes):")
            for i in range(0, count, 16):
                line_addr = addr + i
                hex_part = ""
                ascii_part = ""
                for j in range(16):
                    if i + j < count and 0 <= line_addr + j < self._memory_size:
                        val = self.memory[line_addr + j]
                        if isinstance(val, int):
                            hex_part += f"{val:02x} "
                            ascii_part += chr(val) if 32 <= val < 127 else "."
                        else:
                            hex_part += "?? "
                            ascii_part += "?"
                    else:
                        hex_part += "   "
                        ascii_part += " "
                print(f"{line_addr:04x}: {hex_part} |{ascii_part}|")
    
    def _pad(self):
        self.stack.append(0)
    
    def _variable_stub(self):
        print("Error: VARIABLE requiere nombre")
    
    def _constant_stub(self):
        print("Error: CONSTANT requiere valor y nombre")
    
    def _value_stub(self):
        print("Error: VALUE requiere valor y nombre")
    
    def _to_stub(self):
        print("Error: TO requiere un nombre de VALUE")
    
    def _sanitize_relative_path(self, path, base_dir):
        """Sanitize and validate a relative path"""
        if not path or not isinstance(path, str):
            raise ValueError("Path vacio o invalido")
        
        if path.startswith('/') or path.startswith('\\'):
            raise ValueError("Paths absolutos no permitidos")
        
        segments = path.split('/')
        for segment in segments:
            if not segment or segment.isspace():
                raise ValueError("Path con segmentos vacios")
            if '%' in segment:
                raise ValueError("Percent-encoding no permitido")
            normalized = segment.strip()
            if normalized in ('.', '..'):
                raise ValueError("Path traversal no permitido")
            dangerous_chars = set('<>:"|?*\\')
            if any(c in dangerous_chars for c in segment):
                raise ValueError(f"Caracteres no permitidos: {segment}")
        
        normalized_path = os.path.normpath(path)
        if normalized_path.startswith('..') or normalized_path.startswith('.'):
            raise ValueError("Path intenta escapar del directorio base")
        if '\\' in normalized_path:
            raise ValueError("Separadores Windows no permitidos")
        
        final_path = os.path.abspath(os.path.join(base_dir, normalized_path))
        try:
            common = os.path.commonpath([base_dir, final_path])
            if common != base_dir:
                raise ValueError("Path intenta escapar del directorio base")
        except ValueError:
            raise ValueError("Path intenta escapar del directorio base")
        
        return normalized_path
    
    def _reset_memory(self):
        """Reset memory to initial state"""
        self.memory = [0] * self._memory_size
        self.here = self._pad_size
        print(f"Memoria resetada (HERE en {self.here}, PAD protegido: 0-{self._pad_size-1})")
        return self
    
    def _show_memory_status(self):
        """Show memory status"""
        used = self.here
        free = self._memory_size - self.here
        usage_percent = (used / self._memory_size) * 100 if self._memory_size > 0 else 0
        user_used = self.here - self._pad_size

        print(f"\n=== ESTADO DE MEMORIA ===")
        print(f"Tamaño total: {self._memory_size} bytes ({self._memory_size//1024}KB)")
        print(f"PAD (protegido): 0-{self._pad_size-1} ({self._pad_size} bytes)")
        print(f"HERE actual: {self.here}")
        print(f"Usada por usuario: {user_used} bytes")
        print(f"Memoria libre: {free} bytes ({free//1024}KB)")
        print(f"Uso total: {usage_percent:.1f}%")

        if free > 0:
            print(f"Puedes almacenar aproximadamente {free} números más")
    
    def _resize_memory(self):
        """Resize memory to new size in KB"""
        if len(self.stack) < 1:
            print("Error: falta tamaño en KB para resize-memory")
            return

        new_size_kb = self.stack.pop()
        min_size_kb = 1

        if new_size_kb < min_size_kb:
            print(f"Error: el tamaño debe ser al menos {min_size_kb}KB (para acomodar PAD de {self._pad_size} bytes)")
            self.stack.append(new_size_kb)
            return

        new_size_bytes = new_size_kb * 1024
        old_memory = self.memory
        old_here = self.here

        self.memory = [0] * new_size_bytes
        self._memory_size = new_size_bytes

        copy_size = min(len(old_memory), new_size_bytes)
        for i in range(copy_size):
            self.memory[i] = old_memory[i]

        if self.here > new_size_bytes:
            self.here = self._pad_size

        self._show_memory_status()
    
    def _store_string_to_memory(self):
        """Store string to memory address"""
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
        """Load string from memory address"""
        if len(self.stack) < 1:
            print("Error: falta dirección para load-string")
            return

        address = self.stack.pop()
        string = self._load_string(address)
        self.stack.append(string)
