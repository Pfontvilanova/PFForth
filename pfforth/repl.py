"""
PFForth REPL - Interactive Read-Eval-Print Loop and DSL interface
"""

import sys
import time

from .core import ForthBase, ForthException, clear_screen
from .arithmetic import ForthArithmetic
from .stack_ops import ForthStack
from .memory import ForthMemory
from .control_flow import ForthControlFlow
from .compiler import ForthCompiler
from .io_words import ForthIO
from .persistence import ForthPersistence
from .optimizations import ForthOptimizations


class Forth(ForthBase, ForthArithmetic, ForthStack, ForthMemory, 
            ForthControlFlow, ForthCompiler, ForthIO, ForthPersistence, 
            ForthOptimizations):
    """Complete Forth interpreter combining all mixins"""
    
    def __init__(self):
        super().__init__()
        self._register_all_words()
    
    def _register_all_words(self):
        """Register all words from all mixins"""
        self._register_arithmetic_words()
        self._register_stack_words()
        self._register_memory_words()
        self._register_control_flow_words()
        self._register_compiler_words()
        self._register_io_words()
        self._register_persistence_words()
        self._register_optimization_words()
        self.words['help'] = self._help
        self.words['replit-mode'] = self._set_replit_mode
        self.words['standard-mode'] = self._set_standard_mode
        self._replit_mode = False
    
    def execute(self, text):
        """Execute Forth code"""
        tokens = self._simple_tokenize(text)
        self._execute_tokens(tokens)
        return self
    
    def _execute_tokens(self, tokens):
        """Execute a list of tokens"""
        self._input_tokens = tokens
        self._input_index = 0
        
        i = 0
        while i < len(tokens):
            if self._exit_flag:
                self._exit_flag = False
                return
            
            self._input_index = i
            token = tokens[i]
            
            if isinstance(token, tuple):
                if token[0] == 'string':
                    if self._defining and not self._bracket_mode:
                        self._current_definition.append(token)
                        self._current_source.append(f's" {token[1]}"')
                    else:
                        self.stack.append(token[1])
                elif token[0] == 'print_string':
                    if self._defining and not self._bracket_mode:
                        self._current_definition.append(token)
                        self._current_source.append(f'." {token[1]}"')
                    else:
                        print(token[1], end='')
                elif token[0] == 'literal':
                    self.stack.append(token[1])
                elif token[0] == 'cached':
                    _, name, func = token
                    func()
                elif token[0] == 'do_start':
                    loop_tokens, end_idx, is_plus = self._extract_do_block(tokens, i)
                    self._execute_do_loop(loop_tokens, is_plus)
                    i = end_idx
                    continue
                elif token[0] == 'if_start':
                    if_tokens, else_tokens, end_idx = self._extract_if_block(tokens, i)
                    self._execute_if_then_else(if_tokens, else_tokens)
                    i = end_idx
                    continue
                elif token[0] == 'begin_start':
                    loop_info = self._extract_begin_block(tokens, i)
                    self._execute_begin_structure(loop_info)
                    i = loop_info['end_idx']
                    continue
                elif token[0] == 'case_start':
                    branches, default, end_idx = self._extract_case_block(tokens, i)
                    self._execute_case(branches, default)
                    i = end_idx
                    continue
                elif token[0] == 'py_eval':
                    if self._defining and not self._bracket_mode:
                        self._current_definition.append(token)
                        self._current_source.append(f'py" {token[1]}"')
                    else:
                        self._execute_py_eval(token[1])
                    i += 1
                    continue
                elif token[0] == 'py_exec':
                    if self._defining and not self._bracket_mode:
                        self._current_definition.append(token)
                        self._current_source.append(f'py{{{token[1]}}}py')
                    else:
                        self._execute_py_exec(token[1])
                    i += 1
                    continue
                elif token[0] == 'py_inline':
                    if self._defining and not self._bracket_mode:
                        self._current_definition.append(token)
                        self._current_source.append(f'py[{token[1]}]py')
                    else:
                        self._execute_py_exec(token[1])
                    i += 1
                    continue
                i += 1
                continue
            
            token_lower = token.lower() if isinstance(token, str) else token
            
            if token == ':':
                if i + 1 < len(tokens):
                    self._current_name = tokens[i + 1]
                    self._defining = True
                    self._current_definition = []
                    self._current_locals = []
                    self._current_source = [':', tokens[i + 1]]
                    self.variables['state'] = -1
                    i += 2
                    continue
            
            
            if token == ';':
                if self._defining:
                    self._current_source.append(';')
                    self._finish_definition()
                i += 1
                continue
            
            if self._defining and not self._bracket_mode:
                self._current_source.append(token)
                
                if token in ('char', '[char]'):
                    if i + 1 < len(tokens):
                        next_token = tokens[i + 1]
                        self._current_source.append(next_token)
                        if next_token and len(next_token) > 0:
                            char_code = ord(next_token[0])
                            self._current_definition.append(('literal', char_code))
                        i += 2
                        continue
                    else:
                        print(f"Error: falta carácter después de {token}")
                        i += 1
                        continue
                
                if token == '{':
                    end_idx = i + 1
                    local_names = []
                    while end_idx < len(tokens) and tokens[end_idx] != '}':
                        t = tokens[end_idx]
                        self._current_source.append(t)
                        if t not in ('---', '-', '-'):
                            if not t.startswith('-'):
                                local_names.append(t)
                        end_idx += 1
                    if end_idx < len(tokens):
                        self._current_source.append('}')
                    self._current_locals = local_names
                    self._current_definition.append(('locals', local_names))
                    i = end_idx + 1
                    continue
                
                if token == 'to':
                    if i + 1 < len(tokens):
                        name = tokens[i + 1]
                        self._current_source.append(name)
                        if name in self._current_locals:
                            self._current_definition.append(('to_local', name))
                        elif name in self.values:
                            self._current_definition.append(('to_value', name))
                        else:
                            print(f"Error: TO requiere un VALUE o variable local, no '{name}'")
                        i += 2
                        continue
                
                if token in self.immediate_words:
                    result = self._handle_immediate_during_compile(token, tokens, i)
                    if result is not None:
                        i = result
                        continue
                    self.immediate_words[token]()
                    i += 1
                    continue
                
                if self._use_inline_cache:
                    if token in self.words:
                        self._current_definition.append(('cached', token, self.words[token]))
                    elif token in self.variables:
                        self._current_definition.append(token)
                    elif token in self.constants:
                        self._current_definition.append(('literal', self.constants[token]))
                    elif token in self.values:
                        self._current_definition.append(token)
                    elif token in self._current_locals:
                        self._current_definition.append(token)
                    elif token in self.deferred:
                        self._current_definition.append(token)
                    elif token == self._current_name:
                        self._current_definition.append(token)
                    else:
                        try:
                            num = self._parse_number(token)
                            self._current_definition.append(('literal', num))
                        except:
                            print(f"Error: palabra desconocida '{token}'")
                            self._defining = False
                            self._current_definition = []
                            self._current_name = None
                            return
                else:
                    if token in self.words or token in self.immediate_words:
                        self._current_definition.append(token)
                    elif token in self.variables or token in self.constants or token in self.values:
                        self._current_definition.append(token)
                    elif token in self._current_locals:
                        self._current_definition.append(token)
                    elif token in self.deferred:
                        self._current_definition.append(token)
                    elif token == self._current_name:
                        self._current_definition.append(token)
                    else:
                        try:
                            num = self._parse_number(token)
                            self._current_definition.append(('literal', num))
                        except:
                            print(f"Error: palabra desconocida '{token}'")
                            self._defining = False
                            self._current_definition = []
                            self._current_name = None
                            return
                i += 1
                continue
            
            if token == 'variable':
                if i + 1 < len(tokens):
                    name = tokens[i + 1]
                    self._create_variable(name)
                    self._definition_order.append(('variable', name))
                    i += 2
                    continue
            
            if token == 'constant':
                if self.stack and i + 1 < len(tokens):
                    name = tokens[i + 1]
                    value = self.stack.pop()
                    self.constants[name] = value
                    self.words[name] = lambda v=value: self.stack.append(v)
                    self._definition_order.append(('constant', name))
                    i += 2
                    continue
            
            if token == 'value':
                if self.stack and i + 1 < len(tokens):
                    name = tokens[i + 1]
                    value = self.stack.pop()
                    self.values[name] = value
                    self.words[name] = lambda n=name: self.stack.append(self.values[n])
                    self._definition_order.append(('value', name))
                    i += 2
                    continue
            
            if token == 'to':
                if self.stack and i + 1 < len(tokens):
                    name = tokens[i + 1]
                    if name in self.values:
                        self.values[name] = self.stack.pop()
                    i += 2
                    continue
            
            if token == 'defer':
                if i + 1 < len(tokens):
                    name = tokens[i + 1]
                    self.deferred[name] = None
                    self.words[name] = lambda n=name: self._execute_deferred(n)
                    self._definition_order.append(('word', name))
                    i += 2
                    continue
            
            if token == 'is':
                if self.stack and i + 1 < len(tokens):
                    name = tokens[i + 1]
                    xt = self.stack.pop()
                    if name in self.deferred or name in self.words:
                        self.deferred[name] = xt
                    i += 2
                    continue
            
            if token == "'":
                if i + 1 < len(tokens):
                    word_name = tokens[i + 1]
                    if word_name in self.words:
                        self.stack.append(self.words[word_name])
                    elif word_name in self.immediate_words:
                        self.stack.append(self.immediate_words[word_name])
                    i += 2
                    continue
            
            if token == 'create':
                if i + 1 < len(tokens):
                    name = tokens[i + 1]
                    addr = self.here
                    self._last_created_word = name
                    self._last_created_address = addr
                    self.words[name] = lambda a=addr: self.stack.append(a)
                    self._definition_order.append(('created', name))
                    i += 2
                    continue
            
            if token == 'see':
                if i + 1 < len(tokens):
                    self._see_word(tokens[i + 1])
                    i += 2
                    continue
            
            if token == 'measure':
                if i + 1 < len(tokens):
                    self._measure_word(tokens[i + 1])
                    i += 2
                    continue
            
            if token == 'forget':
                if i + 1 < len(tokens):
                    target_name = tokens[i + 1]
                    if self._is_system_word(target_name):
                        print(f"Error: '{target_name}' es una palabra del sistema")
                    else:
                        target_index = None
                        for j, (def_type, name) in enumerate(self._definition_order):
                            if name == target_name:
                                target_index = j
                                break
                        if target_index is None:
                            print(f"Error: '{target_name}' no encontrada")
                        else:
                            definitions_to_remove = self._definition_order[target_index:]
                            for def_type, name in definitions_to_remove:
                                self._remove_definition(def_type, name)
                                if name in self._definition_source:
                                    del self._definition_source[name]
                            self._definition_order = self._definition_order[:target_index]
                            print(f"Olvidadas {len(definitions_to_remove)} definiciones desde '{target_name}'")
                    i += 2
                    continue
                else:
                    print("Error: falta nombre después de forget")
                    i += 1
                    continue
            
            if token == 'import':
                if i + 1 < len(tokens):
                    self._import_code_word(tokens[i + 1])
                    i += 2
                    continue
            
            if token == 'code':
                if i + 1 < len(tokens):
                    self._code_mode = True
                    self._code_name = tokens[i + 1]
                    self._code_buffer = []
                    i += 2
                    continue
            
            if token in ('char', '[char]'):
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if next_token and len(next_token) > 0:
                        char_code = ord(next_token[0])
                        if self._defining:
                            self._current_definition.append(('literal', char_code))
                            self._current_source.append(token)
                            self._current_source.append(next_token)
                        else:
                            self.stack.append(char_code)
                        i += 2
                        continue
                    else:
                        print(f"Error: token vacío después de {token}")
                else:
                    print(f"Error: falta carácter después de {token}")
                i += 1
                continue
            
            if token == 'rmcode':
                if i + 1 < len(tokens):
                    self._rmcode(tokens[i + 1])
                    i += 2
                    continue
            
            if token == 'seecode':
                if i + 1 < len(tokens):
                    self._seecode(tokens[i + 1])
                    i += 2
                    continue
            
            old_index = self._input_index
            if token in self.words:
                self.words[token]()
            elif token in self.immediate_words:
                self.immediate_words[token]()
            elif token in self.variables:
                self.stack.append(token)
            elif token in self.constants:
                self.stack.append(self.constants[token])
            elif token in self.values:
                self.stack.append(self.values[token])
            elif token in self._current_locals if hasattr(self, '_current_locals') else False:
                if self._locals_stack:
                    self.stack.append(self._locals_stack[-1].get(token, 0))
            else:
                try:
                    num = self._parse_number(token)
                    self.stack.append(num)
                except:
                    if token:
                        print(f"? {token}")
            
            if self._input_index > old_index:
                i = self._input_index + 1
            else:
                i += 1
    
    def _handle_immediate_during_compile(self, token, tokens, i):
        """Handle immediate words during compilation"""
        if token == 'if':
            self._current_definition.append(('if_start',))
            return i + 1
        
        if token == 'else':
            self._current_definition.append(('else_marker',))
            return i + 1
        
        if token == 'then':
            self._current_definition.append(('then_marker',))
            return i + 1
        
        if token == 'do':
            self._current_definition.append(('do_start',))
            return i + 1
        
        if token == 'loop':
            self._current_definition.append(('loop_end',))
            return i + 1
        
        if token == '+loop':
            self._current_definition.append(('plusloop_end',))
            return i + 1
        
        if token == 'begin':
            self._current_definition.append(('begin_start',))
            return i + 1
        
        if token == 'until':
            self._current_definition.append(('until_end',))
            return i + 1
        
        if token == 'again':
            self._current_definition.append(('again_end',))
            return i + 1
        
        if token == 'while':
            self._current_definition.append(('while_marker',))
            return i + 1
        
        if token == 'repeat':
            self._current_definition.append(('repeat_end',))
            return i + 1
        
        if token == 'case':
            self._current_definition.append(('case_start',))
            return i + 1
        
        if token == 'of':
            self._current_definition.append(('of_marker',))
            return i + 1
        
        if token == 'endof':
            self._current_definition.append(('endof_marker',))
            return i + 1
        
        if token == 'endcase':
            self._current_definition.append(('endcase_end',))
            return i + 1
        
        if token == '[char]':
            return None
        
        if token == 'char':
            return None
        
        if token == 'recurse':
            self._current_definition.append(('recurse',))
            return i + 1
        
        if token == 'postpone':
            if i + 1 < len(tokens):
                word_to_postpone = tokens[i + 1]
                control_flow_markers = {
                    'if': ('if_start',),
                    'else': ('else_marker',),
                    'then': ('then_marker',),
                    'do': ('do_start',),
                    'loop': ('loop_end',),
                    '+loop': ('plus_loop_end',),
                    'begin': ('begin_start',),
                    'until': ('until_end',),
                    'again': ('again_end',),
                    'while': ('while_marker',),
                    'repeat': ('repeat_end',),
                    'case': ('case_start',),
                    'of': ('of_marker',),
                    'endof': ('endof_marker',),
                    'endcase': ('endcase_end',),
                    'leave': ('leave',),
                    'exit': ('exit',),
                    'recurse': ('recurse',),
                }
                if word_to_postpone in control_flow_markers:
                    self._current_definition.append(control_flow_markers[word_to_postpone])
                elif word_to_postpone in self.immediate_words:
                    self._current_definition.append((word_to_postpone,))
                else:
                    self._current_definition.append(('compile', word_to_postpone))
                return i + 2
            return i + 1
        
        return None
    
    def _finish_definition(self):
        """Finish a word definition"""
        self._defining = False
        self.variables['state'] = 0
        
        compiled_def = self._compile_definition(self._current_definition)
        local_names = self._current_locals[:]
        
        def word_action(definition=compiled_def, locals_list=local_names):
            if locals_list:
                if len(self.stack) < len(locals_list):
                    print(f"Error: no hay suficientes valores para locals")
                    return
                local_dict = {}
                for name in reversed(locals_list):
                    local_dict[name] = self.stack.pop()
                self._locals_stack.append(local_dict)
            
            try:
                self._run_compiled(definition, locals_list)
            finally:
                if locals_list:
                    self._locals_stack.pop()
        
        if self._noname_mode:
            self._noname_mode = False
            self.stack.append(word_action)
        else:
            self.words[self._current_name] = word_action
            self._definition_order.append(('word', self._current_name))
            self._definition_source[self._current_name] = ' '.join(str(t) for t in self._current_source)
            self._last_defined_word = self._current_name
        
        self._current_definition = []
        self._current_name = None
        self._current_locals = []
        self._current_source = []
    
    def _compile_definition(self, tokens):
        """Compile tokens into executable form"""
        return tokens
    
    def _run_compiled(self, compiled, local_names, is_recurse_root=True):
        """Run a compiled definition
        
        Args:
            compiled: List of compiled tokens
            local_names: List of local variable names
            is_recurse_root: If True, this is a top-level call that should set recurse context
        """
        if is_recurse_root:
            old_context = getattr(self, '_recurse_context', None)
            self._recurse_context = (compiled, local_names)
            try:
                self._run_compiled_inner(compiled, local_names)
            finally:
                self._recurse_context = old_context
        else:
            self._run_compiled_inner(compiled, local_names)
    
    def _run_compiled_inner(self, compiled, local_names):
        """Inner implementation of run_compiled"""
        i = 0
        while i < len(compiled):
            if self._exit_flag:
                return
            
            token = compiled[i]
            
            if isinstance(token, tuple):
                op = token[0]
                
                control_flow_ops = {'if_start', 'else_marker', 'then_marker', 
                                    'do_start', 'loop_end', 'plus_loop_end',
                                    'begin_start', 'until_end', 'again_end', 
                                    'while_marker', 'repeat_end',
                                    'case_start', 'of_marker', 'endof_marker', 'endcase_end',
                                    'leave', 'exit', 'recurse'}
                
                if self._defining and op in control_flow_ops:
                    self._current_definition.append(token)
                    i += 1
                    continue
                
                if op == 'literal':
                    if len(token) > 1:
                        self.stack.append(token[1])
                    else:
                        self._literal()
                elif op == 'string':
                    self.stack.append(token[1])
                elif op == 'print_string':
                    print(token[1], end='')
                elif op == 'py_eval':
                    self._execute_py_eval(token[1])
                elif op == 'py_exec':
                    self._execute_py_exec(token[1])
                elif op == 'py_inline':
                    self._execute_py_exec(token[1])
                elif op == 'cached':
                    token[2]()
                elif op == 'locals':
                    pass
                elif op == 'to_local':
                    name = token[1]
                    if self._locals_stack and self.stack:
                        self._locals_stack[-1][name] = self.stack.pop()
                elif op == 'to_value':
                    name = token[1]
                    if self.stack:
                        self.values[name] = self.stack.pop()
                elif op == 'if_start':
                    if_tokens, else_tokens, end_idx = self._extract_if_block(compiled, i)
                    self._execute_if_then_else(if_tokens, else_tokens)
                    i = end_idx
                    continue
                elif op == 'do_start':
                    loop_tokens, end_idx, is_plus = self._extract_do_block(compiled, i)
                    self._execute_do_loop(loop_tokens, is_plus)
                    i = end_idx
                    continue
                elif op == 'begin_start':
                    loop_info = self._extract_begin_block(compiled, i)
                    self._execute_begin_structure(loop_info)
                    i = loop_info['end_idx']
                    continue
                elif op == 'case_start':
                    branches, default, end_idx = self._extract_case_block(compiled, i)
                    self._execute_case(branches, default)
                    i = end_idx
                    continue
                elif op == 'recurse':
                    if hasattr(self, '_recurse_context') and self._recurse_context:
                        self._run_compiled(self._recurse_context[0], self._recurse_context[1])
                    else:
                        self._run_compiled(compiled, local_names)
                elif op == 'compile':
                    word_name = token[1]
                    if word_name == ';':
                        if self._defining:
                            self._finish_definition()
                    elif self._defining:
                        self._current_definition.append(word_name)
                    elif word_name in self.words:
                        self.words[word_name]()
                else:
                    if op in self.words:
                        self.words[op]()
                    elif op in self.immediate_words:
                        self.immediate_words[op]()
                
                i += 1
                continue
            
            if local_names and token in local_names:
                if self._locals_stack:
                    self.stack.append(self._locals_stack[-1].get(token, 0))
                i += 1
                continue
            
            if token in self.words:
                self.words[token]()
            elif token in self.immediate_words:
                self.immediate_words[token]()
            elif token in self.variables:
                self.stack.append(token)
            elif token in self.constants:
                self.stack.append(self.constants[token])
            elif token in self.values:
                self.stack.append(self.values[token])
            else:
                try:
                    num = self._parse_number(token)
                    self.stack.append(num)
                except:
                    if token:
                        print(f"? {token}")
            
            i += 1
    
    def _extract_if_block(self, tokens, start):
        """Extract IF...ELSE...THEN block"""
        if_tokens = []
        else_tokens = None
        depth = 1
        i = start + 1
        in_else = False
        
        while i < len(tokens) and depth > 0:
            token = tokens[i]
            
            if isinstance(token, tuple):
                if token[0] == 'if_start':
                    depth += 1
                    if in_else:
                        else_tokens.append(token)
                    else:
                        if_tokens.append(token)
                elif token[0] == 'else_marker' and depth == 1:
                    in_else = True
                    else_tokens = []
                elif token[0] == 'then_marker':
                    depth -= 1
                    if depth > 0:
                        if in_else:
                            else_tokens.append(token)
                        else:
                            if_tokens.append(token)
                else:
                    if in_else:
                        else_tokens.append(token)
                    else:
                        if_tokens.append(token)
            else:
                if in_else:
                    else_tokens.append(token)
                else:
                    if_tokens.append(token)
            
            i += 1
        
        return if_tokens, else_tokens, i
    
    def _extract_do_block(self, tokens, start):
        """Extract DO...LOOP block"""
        loop_tokens = []
        depth = 1
        i = start + 1
        is_plus_loop = False
        
        while i < len(tokens) and depth > 0:
            token = tokens[i]
            
            if isinstance(token, tuple):
                if token[0] == 'do_start':
                    depth += 1
                    loop_tokens.append(token)
                elif token[0] in ('loop_end', 'plusloop_end'):
                    depth -= 1
                    if depth > 0:
                        loop_tokens.append(token)
                    else:
                        is_plus_loop = (token[0] == 'plusloop_end')
                else:
                    loop_tokens.append(token)
            else:
                loop_tokens.append(token)
            
            i += 1
        
        return loop_tokens, i, is_plus_loop
    
    def _extract_begin_block(self, tokens, start):
        """Extract BEGIN...UNTIL/AGAIN/WHILE...REPEAT block"""
        i = start + 1
        depth = 1
        
        while_tokens = []
        repeat_tokens = []
        loop_type = None
        in_repeat = False
        
        while i < len(tokens) and depth > 0:
            token = tokens[i]
            
            if isinstance(token, tuple):
                if token[0] == 'begin_start':
                    depth += 1
                    if in_repeat:
                        repeat_tokens.append(token)
                    else:
                        while_tokens.append(token)
                elif token[0] == 'until_end':
                    depth -= 1
                    if depth > 0:
                        while_tokens.append(token)
                    else:
                        loop_type = 'until'
                elif token[0] == 'again_end':
                    depth -= 1
                    if depth > 0:
                        while_tokens.append(token)
                    else:
                        loop_type = 'again'
                elif token[0] == 'while_marker' and depth == 1:
                    in_repeat = True
                elif token[0] == 'repeat_end':
                    depth -= 1
                    if depth > 0:
                        repeat_tokens.append(token)
                    else:
                        loop_type = 'while_repeat'
                else:
                    if in_repeat:
                        repeat_tokens.append(token)
                    else:
                        while_tokens.append(token)
            else:
                if in_repeat:
                    repeat_tokens.append(token)
                else:
                    while_tokens.append(token)
            
            i += 1
        
        return {
            'type': loop_type,
            'while_tokens': while_tokens,
            'repeat_tokens': repeat_tokens,
            'end_idx': i
        }
    
    def _execute_begin_structure(self, loop_info):
        """Execute a BEGIN structure"""
        if loop_info['type'] == 'until':
            self._execute_begin_until(loop_info['while_tokens'])
        elif loop_info['type'] == 'again':
            self._execute_begin_again(loop_info['while_tokens'])
        elif loop_info['type'] == 'while_repeat':
            self._execute_begin_while_repeat(
                loop_info['while_tokens'],
                loop_info['repeat_tokens']
            )
    
    def _extract_case_block(self, tokens, start):
        """Extract CASE...OF...ENDOF...ENDCASE block
        
        Returns list of (test_tokens, body_tokens) for each OF branch,
        plus default_tokens for code after last ENDOF before ENDCASE.
        """
        branches = []
        default_tokens = []
        test_tokens = []
        body_tokens = []
        in_of = False
        depth = 1
        i = start + 1
        
        while i < len(tokens) and depth > 0:
            token = tokens[i]
            
            if isinstance(token, tuple):
                op = token[0]
                if op == 'case_start':
                    depth += 1
                    if in_of:
                        body_tokens.append(token)
                    else:
                        test_tokens.append(token)
                elif op == 'of_marker':
                    if depth == 1:
                        in_of = True
                        body_tokens = []
                    else:
                        body_tokens.append(token)
                elif op == 'endof_marker':
                    if depth == 1:
                        branches.append((test_tokens[:], body_tokens[:]))
                        in_of = False
                        test_tokens = []
                        body_tokens = []
                    else:
                        body_tokens.append(token)
                elif op == 'endcase_end':
                    depth -= 1
                    if depth > 0:
                        if in_of:
                            body_tokens.append(token)
                        else:
                            test_tokens.append(token)
                else:
                    if in_of:
                        body_tokens.append(token)
                    else:
                        test_tokens.append(token)
            else:
                if in_of:
                    body_tokens.append(token)
                else:
                    test_tokens.append(token)
            
            i += 1
        
        if test_tokens:
            default_tokens = test_tokens
        
        return branches, default_tokens if default_tokens else None, i
    
    def _execute_deferred(self, name):
        """Execute a deferred word"""
        xt = self.deferred.get(name)
        if xt is None:
            print(f"Error: '{name}' no inicializado")
        elif callable(xt):
            xt()
    
    def _measure_word(self, word_name):
        """Measure execution time of a word"""
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


