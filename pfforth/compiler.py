"""
PFForth Compiler - Word definitions, POSTPONE, :noname, etc.
"""

import sys
from .core import ForthException


class ForthCompiler:
    """Mixin providing word compilation and definition"""
    
    def _register_compiler_words(self):
        """Register compiler words"""
        self.words['words'] = self._list_words
        self.words['see'] = self._see
        self.words['help'] = self._help_stub
        self.words['measure'] = self._measure_stub
        self.words[':measure'] = self._measure_from_stack
        self.words['forget'] = self._forget
        self.words['definitions'] = self._show_definitions
        
        self.words["'"] = self._tick
        self.words['execute'] = self._execute_word
        self.immediate_words["[']"] = self._bracket_tick
        
        self.words['throw'] = self._throw
        self.words['catch'] = self._catch
        
        self.words['defer'] = self._defer_stub
        self.words['is'] = self._is_stub
        
        self.words[':noname'] = self._noname_word
        self.words['immediate-words'] = self._list_immediate_words
        self.words['tick-demo'] = self._tick_demo
        
        self.immediate_words['immediate'] = self._immediate
        self.immediate_words['postpone'] = self._postpone
        self.immediate_words['create'] = self._create
        self.immediate_words['does>'] = self._does
        self.immediate_words['literal'] = self._literal
        self.immediate_words['['] = self._open_bracket
        self.immediate_words[']'] = self._close_bracket
        self.immediate_words['('] = self._paren_comment
        
        self._create_variable('base')
        self.variables['base'] = 10
        self._create_variable('state')
        self.variables['state'] = 0
    
    def _show_definitions(self):
        """Show all definitions in order"""
        print("=== REGISTRO DE DEFINICIONES ===")
        for i, (def_type, name) in enumerate(self._definition_order):
            print(f"{i:3d}. {def_type:10} {name}")
        return self
    
    def _list_immediate_words(self):
        print("Palabras inmediatas:", list(self.immediate_words.keys()))
        return self
    
    def _tick_demo(self):
        print("\n=== DEMOSTRACIÓN ' Y EXECUTE ===")
        print("Stack actual:", self.stack)
        all_words = [w for w in list(self.words.keys()) + list(self.immediate_words.keys())
                    if not w.startswith('_') and w not in ['tick-demo']]
        print("Palabras disponibles:", all_words[:10])
        return self
    
    def _list_words(self):
        system_words = sorted([w for w in self.words.keys() 
                               if not w.startswith('_') and self._is_system_word(w)])
        user_words = [name for (_, name) in self._definition_order if name in self.words]
        immediate_words = sorted(self.immediate_words.keys())
        variables = sorted(self.variables.keys())
        constants = sorted(self.constants.keys())
        values = sorted(self.values.keys())
        
        if system_words:
            print("Palabras:", " ".join(system_words))
        if user_words:
            print("Usuario:", " ".join(user_words))
        if immediate_words:
            print("Inmediatas:", " ".join(immediate_words))
        if variables:
            print("Variables:", " ".join(variables))
        if constants:
            print("Constantes:", " ".join(constants))
        if values:
            print("Values:", " ".join(values))
        return self
    
    def _see(self):
        if self.stack:
            word_name = self.stack.pop()
            self._see_word(word_name)
        return self
    
    def _see_word(self, word_name):
        """Display the definition of a word"""
        if word_name in self._definition_source:
            print(self._definition_source[word_name])
        elif word_name in self.words:
            print(f": {word_name} <primitiva> ;")
        elif word_name in self.immediate_words:
            print(f": {word_name} <inmediata> ; immediate")
        elif word_name in self.variables:
            print(f"variable {word_name}  \\ valor: {self.variables[word_name]}")
        elif word_name in self.constants:
            print(f"{self.constants[word_name]} constant {word_name}")
        elif word_name in self.values:
            print(f"{self.values[word_name]} value {word_name}")
        else:
            print(f"Palabra '{word_name}' no encontrada")
    
    def _help_stub(self):
        print("Usa 'help' para ver documentación")
    
    def _measure_stub(self):
        print("Error: MEASURE requiere nombre de palabra")
    
    def _measure_from_stack(self):
        """( str -- ) Mide tiempo de ejecucion de la palabra cuyo nombre esta en el stack"""
        import time
        if not self.stack:
            print("Error: :MEASURE requiere nombre de palabra en el stack")
            return
        
        word_name = self.stack.pop()
        if not isinstance(word_name, str):
            print(f"Error: :MEASURE requiere un string, recibido {type(word_name).__name__}")
            return
        
        if word_name not in self.words and word_name not in self.immediate_words:
            print(f"Error: palabra '{word_name}' no encontrada")
            return
        
        word_func = self.words.get(word_name) or self.immediate_words.get(word_name)
        
        start = time.perf_counter()
        word_func()
        elapsed = time.perf_counter() - start
        
        if elapsed < 1e-6:
            print(f"{word_name}: {elapsed * 1e9:.2f} ns")
        elif elapsed < 1e-3:
            print(f"{word_name}: {elapsed * 1e6:.2f} us")
        elif elapsed < 1:
            print(f"{word_name}: {elapsed * 1e3:.2f} ms")
        else:
            print(f"{word_name}: {elapsed:.3f} s")
    
    def _forget(self):
        if not self.stack:
            print("Error: nombre faltante para forget")
            return
        
        target_name = self.stack.pop()
        
        if self._is_system_word(target_name):
            print(f"Error: '{target_name}' es palabra del sistema")
            return
        
        target_index = None
        for i, (def_type, name) in enumerate(self._definition_order):
            if name == target_name:
                target_index = i
                break
        
        if target_index is None:
            print(f"Error: '{target_name}' no encontrada")
            return
        
        definitions_to_remove = self._definition_order[target_index:]
        for def_type, name in definitions_to_remove:
            self._remove_definition(def_type, name)
        
        self._definition_order = self._definition_order[:target_index]
        print(f"Olvidadas {len(definitions_to_remove)} definiciones desde '{target_name}'")
    
    def _remove_definition(self, def_type, name):
        """Remove a definition by type and name"""
        if def_type in ('word', 'immediate', 'code', 'created'):
            if name in self.words:
                del self.words[name]
            if name in self.immediate_words:
                del self.immediate_words[name]
        elif def_type == 'variable':
            if name in self.variables:
                del self.variables[name]
            if name in self.words:
                del self.words[name]
        elif def_type == 'constant':
            if name in self.constants:
                del self.constants[name]
            if name in self.words:
                del self.words[name]
        elif def_type == 'value':
            if name in self.values:
                del self.values[name]
            if name in self.words:
                del self.words[name]
    
    def _tick(self):
        pass
    
    def _execute_word(self):
        if self.stack:
            xt = self.stack.pop()
            if callable(xt):
                xt()
            elif isinstance(xt, str):
                if xt in self.words:
                    self.words[xt]()
                elif xt in self.immediate_words:
                    self.immediate_words[xt]()
    
    def _bracket_tick(self):
        pass
    
    def _throw(self):
        if self.stack:
            code = self.stack.pop()
            if code != 0:
                raise ForthException(code)
    
    def _catch(self):
        if len(self.stack) >= 1:
            xt = self.stack.pop()
            if isinstance(xt, tuple) and len(xt) == 3 and xt[0] == 'word':
                xt = xt[2]
            
            if not callable(xt):
                print("Error: catch requiere xt ejecutable")
                return
            saved_stack = self.stack.copy()
            saved_rstack = self.rstack.copy()
            try:
                xt()
                self.stack.append(0)
            except ForthException as e:
                self.stack = saved_stack
                self.rstack = saved_rstack
                self.stack.append(e.code)
        else:
            print("Error: catch requiere xt en pila")
    
    def _defer_stub(self):
        print("Error: DEFER requiere nombre")
    
    def _is_stub(self):
        print("Error: IS requiere xt y nombre")
    
    def _noname_word(self):
        """Start an anonymous word definition"""
        self._defining = True
        self._noname_mode = True
        self._current_definition = []
        self._current_name = None
        self._current_locals = []
        self._current_source = []
        self.variables['state'] = -1
    
    def _immediate(self):
        if self._last_defined_word:
            if self._last_defined_word in self.words:
                self.immediate_words[self._last_defined_word] = self.words[self._last_defined_word]
                del self.words[self._last_defined_word]
                for i, (def_type, name) in enumerate(self._definition_order):
                    if name == self._last_defined_word and def_type == 'word':
                        self._definition_order[i] = ('immediate', self._last_defined_word)
                        break
                print(f"'{self._last_defined_word}' marcada IMMEDIATE")
    
    def _postpone(self):
        if not self._defining:
            print("Error: POSTPONE solo en compilación")
    
    def _create(self):
        pass
    
    def _does(self):
        if not self._defining:
            print("Error: DOES> solo en compilación")
    
    def _literal(self):
        if not self._defining or self._current_definition is None:
            print("Error: LITERAL solo en compilación")
            return
        if not self.stack:
            print("Error: LITERAL requiere valor")
            return
        value = self.stack.pop()
        self._current_definition.append(('literal', value))
    
    def _open_bracket(self):
        if self._defining:
            self._bracket_mode = True
            self.variables['state'] = 0
    
    def _close_bracket(self):
        if self._defining:
            self._bracket_mode = False
            self.variables['state'] = -1
    
    def _paren_comment(self):
        pass
    
    def show_definitions(self):
        """Show all user definitions"""
        print("=== REGISTRO DE DEFINICIONES ===")
        for i, (def_type, name) in enumerate(self._definition_order):
            print(f"{i:3d}. {def_type:10} {name}")
        return self
