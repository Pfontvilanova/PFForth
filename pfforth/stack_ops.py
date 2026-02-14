"""
PFForth Stack Operations - Stack manipulation words
"""

import sys


class ForthStack:
    """Mixin providing stack manipulation operations"""
    
    def _register_stack_words(self):
        """Register stack words"""
        self.words['dup'] = self._dup
        self.words['?dup'] = self._qdup
        self.words['drop'] = self._drop
        self.words['swap'] = self._swap
        self.words['over'] = self._over
        self.words['rot'] = self._rot
        self.words['-rot'] = self._nrot
        self.words['nip'] = self._nip
        self.words['tuck'] = self._tuck
        
        self.words['2dup'] = self._2dup
        self.words['2drop'] = self._2drop
        self.words['2swap'] = self._2swap
        self.words['2over'] = self._2over
        
        self.words['pick'] = self._pick
        self.words['roll'] = self._roll
        self.words['depth'] = self._depth
        
        self.words['>r'] = self._to_r
        self.words['r>'] = self._from_r
        self.words['r@'] = self._r_fetch
        
        self.words['.'] = self._dot
        self.words['.r'] = self._dot_r
        self.words['.s'] = self._dot_s
        self.words['clear'] = self._clear_stack
    
    def _dup(self):
        if self.stack:
            self.stack.append(self.stack[-1])
    
    def _qdup(self):
        if self.stack and self.stack[-1] != 0:
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
    
    def _rot(self):
        if len(self.stack) >= 3:
            c = self.stack.pop()
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.extend([b, c, a])
    
    def _nrot(self):
        if len(self.stack) >= 3:
            c = self.stack.pop()
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.extend([c, a, b])
    
    def _nip(self):
        if len(self.stack) >= 2:
            a = self.stack.pop()
            self.stack.pop()
            self.stack.append(a)
    
    def _tuck(self):
        if len(self.stack) >= 2:
            a = self.stack.pop()
            b = self.stack.pop()
            self.stack.extend([a, b, a])
    
    def _2dup(self):
        if len(self.stack) >= 2:
            self.stack.extend([self.stack[-2], self.stack[-1]])
    
    def _2drop(self):
        if len(self.stack) >= 2:
            self.stack.pop()
            self.stack.pop()
    
    def _2swap(self):
        if len(self.stack) >= 4:
            a = self.stack.pop()
            b = self.stack.pop()
            c = self.stack.pop()
            d = self.stack.pop()
            self.stack.extend([b, a, d, c])
    
    def _2over(self):
        if len(self.stack) >= 4:
            self.stack.extend([self.stack[-4], self.stack[-3]])
    
    def _pick(self):
        if self.stack:
            n = int(self.stack.pop())
            if n < len(self.stack):
                self.stack.append(self.stack[-(n+1)])
    
    def _roll(self):
        if self.stack:
            n = int(self.stack.pop())
            if n < len(self.stack):
                val = self.stack.pop(-(n+1))
                self.stack.append(val)
    
    def _depth(self):
        self.stack.append(len(self.stack))
    
    def _to_r(self):
        if self.stack:
            self.rstack.append(self.stack.pop())
    
    def _from_r(self):
        if self.rstack:
            self.stack.append(self.rstack.pop())
    
    def _r_fetch(self):
        if self.rstack:
            self.stack.append(self.rstack[-1])
    
    def _dot(self):
        if self.stack:
            value = self.stack.pop()
            base = self.variables.get('base', 10)
            try:
                if isinstance(value, float) and value != int(value):
                    print(value, end=' ')
                    sys.stdout.flush()
                    return
                int_value = int(value)
            except (ValueError, TypeError):
                print(value, end=' ')
                sys.stdout.flush()
                return
            
            if base == 16:
                print(format(int_value, 'x'), end=' ')
            elif base == 2:
                print(format(int_value, 'b'), end=' ')
            elif base == 8:
                print(format(int_value, 'o'), end=' ')
            else:
                print(int_value, end=' ')
            sys.stdout.flush()
    
    def _dot_r(self):
        if len(self.stack) >= 2:
            width = int(self.stack.pop())
            n = self.stack.pop()
            base = self.variables.get('base', 10)
            try:
                int_value = int(n)
            except (ValueError, TypeError):
                print(str(n).rjust(width), end=' ')
                sys.stdout.flush()
                return
            
            if base == 16:
                num_str = format(int_value, 'x')
            elif base == 2:
                num_str = format(int_value, 'b')
            elif base == 8:
                num_str = format(int_value, 'o')
            else:
                num_str = str(int_value)
            
            print(num_str.rjust(width), end=' ')
            sys.stdout.flush()
    
    def _format_value(self, item, base):
        """Format a value for display, preserving floats"""
        if isinstance(item, float):
            if item == int(item):
                return str(int(item))
            else:
                return str(item)
        try:
            int_value = int(item)
            if base == 16:
                return format(int_value, 'x')
            elif base == 2:
                return format(int_value, 'b')
            elif base == 8:
                return format(int_value, 'o')
            else:
                return str(int_value)
        except (ValueError, TypeError):
            return str(item)
    
    def _dot_s(self):
        base = self.variables.get('base', 10)
        formatted_stack = [self._format_value(item, base) for item in self.stack]
        
        print(f"<{len(self.stack)}> {formatted_stack}")
        
        if self.rstack:
            formatted_rstack = [self._format_value(item, base) for item in self.rstack]
            print(f"R:<{len(self.rstack)}> {formatted_rstack}")
        return self
    
    def _clear_stack(self):
        self.stack.clear()
        return self