class ForthREPL:
    """Mixin providing REPL functionality"""
    
    def _needs_parse_continuation(self, line):
        """Check if PARSE needs multiline continuation"""
        import re
        line_lower = line.lower()
        if 'parse' not in line_lower:
            return False
        
        delimiter = self._get_parse_delimiter(line)
        if not delimiter:
            return False
        
        parse_match = re.search(r'\bparse\b', line_lower)
        if not parse_match:
            return False
        
        after_parse = line[parse_match.end():]
        return delimiter not in after_parse
    
    def _get_parse_delimiter(self, line):
        """Extract the delimiter for PARSE from the line"""
        import re
        line_lower = line.lower()
        
        char_match = re.search(r'\bchar\s+(\S)', line_lower)
        if char_match:
            return char_match.group(1)
        
        if re.search(r'\bbl\b', line_lower):
            return ' '
        
        num_match = re.search(r'(\d+)\s+parse\b', line_lower)
        if num_match:
            try:
                code = int(num_match.group(1))
                if 0 <= code <= 127:
                    return chr(code)
            except:
                pass
        
        return None
    
    def _readline_input(self, prompt):
        """Alternative input using sys.stdin.readline for compatibility"""
        import sys
        sys.stdout.write(prompt)
        sys.stdout.flush()
        line = sys.stdin.readline()
        if not line:
            raise EOFError()
        return line.rstrip('\n\r')
    
    def _ipython_input(self, prompt):
        """Input using IPython's own input system for a-Shell/IPython compatibility"""
        try:
            from IPython import get_ipython
            ip = get_ipython()
            if ip is not None:
                return ip.pt_app.prompt(prompt)
        except:
            pass
        return input(prompt)
    
    def _detect_ipython(self):
        """Detect if running inside IPython"""
        try:
            from IPython import get_ipython
            return get_ipython() is not None
        except:
            return False
    
    def _set_replit_mode(self):
        """Activa modo Replit (salto de linea extra despues de comandos)"""
        self._replit_mode = True
        print("Modo Replit activado")
    
    def _set_standard_mode(self):
        """Desactiva modo Replit (sin salto de linea extra)"""
        self._replit_mode = False
        print("Modo estandar activado")
    
    def repl(self, readline_mode=False, ipython_mode=None, replit_mode=None):
        """Start interactive REPL
        
        Args:
            readline_mode: If True, use sys.stdin.readline instead of input().
            ipython_mode: If True, use IPython's prompt system. 
                         If None (default), auto-detect IPython.
                         Use this for a-Shell with IPython.
            replit_mode: If True, add extra newline after commands (for Replit console).
                        If None (default), auto-detect Replit environment.
        """
        print("PFForth v2.0 - Modular Edition")
        print("Escribe 'bye' para salir, 'help' para ayuda")
        
        if ipython_mode is None:
            ipython_mode = self._detect_ipython()
        
        if replit_mode is None:
            import os
            replit_mode = 'REPL_ID' in os.environ or 'REPLIT_ENVIRONMENT' in os.environ
        
        self._replit_mode = replit_mode
        
        if ipython_mode:
            get_input = self._ipython_input
            print("(Modo IPython detectado)")
        elif readline_mode:
            get_input = self._readline_input
            print("(Modo readline activado)")
        else:
            get_input = input
        
        if replit_mode:
            print("(Modo Replit - usa 'standard-mode' para desactivar)")
        print()
        
        
        while True:
            try:
                if self._code_mode:
                    prompt = "CODE> "
                elif self._defining:
                    prompt = "...> "
                else:
                    prompt = "OK> "
                
                try:
                    line = get_input(prompt)
                except EOFError:
                    break
                
                line_stripped = line.strip()
                
                if line_stripped.lower() == 'bye':
                    print("Adios!")
                    break
                
                if line_stripped.lower() == 'abort':
                    self.stack.clear()
                    self.rstack.clear()
                    print("Pilas limpiadas")
                    continue
                
                if line_stripped.lower() in ('stack', '.s'):
                    self._dot_s()
                    continue
                
                if line_stripped.lower() in ('cls', 'page'):
                    clear_screen()
                    continue
                
                if self._code_mode:
                    if line_stripped.lower() == 'endcode':
                        code_text = '\n'.join(self._code_buffer)
                        self._code_mode = False
                        self._create_code_word(self._code_name, code_text)
                        self._code_buffer = []
                        self._code_name = None
                    else:
                        self._code_buffer.append(line)
                    continue
                
                if 'r|' in line and '|' not in line[line.find('r|')+2:]:
                    accumulated = line
                    while True:
                        try:
                            cont_line = get_input("... ")
                            accumulated += '\n' + cont_line
                            if '|' in cont_line:
                                break
                        except (KeyboardInterrupt, EOFError):
                            print("\nMultilinea cancelado")
                            accumulated = ""
                            break
                    if accumulated:
                        self.execute(accumulated)
                elif 'py{' in line and '}py' not in line[line.find('py{')+3:]:
                    accumulated = line
                    while True:
                        try:
                            cont_line = get_input("py{> ")
                            accumulated += '\n' + cont_line
                            if '}py' in cont_line:
                                break
                        except (KeyboardInterrupt, EOFError):
                            print("\nMultilinea cancelado")
                            accumulated = ""
                            break
                    if accumulated:
                        self.execute(accumulated)
                elif 'py[' in line and ']py' not in line[line.find('py[')+3:]:
                    accumulated = line
                    while True:
                        try:
                            cont_line = get_input("py[> ")
                            accumulated += '\n' + cont_line
                            if ']py' in cont_line:
                                break
                        except (KeyboardInterrupt, EOFError):
                            print("\nMultilinea cancelado")
                            accumulated = ""
                            break
                    if accumulated:
                        self.execute(accumulated)
                elif self._needs_parse_continuation(line):
                    delimiter = self._get_parse_delimiter(line)
                    if delimiter:
                        accumulated = line
                        while True:
                            try:
                                cont_line = get_input("... ")
                                accumulated += '\n' + cont_line
                                if delimiter in cont_line:
                                    break
                            except (KeyboardInterrupt, EOFError):
                                print("\nMultilinea cancelado")
                                accumulated = ""
                                break
                        if accumulated:
                            self.execute(accumulated)
                    else:
                        self.execute(line)
                else:
                    self.execute(line)
                if self._replit_mode:
                    print()
                
            except KeyboardInterrupt:
                print("\n(Ctrl+C) Usa 'bye' para salir")
            except Exception as e:
                print(f"Error: {e}")
        
        return self


