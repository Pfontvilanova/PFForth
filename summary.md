# Overview

This project provides a Python-based Forth interpreter and compiler, offering an interactive development environment with a REPL. It supports core Forth operations, mathematical functions, control structures, user-defined words, variables, constants, and memory management within a 64KB address space. The system is designed to be extensible, supporting concurrent programming via an actor model, network capabilities (WiFi, HTTP, MQTT), and integrated AI functionalities covering data analysis, machine learning, computer vision, natural language processing, and audio analysis. Its purpose is to provide a robust, stack-based Forth environment suitable for various programming tasks, including advanced AI and IoT applications.

# User Preferences

Preferred communication style: Simple, everyday language (Spanish).

# System Architecture

## Core Interpreter Design

The interpreter uses a 5-level Python class hierarchy for modularity, handling stack operations, arithmetic, word definition, variables, constants, values, a 64KB memory space, and an immediate word system. It separates compilation from execution and supports both interactive and compiled execution, including control flow structures (`DO/LOOP`, `IF/THEN/ELSE`, `BEGIN/UNTIL/AGAIN/WHILE/REPEAT`, `CASE/OF/ENDOF/ENDCASE`). Advanced features include `RECURSE`, compile-time execution, meta-programming with `POSTPONE` and `CREATE`/`DOES>`, and local variable support. Memory is managed via a 64KB byte array with a `here` pointer.

## Actor Model

The system includes an actor model for concurrent programming across three phases:

**Fase 1** (`pfforth/actors.py`, `extended-code/forth/actors.fth`): Each actor has its own Forth instance and a thread-safe message queue. Core primitives: actor management (`actor-spawn`, `actor-run`, `actor-kill`), message passing (`actor-send`, `receive`, `receive-timeout`), and introspection (`actor-id`, `actor-alive?`, `actor-list`). Reactive (event-driven) and proactive (periodic tick) modes. Internal protocol: `_ActorMsg(sender_id, value)` envelope; `_KILL_SENTINEL` for reliable kill.

**Fase 2** (`pfforth/actors.py`, `extended-code/forth/actor-log.fth`, `extended-code/forth/actor-watchdog.fth`): `sender-id` / `reply` / `broadcast` for advanced messaging; `actor-wait` to block until an actor terminates; `actor-watchdog` for automatic restart with retry limit; centralised logger actor (`actor-log-start`, `log-info`, `log-warn`, `log-error`).

**Fase 3** (`pfforth/actors.py`, `extended-code/forth/actor-transport.fth`, `extended-code/forth/actor-distributed-demo.fth`): Distributed multi-micro communication with transparent routing. `actor-send` checks a global routing table before delivering: local actors receive messages via their queue; remote actors receive via WiFi (MQTT) or UART.
- **Routing table**: `wifi-ruta-add` / `uart-ruta-add` / `ruta-del` / `rutas`
- **WiFi transport**: `actor-wifi-in` (MQTT listener); outgoing messages published via paho-mqtt. Protocol: JSON envelope `{"proto":"pfforth-actor","v":1,"to":<id>,"from":<id>,"msg":<value>}`.
- **UART transport**: `actor-uart-in` (serial listener via pyserial); binary frame `[0xAC][0xE0][len_hi][len_lo][json…]`.
- **NTP sync**: `actor-ntp` (raw UDP, no extra deps) stores offset; `actor-time` returns Unix-ms adjusted by NTP for cross-node log correlation.
- Message serialisation handles non-JSON-serialisable values by converting to string.
- Demo: `extended-code/forth/actor-distributed-demo.fth` shows REPL (Mac) ↔ sensor (RPi) ↔ display (ESP32) topology and a fully local simulation (`demo-local`).

## Extension System

The system allows defining Forth primitives in Python using `CODE`/`ENDCODE` blocks, with commands for importing, listing, viewing, and removing these definitions.

### Vocabularies

-   **WiFi Vocabulary:** Provides network and connectivity words for TCP/UDP sockets, HTTP requests (`http-get`, `http-post`), MQTT publish/subscribe, and network utilities (`resolve`, `my-ip`, `wifi-connect`).
-   **Graphics Vocabulary:** Renders pixel-based graphics in the terminal using Unicode braille characters, offering drawing primitives (`circle`, `line`, `box`, `plot`) and canvas management.
-   **Charts Vocabulary:** Supports data visualization using Unicode block characters for various chart types (`bar-chart`, `line-chart`, `histogram`) with auto-scaling.
-   **AI Vocabulary:** A modular system for machine learning, data analysis, computer vision, natural language processing, and audio analysis.
    -   **DATA Module:** Handles dataset preparation (`data-load`, `data-info`, `data-split`, `data-norm`).
    -   **PATTERN Module:** Focuses on exploratory analysis (`pat-corr`, `pat-cluster`, `pat-pca`, `pat-anomaly`).
    -   **MODEL Module:** Manages ML model training, evaluation, and persistence (`model-train`, `model-predict`, `model-save`).
    -   **VISION Module:** Analyzes images (load, resize, save, object detection, classification, similarity, embedding).
    -   **EXPLAIN Module:** Provides rule-based natural language explanations for AI operations, interpreting results and suggesting next steps.
    -   **TEXT Module:** Processes and analyzes text (load, clean, tokens, sentiment, summary, embedding, generation).
    -   **AUDIO Module:** Analyzes audio files (load, info, waveform, features, classification, transcription).

## Python Interop

Bidirectional integration with Python is provided through shared variables, direct evaluation of Python expressions and code blocks, and execution of Python files.

## Persistence System

Allows saving and loading user definitions to/from `.fth` files.

## I/O Stream Redirection

Enables redirection of all Forth output words to any Python object with a `write()` interface, and input words to objects with `read()`/`readline()` methods, allowing flexible I/O handling.

## UI/UX Decisions

The REPL features an `OK>` prompt (changing to `CODE>` during definition), automatic line breaks, code inspection (`SEE`), DSL function listing, and documentation (`HELP`). Inline caching is used for performance optimization.

# External Dependencies

## Required Python Libraries

-   **Core:** `math`, `socket`, `os`, `sys`, `select`, `ast`, `re`, `collections.defaultdict`, `importlib.util`, `time`, `code`.
-   **WiFi Vocabulary:** `requests`, `paho-mqtt`.
-   **Actor Model Fase 3 (UART transport):** `pyserial` (optional — only needed for `actor-uart-in` and `uart-ruta-add`).
-   **AI Vocabulary (Base):** `pandas`, `scikit-learn`, `openpyxl`.
-   **AI Vocabulary (VISION Module):** `pillow`, `opencv-python`, `onnxruntime`. Models downloaded automatically to `~/.pfforth/models/`: `yolov5n.onnx` (~4 MB, detección), `mobilenetv2.onnx` (~14 MB, clasificación), `clip_visual_q.onnx` + `clip_text_q.onnx` (~150 MB total, CLIP zero-shot). Works without PyTorch on Mac/iPad/PC/RPi.
-   **AI Vocabulary (TEXT Module):** `textblob` (optional), `langdetect` (optional), `sentence-transformers` (optional), `transformers` (optional).
-   **AI Vocabulary (AUDIO Module):** `librosa`, `soundfile`, `numpy`, `openai-whisper` (optional), `SpeechRecognition` (optional).
-   **Optional (higher accuracy):** `torch`, `clip` (OpenAI), `ultralytics` — las palabras de visión los usan si están disponibles.
