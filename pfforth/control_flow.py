"""
PFForth Control Flow - IF, DO, CASE, BEGIN, locals, etc.
"""


class ForthControlFlow:
    """Mixin providing control flow structures"""
    
    def _register_control_flow_words(self):
        """Register control flow words"""
        self.words['i'] = self._loop_i
        self.words['j'] = self._loop_j
        self.words['k'] = self._loop_k
        self.words['leave'] = self._loop_leave
        self.words['exit'] = self._exit_word
        
        self.immediate_words['recurse'] = self._recurse
        self.immediate_words['do'] = self._do_marker
        self.immediate_words['loop'] = self._loop_marker
        self.immediate_words['+loop'] = self._plusloop_marker
        
        self.immediate_words['if'] = self._if_marker
        self.immediate_words['else'] = self._else_marker
        self.immediate_words['then'] = self._then_marker
        
        self.immediate_words['begin'] = self._begin_marker
        self.immediate_words['until'] = self._until_marker
        self.immediate_words['again'] = self._again_marker
        self.immediate_words['while'] = self._while_marker
        self.immediate_words['repeat'] = self._repeat_marker
        
        self.immediate_words['case'] = self._case_marker
        self.immediate_words['of'] = self._of_marker
        self.immediate_words['endof'] = self._endof_marker
        self.immediate_words['endcase'] = self._endcase_marker
    
    def _loop_i(self):
        if self._loop_stack:
            self.stack.append(self._loop_stack[-1][0])
    
    def _loop_j(self):
        if len(self._loop_stack) >= 2:
            self.stack.append(self._loop_stack[-2][0])
    
    def _loop_k(self):
        if len(self._loop_stack) >= 3:
            self.stack.append(self._loop_stack[-3][0])
    
    def _loop_leave(self):
        self._leave_flag = True
    
    def _exit_word(self):
        self._exit_flag = True
    
    def _recurse(self):
        pass
    
    def _do_marker(self):
        pass
    
    def _loop_marker(self):
        pass
    
    def _plusloop_marker(self):
        pass
    
    def _if_marker(self):
        pass
    
    def _else_marker(self):
        pass
    
    def _then_marker(self):
        pass
    
    def _begin_marker(self):
        pass
    
    def _until_marker(self):
        pass
    
    def _again_marker(self):
        pass
    
    def _while_marker(self):
        pass
    
    def _repeat_marker(self):
        pass
    
    def _case_marker(self):
        pass
    
    def _of_marker(self):
        pass
    
    def _endof_marker(self):
        pass
    
    def _endcase_marker(self):
        pass
    
    def _execute_do_loop(self, loop_tokens, is_plus_loop=False):
        """Execute a DO...LOOP or DO...+LOOP"""
        if len(self.stack) < 2:
            print("Error: DO requiere dos valores (límite e índice)")
            return
        
        start = self.stack.pop()
        limit = self.stack.pop()
        
        self._loop_stack.append([start, limit])
        
        while True:
            if self._leave_flag:
                self._leave_flag = False
                break
            
            current_index = self._loop_stack[-1][0]
            current_limit = self._loop_stack[-1][1]
            
            if is_plus_loop:
                if current_index >= current_limit:
                    break
            else:
                if current_index >= current_limit:
                    break
            
            if hasattr(self, '_recurse_context') and self._recurse_context:
                self._run_compiled(loop_tokens, self._recurse_context[1], is_recurse_root=False)
            else:
                self._execute_tokens(loop_tokens)
            
            if self._exit_flag:
                break
            if self._leave_flag:
                self._leave_flag = False
                break
            
            if is_plus_loop and self.stack:
                increment = self.stack.pop()
            else:
                increment = 1
            
            self._loop_stack[-1][0] += increment
        
        self._loop_stack.pop()
    
    def _execute_if_then_else(self, if_tokens, else_tokens=None):
        """Execute an IF...THEN or IF...ELSE...THEN"""
        if not self.stack:
            print("Error: IF requiere una condición")
            return
        
        condition = self.stack.pop()
        
        if condition != 0:
            if hasattr(self, '_recurse_context') and self._recurse_context:
                self._run_compiled(if_tokens, self._recurse_context[1], is_recurse_root=False)
            else:
                self._execute_tokens(if_tokens)
        elif else_tokens:
            if hasattr(self, '_recurse_context') and self._recurse_context:
                self._run_compiled(else_tokens, self._recurse_context[1], is_recurse_root=False)
            else:
                self._execute_tokens(else_tokens)
    
    def _execute_begin_until(self, loop_tokens):
        """Execute BEGIN...UNTIL"""
        while True:
            if hasattr(self, '_recurse_context') and self._recurse_context:
                self._run_compiled(loop_tokens, self._recurse_context[1], is_recurse_root=False)
            else:
                self._execute_tokens(loop_tokens)
            
            if self._exit_flag:
                break
            
            if not self.stack:
                print("Error: UNTIL requiere una condición")
                break
            
            condition = self.stack.pop()
            if condition != 0:
                break
    
    def _execute_begin_again(self, loop_tokens):
        """Execute BEGIN...AGAIN (infinite loop, needs LEAVE or EXIT)"""
        while True:
            if hasattr(self, '_recurse_context') and self._recurse_context:
                self._run_compiled(loop_tokens, self._recurse_context[1], is_recurse_root=False)
            else:
                self._execute_tokens(loop_tokens)
            
            if self._exit_flag or self._leave_flag:
                self._leave_flag = False
                break
    
    def _execute_begin_while_repeat(self, while_tokens, repeat_tokens):
        """Execute BEGIN...WHILE...REPEAT"""
        while True:
            if hasattr(self, '_recurse_context') and self._recurse_context:
                self._run_compiled(while_tokens, self._recurse_context[1], is_recurse_root=False)
            else:
                self._execute_tokens(while_tokens)
            
            if self._exit_flag:
                break
            
            if not self.stack:
                print("Error: WHILE requiere una condición")
                break
            
            condition = self.stack.pop()
            if condition == 0:
                break
            
            if hasattr(self, '_recurse_context') and self._recurse_context:
                self._run_compiled(repeat_tokens, self._recurse_context[1], is_recurse_root=False)
            else:
                self._execute_tokens(repeat_tokens)
            
            if self._exit_flag:
                break
    
    def _execute_case(self, case_branches, default_tokens=None):
        """Execute CASE...OF...ENDOF...ENDCASE
        
        ANS Forth semantics:
        - The case value is on the stack
        - Each OF branch has test_tokens (executed to get test value) and body_tokens
        - If test value matches case value, execute body and exit CASE
        - If no match, execute default_tokens (if any)
        - ENDCASE drops the case value
        """
        if not self.stack:
            print("Error: CASE requiere un valor")
            return
        
        case_value = self.stack[-1]
        matched = False
        
        for (test_tokens, body_tokens) in case_branches:
            self._execute_tokens(test_tokens)
            
            if not self.stack:
                print("Error: OF requiere un valor de prueba")
                continue
            
            test_value = self.stack.pop()
            
            if case_value == test_value:
                self.stack.pop()
                self._execute_tokens(body_tokens)
                matched = True
                break
        
        if not matched:
            if self.stack:
                self.stack.pop()
            if default_tokens:
                self._execute_tokens(default_tokens)