class InteractiveForth(Forth, ForthREPL):
    """Complete Interactive Forth with REPL and DSL support"""
    
    def __init__(self):
        super().__init__()
    
    def __repr__(self):
        return ""
    
    def __call__(self, *values):
        for v in values:
            self.stack.append(v)
        return self
    
    def push(self, *values):
        for v in values:
            self.stack.append(v)
        return self
    
    def pop(self):
        return self.stack.pop() if self.stack else None
    
    def peek(self):
        return self.stack[-1] if self.stack else None
    
    def dup(self):
        self._dup()
        return self
    
    def drop(self):
        self._drop()
        return self
    
    def swap(self):
        self._swap()
        return self
    
    def over(self):
        self._over()
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
    
    def pick(self):
        self.words['pick']()
        return self
    
    def roll(self):
        self.words['roll']()
        return self
    
    def two_dup(self):
        self.words['2dup']()
        return self
    
    def two_drop(self):
        self.words['2drop']()
        return self
    
    def two_swap(self):
        self.words['2swap']()
        return self
    
    def two_over(self):
        self.words['2over']()
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
    
    def plus(self):
        self.words['+']()
        return self
    
    def add(self):
        return self.plus()
    
    def minus(self):
        self.words['-']()
        return self
    
    def sub(self):
        return self.minus()
    
    def mult(self):
        self.words['*']()
        return self
    
    def mul(self):
        return self.mult()
    
    def div(self):
        self.words['/']()
        return self
    
    def mod(self):
        self.words['mod']()
        return self
    
    def divmod(self):
        self.words['/mod']()
        return self
    
    def power(self):
        self.words['**']()
        return self
    
    def abs_(self):
        self.words['abs']()
        return self
    
    def negate(self):
        self.words['negate']()
        return self
    
    def min_(self):
        self.words['min']()
        return self
    
    def max_(self):
        self.words['max']()
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
    
    def exp(self):
        self.words['exp']()
        return self
    
    def floor(self):
        self.words['floor']()
        return self
    
    def ceil(self):
        self.words['ceil']()
        return self
    
    def round_(self):
        self.words['round']()
        return self
    
    def pi(self):
        self.words['pi']()
        return self
    
    def e(self):
        self.words['e']()
        return self
    
    def equal(self):
        self.words['=']()
        return self
    
    def not_equal(self):
        self.words['<>']()
        return self
    
    def less(self):
        self.words['<']()
        return self
    
    def greater(self):
        self.words['>']()
        return self
    
    def less_equal(self):
        self.words['<=']()
        return self
    
    def greater_equal(self):
        self.words['>=']()
        return self
    
    def and_(self):
        self.words['and']()
        return self
    
    def or_(self):
        self.words['or']()
        return self
    
    def not_(self):
        self.words['not']()
        return self
    
    def xor(self):
        self.words['xor']()
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
    
    def fill(self, addr=None, n=None, byte=None):
        if addr is not None and n is not None and byte is not None:
            self.stack.extend([addr, n, byte])
        self.words['fill']()
        return self
    
    def erase(self, addr=None, n=None):
        if addr is not None and n is not None:
            self.stack.extend([addr, n])
        self.words['erase']()
        return self
    
    def dump_memory(self, addr=None, n=None):
        if addr is not None and n is not None:
            self.stack.extend([addr, n])
        self.words['dump']()
        return self
    
    def dot(self):
        self.words['.']()
        return self
    
    def dot_s(self):
        self.words['.s']()
        return self
    
    def show(self):
        return self.dot_s()
    
    def dot_r(self, width=None):
        if width is not None:
            self.stack.append(width)
        self.words['.r']()
        return self
    
    def cr(self):
        self.words['cr']()
        return self
    
    def cls(self):
        clear_screen()
        return self
    
    def page(self):
        clear_screen()
        return self
    
    def space(self):
        self.words['space']()
        return self
    
    def emit(self):
        self.words['emit']()
        return self
    
    def type(self):
        self.words['type']()
        return self
    
    def key(self):
        self.words['key']()
        return self
    
    def bl(self):
        self.words['bl']()
        return self
    
    def pad(self):
        self.words['pad']()
        return self
    
    def accept(self, addr=None, length=None):
        if addr is not None and length is not None:
            self.stack.extend([addr, length])
        elif addr is not None:
            self.stack.append(addr)
        self.words['accept']()
        return self
    
    def clear(self):
        self.stack.clear()
        return self
    
    def run(self, code):
        return self.execute(code)
    
    def define(self, name, body):
        self.execute(f": {name} {body} ;")
        return self
    
    def var(self, name, value=0):
        self.execute(f"variable {name}")
        if value != 0:
            self.variables[name] = value
        return self
    
    def variable(self, name):
        self.execute(f"variable {name}")
        return self
    
    def const(self, name, value):
        self.stack.append(value)
        self.execute(f"constant {name}")
        return self
    
    def constant(self, name, value):
        return self.const(name, value)
    
    def value(self, name, val):
        self.stack.append(val)
        self.execute(f"value {name}")
        return self
    
    def get_var(self, name):
        return self.variables.get(name, 0)
    
    def set_var(self, name, val):
        if name in self.variables:
            self.variables[name] = val
        return self
    
    def immediate(self):
        self.words['immediate']()
        return self
    
    def forget(self, name=None):
        if name is not None:
            self.stack.append(name)
        self.words['forget']()
        return self
    
    def tick(self, word_name=None):
        if word_name is not None:
            self.stack.append(word_name)
        self.words["'"]()
        return self
    
    def execute_word(self):
        self.words['execute']()
        return self
    
    def evaluate(self):
        self.words['evaluate']()
        return self
    
    def list_words(self):
        self._list_words()
        return self
    
    def help(self):
        return self._help()
    
    def measure(self, word_name):
        start_time = time.perf_counter()
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
        time_str, _ = self._format_time(elapsed)
        self.stack.append(elapsed)
        print(f"Tiempo de '{word_name}': {time_str}")
        return self
    
    def negativo(self, value):
        self.stack.append(-value)
        return self
    
    def dot(self):
        """DSL: imprime y consume el tope de la pila"""
        self._dot()
        return self
    
    def __getattr__(self, name):
        """Permite acceder a palabras Forth como métodos Python"""
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        if name in self.words:
            def wrapper(*args):
                if args:
                    self.stack.extend(args)
                self.words[name]()
                return self
            return wrapper
        elif name in self.immediate_words:
            def wrapper(*args):
                if args:
                    self.stack.extend(args)
                self.immediate_words[name]()
                return self
            return wrapper
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def _execute_py_eval(self, code):
        """Evaluate Python expression and push result to stack"""
        if not hasattr(self, 'shared'):
            self.shared = {}
        env = {
            'f': self,
            'forth': self,
            'stack': self.stack,
            'shared': self.shared,
            'push': lambda v: self.stack.append(v),
            'pop': lambda: self.stack.pop() if self.stack else 0,
        }
        try:
            result = eval(code, env)
            if result is not None:
                self.stack.append(result)
        except Exception as e:
            print(f"Error py\": {e}")
    
    def _execute_py_exec(self, code):
        """Execute Python code block"""
        if not hasattr(self, 'shared'):
            self.shared = {}
        code = code.strip()
        env = {
            'f': self,
            'forth': self,
            'stack': self.stack,
            'shared': self.shared,
            'push': lambda v: self.stack.append(v),
            'pop': lambda: self.stack.pop() if self.stack else 0,
            'execute': lambda text: self.execute(text),
        }
        try:
            exec(code, env)
        except Exception as e:
            print(f"Error py{{}}: {e}")
    
    def _help(self):
        print("\n" + "=" * 70)
        print("PFFORTH - Python Forth Interpreter v2.0 (Modular)")
        print("Pere Font 2025")
        print("=" * 70)
        print("\n  Aritmetica: + - * / /mod mod abs negate min max 1+ 1-")
        print("  Comparacion: = <> < > <= >= 0= 0< 0>")
        print("  Logica: and or xor not invert lshift rshift")
        print("  Matematicas: sin cos tan sqrt log ln exp floor ceil round pi e")
        print("\n  Pila: dup ?dup drop swap over rot -rot nip tuck pick roll depth")
        print("  Pila doble: 2dup 2drop 2swap 2over")
        print("  Pila retorno: >r r> r@")
        print("\n  Memoria: @ ! c@ c! m@ m! +! ? fill erase move cmove dump")
        print("  Definicion: variable constant value to create does>")
        print("  Palabras: : ; immediate postpone recurse ' execute")
        print("\n  Control: if else then do loop +loop i j k leave exit")
        print("  Bucles: begin until again while repeat")
        print("  Switch: case of endof endcase")
        print("\n  I/O: emit key type cr space . .r .s")
        print("  Strings: .\" s\" s' r|")
        print("\n  Python Interop (palabras Forth):")
        print("    py\" expr \"     - Evalua expresion Python, pone resultado en stack")
        print("    py{ code }py   - Ejecuta bloque Python multilinea")
        print("    py[ code ]py   - Codigo Python dentro de definiciones Forth")
        print("    py-var! py-var@ - Guardar/leer variables compartidas")
        print("    py-run         - Ejecutar archivo .py")
        print("  Contexto Python (dentro de py{ py[ py-run):")
        print("    f.stack        - Lista: la pila de Forth")
        print("    f.shared       - Dict: variables compartidas (py-var!/py-var@)")
        print("    f.execute(s)   - Ejecutar codigo Forth desde Python")
        print("    push(v), pop() - Funciones auxiliares para la pila")
        print("\n  File Wordset:")
        print("    open-file close-file create-file delete-file")
        print("    read-file read-line write-file write-line")
        print("    file-position reposition-file file-size file-exists?")
        print("\n  Sistema: words see help measure forget bye abort")
        print("  Optimizacion: cache-on cache-off cache?")
        print("  Persistencia: save load lssave code endcode import lscode")
        print("\n" + "=" * 70)
        print("Usa 'words' para ver todas las palabras disponibles")
        print("=" * 70)
    
    def dsl_methods(self):
        print("=" * 70)
        print("METODOS DSL DISPONIBLES (para uso desde Python)")
        print("=" * 70)
        dsl_categories = {
            "Pila basica": [
                ("push(*valores)", "Anade valores a la pila"),
                ("pop()", "Retira y retorna el tope de la pila"),
                ("peek()", "Retorna el tope sin retirarlo"),
                ("dup()", "Duplica el tope"),
                ("drop()", "Descarta el tope"),
                ("swap()", "Intercambia los dos superiores"),
                ("over()", "Copia el segundo sobre el tope"),
                ("rot()", "Rota los tres superiores"),
                ("nip()", "Descarta el segundo"),
                ("tuck()", "Copia tope debajo del segundo"),
                ("depth()", "Pone profundidad en pila"),
                ("pick()", "Copia n-esimo elemento"),
                ("roll()", "Mueve n-esimo al tope"),
            ],
            "Pila doble": [
                ("two_dup()", "Duplica par superior"),
                ("two_drop()", "Descarta par superior"),
                ("two_swap()", "Intercambia dos pares"),
                ("two_over()", "Copia segundo par"),
            ],
            "Pila de retorno": [
                ("to_r()", "Mueve a pila de retorno (>r)"),
                ("from_r()", "Trae de pila de retorno (r>)"),
                ("r_fetch()", "Copia de pila de retorno (r@)"),
            ],
            "Aritmetica": [
                ("plus()", "Suma (+)"),
                ("minus()", "Resta (-)"),
                ("mult()", "Multiplicacion (*)"),
                ("div()", "Division (/)"),
                ("mod()", "Modulo"),
                ("divmod()", "Division y modulo"),
                ("power()", "Potencia (**)"),
                ("abs_()", "Valor absoluto"),
                ("negate()", "Cambia signo"),
                ("min_()", "Minimo"),
                ("max_()", "Maximo"),
            ],
            "Matematicas": [
                ("sin()", "Seno"),
                ("cos()", "Coseno"),
                ("tan()", "Tangente"),
                ("sqrt()", "Raiz cuadrada"),
                ("log()", "Logaritmo base 10"),
                ("ln()", "Logaritmo natural"),
                ("exp()", "Exponencial"),
                ("floor()", "Redondeo hacia abajo"),
                ("ceil()", "Redondeo hacia arriba"),
                ("round_()", "Redondeo"),
                ("pi()", "Constante pi"),
                ("e()", "Constante e"),
            ],
            "Comparacion": [
                ("equal()", "Igual (=)"),
                ("not_equal()", "Distinto (<>)"),
                ("less()", "Menor (<)"),
                ("greater()", "Mayor (>)"),
                ("less_equal()", "Menor o igual (<=)"),
                ("greater_equal()", "Mayor o igual (>=)"),
            ],
            "Logica": [
                ("and_()", "AND logico"),
                ("or_()", "OR logico"),
                ("not_()", "NOT logico"),
                ("xor()", "XOR"),
                ("lshift()", "Desplazar bits izquierda"),
                ("rshift()", "Desplazar bits derecha"),
                ("invert()", "Invertir bits"),
            ],
            "Memoria": [
                ("here()", "Direccion actual"),
                ("allot(n)", "Reserva n bytes"),
                ("comma(v)", "Almacena v y avanza"),
                ("memory_fetch(addr)", "Lee de memoria (m@)"),
                ("memory_store(v, addr)", "Escribe en memoria (m!)"),
                ("c_fetch(addr)", "Lee byte (c@)"),
                ("c_store(v, addr)", "Escribe byte (c!)"),
                ("fill(addr, n, byte)", "Llena memoria"),
                ("erase(addr, n)", "Borra memoria"),
                ("dump_memory(addr, n)", "Muestra memoria"),
            ],
            "E/S": [
                ("dot()", "Imprime tope (.)"),
                ("dot_s()", "Muestra pila (.s)"),
                ("dot_r()", "Imprime con ancho (.r)"),
                ("cr()", "Nueva linea"),
                ("space()", "Imprime espacio"),
                ("emit()", "Imprime caracter"),
                ("type()", "Imprime cadena"),
                ("key()", "Lee caracter"),
            ],
            "Definiciones": [
                ("constant(nombre, valor)", "Crea constante"),
                ("variable(nombre)", "Crea variable"),
                ("value(nombre, valor)", "Crea value"),
                ("set_var(nombre, valor)", "Establece valor de variable/value"),
                ("get_var(nombre)", "Obtiene valor de variable/value"),
                ("immediate()", "Marca ultima palabra como inmediata"),
                ("forget(nombre)", "Olvida definicion"),
            ],
            "Ejecucion": [
                ("execute_word()", "Ejecuta xt de la pila"),
                ("evaluate()", "Ejecuta codigo Forth de cadena"),
            ],
            "Sistema": [
                ("list_words()", "Lista palabras Forth"),
                ("dsl_methods()", "Lista metodos DSL (este)"),
                ("help()", "Ayuda general"),
                ("measure(word)", "Mide tiempo de ejecucion"),
            ],
        }
        for category, methods in dsl_categories.items():
            print(f"\n{category}:")
            for name, desc in methods:
                print(f"  {name:25} - {desc}")
        print("\n" + "=" * 70)
        print("Uso: f.push(10, 20).plus().dot()  # Encadenamiento de metodos")
        print("     f(10, 20).plus().dot()       # Sintaxis abreviada")
        print("=" * 70)
        return self


if __name__ == '__main__':
    forth = InteractiveForth()
    forth.repl()
