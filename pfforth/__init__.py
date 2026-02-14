"""
PFForth - Python Forth Interpreter/Compiler
Modular package implementation

Usage:
    from pfforth import InteractiveForth
    forth = InteractiveForth()
    forth.execute("1 2 + .")
    
Compatible with Jupyter Notebook and any Python 3.x environment.
"""

from .core import ForthException, ForthBase
from .arithmetic import ForthArithmetic
from .stack_ops import ForthStack
from .memory import ForthMemory
from .control_flow import ForthControlFlow
from .compiler import ForthCompiler
from .io_words import ForthIO
from .persistence import ForthPersistence
from .optimizations import ForthOptimizations
from .repl import ForthREPL, InteractiveForth

__all__ = ['InteractiveForth', 'ForthException']
__version__ = '2.0.0'
