# Overview

This project delivers a Python-based Forth interpreter and compiler, providing an interactive development environment with a Read-Eval-Print Loop (REPL). It supports core Forth operations, mathematics, control structures, user-defined words, variables, constants, and memory management within a 64KB space. The interpreter is case-sensitive, distinguishing between system primitives and user-defined words. The primary goal is to offer a robust, extensible, stack-based Forth environment suitable for diverse programming tasks.

# User Preferences

Preferred communication style: Simple, everyday language (Spanish).

# System Architecture

## Core Interpreter Design

The interpreter uses a 5-level Python class hierarchy for modularity, managing stack operations, arithmetic, word definition, variable/constant/value support, a 64KB memory space, and an immediate word system. It employs a dictionary-based word lookup and separates compilation and execution phases.

## Execution Model

The system supports both interactive and compiled execution. Key control flow structures include `DO/LOOP`, `IF/THEN/ELSE`, `BEGIN/UNTIL/AGAIN/WHILE/REPEAT`, and `CASE/OF/ENDOF/ENDCASE`. Advanced features like `RECURSE` for recursion, bracket mode `[ ]` for compile-time execution, and meta-programming with `POSTPONE` and `CREATE`/`DOES>` are supported. Local variables are implemented using `{ a b c --- comment }` syntax.

## Memory Management

A 64KB byte array manages memory, with a `here` pointer. It provides operations for Python objects (`m@`/`m!`) and integers/bytes (`@`/`!`). The memory layout includes a protected 256-byte PAD area, with user memory starting thereafter.

## Stack Operations

A comprehensive set of stack manipulation words is included, such as `dup`, `drop`, `swap`, `over`, `rot`, `?dup`, `2dup`, `2drop`, `2swap`, `pick`, `roll`, and `depth`, along with return stack operations (`>r`, `r>`, `r@`).

## Extension System (CODE/ENDCODE)

The system allows defining Forth primitives in Python using `CODE`/`ENDCODE` which are persisted for reuse. Commands like `IMPORT`, `LSCODE`, `VLIST`, `RMCODE`, and `SEECODE` manage these extensions.

### WiFi Vocabulary (code/wifi/)

Network and connectivity words for sockets, HTTP, and MQTT:

**Sockets:** `tcp-socket`, `udp-socket`, `connect`, `bind`, `listen`, `sock-accept`, `send`, `recv`, `sock-close`
**HTTP:** `http-get`, `http-post`, `http-status`, `http-body`, `http-json`
**MQTT:** `mqtt-connect`, `mqtt-subscribe`, `mqtt-publish`, `mqtt-callback`, `mqtt-loop`, `mqtt-disconnect`
**Utilities:** `resolve`, `my-ip`, `ping`, `net-info`
**WiFi Management:** `wifi-config`, `wifi-connect`, `wifi-status` (MicroPython/PC compatible)

Socket operations preserve the socket on stack for chaining. MQTT uses loop_start() for async message handling.

### Python Interop (code/python/)

Bidirectional Python-Forth integration:

**Variables compartidas:** `py-var!` (guardar), `py-var@` (leer) - diccionario `f.shared`
**Expresiones:** `py" expr "` - evalúa Python y pone resultado en stack
**Bloques:** `py{ code }py` / `py[ code ]py` - ejecuta código Python (sinónimos, funcionan igual)
**Ficheros:** `py-run` - ejecuta un archivo .py con acceso a stack/shared

**Contexto Python disponible:** `f.stack`, `f.shared`, `f.execute()`, `push()`, `pop()`

El REPL soporta entrada multilínea para `py{` y `py[` con prompts `py{>` y `py[>` respectivamente.

## Persistence System (SAVE/LOAD)

User definitions can be saved to and loaded from `.fth` files, with folder organization. `LSSAVE` lists files, `RMSAVE` deletes them, and `LOAD` executes their content. Path sanitization is in place for security.

## DSL Interface

A Python Domain Specific Language (DSL) provides a fluent, chainable interface for programmatic interaction.

## Number System

Supports integers and floating-point numbers, including mixed-type arithmetic and user-defined number bases (decimal, hexadecimal, binary, octal). Smart printing for floats is also implemented.

## Key Forth Words

A comprehensive set of standard Forth words covers arithmetic, mathematical functions, comparison, logic, I/O, memory operations, defining words (`variable`, `constant`, `value`, `create`, `does>`, `:`, `;`), exception handling (`catch`, `throw`), and file I/O. Introspection words like `words`, `see`, `help`, and `measure` are also available.

## Performance Measurement

The `MEASURE` word profiles the execution time of other words, providing performance statistics in appropriate units.

## UI/UX Decisions

The REPL uses a traditional `OK>` prompt, which changes to `CODE>` during `CODE`/`ENDCODE` definition. Output includes automatic line breaks for readability. `SEE` allows code inspection, `dsl_methods()` lists DSL functions, and `HELP` provides categorized documentation.

## Performance Optimizations

Inline caching is enabled by default, pre-resolving word references during compilation for significant speedup (1.9x-3.3x). Use `cache-on`, `cache-off`, and `cache?` to control it.

# External Dependencies

## Required Python Libraries

Core libraries (standard):
-   `math`, `socket`
-   `os`, `sys`, `select`
-   `ast`, `re`, `collections.defaultdict`, `importlib.util`
-   `time`, `code`

Optional libraries (for wifi vocabulary):
-   `requests` - HTTP client
-   `paho-mqtt` - MQTT client

## Network Capabilities

The wifi vocabulary enables network operations: TCP/UDP sockets, HTTP requests, MQTT pub/sub for IoT applications.