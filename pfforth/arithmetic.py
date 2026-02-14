"""
PFForth Arithmetic - Mathematical operations
"""

import math
import sys


class ForthArithmetic:
    """Mixin providing arithmetic operations"""
    
    def _register_arithmetic_words(self):
        """Register arithmetic words"""
        self.words['+'] = self._plus
        self.words['-'] = self._minus
        self.words['*'] = self._mult
        self.words['/'] = self._div
        self.words['/mod'] = self._divmod
        self.words['mod'] = self._mod
        self.words['1+'] = self._one_plus
        self.words['1-'] = self._one_minus
        self.words['2*'] = self._two_mult
        self.words['2/'] = self._two_div
        
        self.words['0='] = self._zero_equal
        self.words['0<'] = self._zero_less
        self.words['0>'] = self._zero_greater
        
        self.words['='] = self._equal
        self.words['<>'] = self._not_equal
        self.words['<'] = self._less
        self.words['>'] = self._greater
        self.words['<='] = self._less_equal
        self.words['>='] = self._greater_equal
        
        self.words['and'] = self._and
        self.words['or'] = self._or
        self.words['xor'] = self._xor
        self.words['not'] = self._not
        self.words['invert'] = self._invert
        self.words['lshift'] = self._lshift
        self.words['rshift'] = self._rshift
        
        self.words['abs'] = self._abs
        self.words['negate'] = self._negate
        self.words['min'] = self._min
        self.words['max'] = self._max
        
        self.words['sin'] = self._sin
        self.words['cos'] = self._cos
        self.words['tan'] = self._tan
        self.words['asin'] = self._asin
        self.words['acos'] = self._acos
        self.words['atan'] = self._atan
        self.words['sqrt'] = self._sqrt
        self.words['log'] = self._log
        self.words['ln'] = self._ln
        self.words['exp'] = self._exp
        self.words['floor'] = self._floor
        self.words['ceil'] = self._ceil
        self.words['round'] = self._round
        self.words['pi'] = self._pi
        self.words['e'] = self._e
        self.words['**'] = self._power
        
        self.immediate_words['decimal'] = self._set_base_decimal
        self.immediate_words['hex'] = self._set_base_hex
        self.immediate_words['binary'] = self._set_base_binary
    
    def _power(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(a ** b)
    
    def _set_base_decimal(self):
        self.variables['base'] = 10
    
    def _set_base_hex(self):
        self.variables['base'] = 16
    
    def _set_base_binary(self):
        self.variables['base'] = 2
    
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
                if isinstance(a, int) and isinstance(b, int):
                    self.stack.append(a // b)
                else:
                    self.stack.append(a / b)
            else:
                print("Error: division by zero")
                self.stack.extend([a, b])
    
    def _divmod(self):
        if len(self.stack) >= 2:
            divisor = self.stack.pop()
            dividendo = self.stack.pop()
            if divisor != 0:
                resto = dividendo % divisor
                cociente = dividendo // divisor
                self.stack.append(resto)
                self.stack.append(cociente)
            else:
                print("Error: division by zero")
                self.stack.extend([dividendo, divisor])
    
    def _mod(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            if b != 0:
                self.stack.append(a % b)
            else:
                print("Error: division by zero")
                self.stack.extend([a, b])
    
    def _one_plus(self):
        if self.stack:
            self.stack.append(self.stack.pop() + 1)
    
    def _one_minus(self):
        if self.stack:
            self.stack.append(self.stack.pop() - 1)
    
    def _two_mult(self):
        if self.stack:
            self.stack.append(self.stack.pop() * 2)
    
    def _two_div(self):
        if self.stack:
            self.stack.append(self.stack.pop() / 2)
    
    def _zero_equal(self):
        if self.stack:
            self.stack.append(-1 if self.stack.pop() == 0 else 0)
    
    def _zero_less(self):
        if self.stack:
            self.stack.append(-1 if self.stack.pop() < 0 else 0)
    
    def _zero_greater(self):
        if self.stack:
            self.stack.append(-1 if self.stack.pop() > 0 else 0)
    
    def _equal(self):
        if len(self.stack) >= 2:
            self.stack.append(-1 if self.stack.pop() == self.stack.pop() else 0)
    
    def _not_equal(self):
        if len(self.stack) >= 2:
            self.stack.append(-1 if self.stack.pop() != self.stack.pop() else 0)
    
    def _less(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(-1 if a < b else 0)
    
    def _greater(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(-1 if a > b else 0)
    
    def _less_equal(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(-1 if a <= b else 0)
    
    def _greater_equal(self):
        if len(self.stack) >= 2:
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.append(-1 if a >= b else 0)
    
    def _and(self):
        if len(self.stack) >= 2:
            self.stack.append(self.stack.pop() & self.stack.pop())
    
    def _or(self):
        if len(self.stack) >= 2:
            self.stack.append(self.stack.pop() | self.stack.pop())
    
    def _xor(self):
        if len(self.stack) >= 2:
            self.stack.append(self.stack.pop() ^ self.stack.pop())
    
    def _not(self):
        if self.stack:
            self.stack.append(-1 if self.stack.pop() == 0 else 0)
    
    def _invert(self):
        if self.stack:
            self.stack.append(~int(self.stack.pop()))
    
    def _lshift(self):
        if len(self.stack) >= 2:
            n = int(self.stack.pop())
            val = int(self.stack.pop())
            self.stack.append(val << n)
    
    def _rshift(self):
        if len(self.stack) >= 2:
            n = int(self.stack.pop())
            val = int(self.stack.pop())
            self.stack.append(val >> n)
    
    def _abs(self):
        if self.stack:
            self.stack.append(abs(self.stack.pop()))
    
    def _negate(self):
        if self.stack:
            self.stack.append(-self.stack.pop())
    
    def _min(self):
        if len(self.stack) >= 2:
            self.stack.append(min(self.stack.pop(), self.stack.pop()))
    
    def _max(self):
        if len(self.stack) >= 2:
            self.stack.append(max(self.stack.pop(), self.stack.pop()))
    
    def _clean_trig(self, value):
        """Clean up floating point errors for trig functions"""
        if abs(value) < 1e-14:
            return 0.0
        if abs(value - 1.0) < 1e-14:
            return 1.0
        if abs(value + 1.0) < 1e-14:
            return -1.0
        return value
    
    def _sin(self):
        if self.stack:
            self.stack.append(self._clean_trig(math.sin(self.stack.pop())))
    
    def _cos(self):
        if self.stack:
            self.stack.append(self._clean_trig(math.cos(self.stack.pop())))
    
    def _tan(self):
        if self.stack:
            result = math.tan(self.stack.pop())
            if abs(result) < 1e-14:
                self.stack.append(0.0)
            else:
                self.stack.append(result)
    
    def _asin(self):
        if self.stack:
            self.stack.append(math.asin(self.stack.pop()))
    
    def _acos(self):
        if self.stack:
            self.stack.append(math.acos(self.stack.pop()))
    
    def _atan(self):
        if self.stack:
            self.stack.append(math.atan(self.stack.pop()))
    
    def _sqrt(self):
        if self.stack:
            self.stack.append(math.sqrt(self.stack.pop()))
    
    def _log(self):
        if self.stack:
            self.stack.append(math.log10(self.stack.pop()))
    
    def _ln(self):
        if self.stack:
            self.stack.append(math.log(self.stack.pop()))
    
    def _exp(self):
        if self.stack:
            self.stack.append(math.exp(self.stack.pop()))
    
    def _floor(self):
        if self.stack:
            self.stack.append(math.floor(self.stack.pop()))
    
    def _ceil(self):
        if self.stack:
            self.stack.append(math.ceil(self.stack.pop()))
    
    def _round(self):
        if self.stack:
            self.stack.append(round(self.stack.pop()))
    
    def _pi(self):
        self.stack.append(math.pi)
    
    def _e(self):
        self.stack.append(math.e)
