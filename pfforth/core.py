"""
PFForth Core - Base class with fundamental infrastructure
- Exception class
- Stack and dictionary management
- Parser/tokenizer
- Base initialization
"""

import math
import os
import sys
import time


class ForthException(Exception):
    """Exception for THROW/CATCH mechanism"""
    def __init__(self, code):
        self.code = code
        super().__init__(f"THROW {code}")


def clear_screen():
    """Clears the terminal screen"""
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')


class ForthBase:
    """Base mixin providing core infrastructure"""
    
    def __init__(self):
        self.stack = []
        self.rstack = []
        self.words = {}
        self.variables = {}
        self.constants = {}
        self.values = {}
        self.deferred = {}
        self.immediate_words = {}
        
        self._definition_order = []
        self._definition_source = {}
        self._defining = False
        self._current_definition = []
        self._current_name = None
        self._current_source = []
        self._last_defined_word = None
        self._noname_mode = False
        
        try:
            self._base_dir = os.path.dirname(os.path.abspath(__file__))
            self._base_dir = os.path.dirname(self._base_dir)
        except NameError:
            self._base_dir = os.path.abspath(os.getcwd())
        
        self._memory_size = 65536
        self._pad_size = 256
        self.memory = [0] * self._memory_size
        self.here = self._pad_size
        
        self._tick_mode = False
        self._compiling_tick = False
        self._bracket_mode = False
        
        self._loop_stack = []
        self._leave_flag = False
        self._exit_flag = False
        
        self._control_stack = []
        
        self._last_created_word = None
        self._last_created_address = None
        
        self._input_tokens = []
        self._input_index = 0
        
        self._code_mode = False
        self._code_name = None
        self._code_buffer = []
        
        self._file_handles = {}
        self._next_fileid = 1
        
        self._use_inline_cache = True
        
        self._locals_stack = []
        self._current_locals = []
        
        self._register_core_words()
    
    def _register_core_words(self):
        """Register core words - to be extended by mixins"""
        pass
    
    def _is_immediate(self, word_name):
        """Check if a word is immediate"""
        return word_name in self.immediate_words
    
    def _lookup_word(self, word_name):
        """Look up a word and return (func, is_immediate)"""
        if word_name in self.immediate_words:
            return (self.immediate_words[word_name], True)
        elif word_name in self.words:
            return (self.words[word_name], False)
        return (None, False)
    
    def _is_system_word(self, name):
        """Check if a word is a system word (not user-defined)"""
        user_words = {word_name for (_, word_name) in self._definition_order}
        if name in user_words:
            return False
        is_in_dictionaries = (name in self.words or 
                              name in self.immediate_words or 
                              name in self.variables or 
                              name in self.constants or 
                              name in self.values)
        return is_in_dictionaries
    
    def _create_variable(self, name):
        """Create a variable"""
        self.variables[name] = 0
        def var_action():
            self.stack.append(name)
        self.words[name] = var_action
    
    def _parse_number(self, token):
        """Parse a token as a number, considering current base"""
        base = self.variables.get('base', 10)
        
        if token.startswith('0x') or token.startswith('0X'):
            return int(token, 16)
        if token.startswith('0b') or token.startswith('0B'):
            return int(token, 2)
        if token.startswith('0o') or token.startswith('0O'):
            return int(token, 8)
        
        if '.' in token or 'e' in token.lower():
            return float(token)
        
        if base == 10:
            return int(token)
        else:
            return int(token, base)
    
    def _simple_tokenize(self, text):
        """Simple tokenizer that handles strings and comments"""
        tokens = []
        i = 0
        n = len(text)
        
        while i < n:
            if text[i].isspace():
                i += 1
                continue
            
            if i < n - 1 and text[i:i+2] == '."':
                i += 2
                while i < n and text[i].isspace():
                    i += 1
                start = i
                while i < n and text[i] != '"':
                    i += 1
                string_content = text[start:i]
                tokens.append(('print_string', string_content))
                if i < n:
                    i += 1
                continue
            
            if i < n - 1 and text[i:i+2] == 's"':
                i += 2
                while i < n and text[i].isspace():
                    i += 1
                start = i
                while i < n and text[i] != '"':
                    i += 1
                string_content = text[start:i]
                tokens.append(('string', string_content))
                if i < n:
                    i += 1
                continue
            
            if i < n - 1 and text[i:i+2] == "s'":
                i += 2
                while i < n and text[i].isspace():
                    i += 1
                start = i
                while i < n and text[i] != "'":
                    i += 1
                string_content = text[start:i]
                tokens.append(('string', string_content))
                if i < n:
                    i += 1
                continue
            
            if i < n - 1 and text[i:i+2] == "r|":
                i += 2
                start = i
                while i < n and text[i] != '|':
                    i += 1
                string_content = text[start:i]
                tokens.append(('string', string_content))
                if i < n:
                    i += 1
                continue
            
            if i < n - 2 and text[i:i+3] == 'py"':
                i += 3
                while i < n and text[i].isspace():
                    i += 1
                start = i
                while i < n and text[i] != '"':
                    i += 1
                py_code = text[start:i]
                tokens.append(('py_eval', py_code))
                if i < n:
                    i += 1
                continue
            
            if i < n - 2 and text[i:i+3] == 'py{':
                i += 3
                start = i
                end_marker = '}py'
                end_pos = text.find(end_marker, i)
                if end_pos != -1:
                    py_code = text[start:end_pos]
                    tokens.append(('py_exec', py_code))
                    i = end_pos + len(end_marker)
                else:
                    py_code = text[start:]
                    tokens.append(('py_exec_incomplete', py_code))
                    i = n
                continue
            
            if i < n - 2 and text[i:i+3] == 'py[':
                i += 3
                start = i
                end_marker = ']py'
                end_pos = text.find(end_marker, i)
                if end_pos != -1:
                    py_code = text[start:end_pos]
                    tokens.append(('py_inline', py_code))
                    i = end_pos + len(end_marker)
                else:
                    py_code = text[start:]
                    tokens.append(('py_inline', py_code))
                    i = n
                continue
            
            if text[i] == '(' and (i + 1 >= n or text[i + 1].isspace()):
                i += 1
                depth = 1
                while i < n and depth > 0:
                    if text[i] == '(':
                        depth += 1
                    elif text[i] == ')':
                        depth -= 1
                    i += 1
                continue
            
            if text[i] == '\\':
                while i < n and text[i] != '\n':
                    i += 1
                continue
            
            start = i
            while i < n and not text[i].isspace():
                i += 1
            token = text[start:i]
            if token:
                tokens.append(token)
        
        return tokens
