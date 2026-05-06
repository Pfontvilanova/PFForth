"""
PFForth Actors — Actor Model concurrency mixin (Fase 1 + 2 + 3)

Each actor = Python daemon thread + own Forth instance + queue.Queue
Thread-local storage tracks which actor is running in each thread.
The REPL is actor-id 0 and never blocks.

Phase 2 adds:
  sender-id / reply     — track and reply to message senders
  broadcast             — send to all alive actors except self
  actor-wait            — block REPL until an actor terminates
  actor-watchdog        — monitor and auto-restart a failed actor
  actor-log-start       — start centralized logger actor

Phase 3 adds:
  wifi-ruta-add         — register a remote WiFi (MQTT) route for an actor-id
  uart-ruta-add         — register a remote UART route for an actor-id
  ruta-del              — remove a route
  rutas                 — print routing table
  actor-wifi-in         — MQTT listener that delivers remote messages locally
  actor-uart-in         — UART listener that delivers remote messages locally
  actor-ntp             — synchronise local clock with NTP
  actor-time            — current time in milliseconds (NTP-adjusted)
  actor-send is extended to auto-route remote messages transparently
"""

import threading
import queue
import time
import sys
import json
import socket
import struct
from datetime import datetime

# Thread-local: each actor thread sets actor_id before running its word
_actor_local = threading.local()

# Sentinel used to signal actor-kill
_KILL_SENTINEL = object()


class _ActorMsg:
    """Internal message envelope that carries sender identity."""
    __slots__ = ('sender_id', 'value')

    def __init__(self, sender_id, value):
        self.sender_id = sender_id
        self.value     = value


class _ActorKilled(Exception):
    """Raised inside an actor thread when actor-kill is received."""


# ── Free functions used by child lambdas ──────────────────────────────────────

def _receive_in(child):
    """Block the actor thread until a message arrives; push value onto child stack.
    Raises _ActorKilled if the kill sentinel is received."""
    msg = child._actor_queue.get(block=True)
    if msg is _KILL_SENTINEL:
        raise _ActorKilled()
    child._last_sender_id = msg.sender_id
    child.stack.append(msg.value)


def _receive_timeout_in(child):
    """( ms -- value found ) Receive with timeout; pushes 0 0 on empty.
    Raises _ActorKilled if the kill sentinel is received."""
    timeout_ms = int(child.stack.pop()) if child.stack else 0
    try:
        msg = child._actor_queue.get(block=True, timeout=timeout_ms / 1000.0)
        if msg is _KILL_SENTINEL:
            raise _ActorKilled()
        child._last_sender_id = msg.sender_id
        child.stack.append(msg.value)
        child.stack.append(-1)   # found = true
    except queue.Empty:
        child.stack += [0, 0]    # value=0, found=false


def _reply_in(child):
    """( value -- ) Send value back to the actor that sent the last message."""
    if not child.stack:
        print("Error: reply requiere un valor en la pila")
        return
    value = child.stack.pop()
    sid   = child._last_sender_id
    from pfforth.actors import ForthActors
    with ForthActors._registry_lock:
        entry = ForthActors._registry.get(sid)
    if entry:
        my_id = child._actor_id_val
        entry['queue'].put(_ActorMsg(my_id, value))
    else:
        print(f"Error: reply: sender {sid} ya no existe")


def _respawn_actor(parent_forth, actor_id):
    """Create a fresh thread for a dead actor, reusing its actor_id and queue.
    Returns True on success, False if actor is not in registry."""
    from pfforth.actors import ForthActors, _actor_local, _ActorKilled

    with ForthActors._registry_lock:
        entry = ForthActors._registry.get(actor_id)
    if not entry:
        return False

    word_name = entry['name']
    child = parent_forth._create_child_forth(actor_id)

    def actor_body():
        _actor_local.actor_id = actor_id
        with ForthActors._registry_lock:
            if actor_id in ForthActors._registry:
                ForthActors._registry[actor_id]['alive'] = True
        try:
            child.execute(word_name)
        except _ActorKilled:
            pass
        except Exception as e:
            print(f"\nActor {actor_id} ({word_name}) error (reinicio): {e}")
        finally:
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = False
                    stop = ForthActors._registry[actor_id].get('_timer_stop')
                    if stop:
                        stop.set()

    new_thread = threading.Thread(
        target=actor_body,
        daemon=True,
        name=f"actor-{actor_id}-{word_name}",
    )

    with ForthActors._registry_lock:
        if actor_id in ForthActors._registry:
            ForthActors._registry[actor_id].update({
                'thread':  new_thread,
                'queue':   child._actor_queue,
                'forth':   child,
                'alive':   False,
                'pending': False,
            })

    new_thread.start()
    return True


# ── Main mixin class ──────────────────────────────────────────────────────────

class ForthActors:
    """Mixin that adds Actor Model words to pfforth (Phase 1 + 2)."""

    def _register_actor_words(self):
        # Class-level (global) registry: shared across ALL interpreter instances
        # in the same Python process.  This means actors created by any Forth
        # instance are visible and addressable from any other.  This is intentional
        # for Phase 1-2 (single-interpreter, single-process use); per-interpreter
        # scoping is deferred to a later phase if multi-instance isolation is needed.
        if not hasattr(ForthActors, '_registry'):
            ForthActors._registry      = {}
            ForthActors._registry_lock = threading.Lock()
            ForthActors._next_id       = 1
            # Actor 0 = REPL / main thread — has its own message queue
            ForthActors._main_queue = queue.Queue()
            ForthActors._registry[0] = {
                'thread': None,
                'queue': ForthActors._main_queue,
                'name': 'repl',
                'forth': None,
                'alive': True,
                'pending': False,
                'type': 'repl',
                '_timer_stop': None,
                '_timer_thread': None,
            }

        # Mark this thread (main/REPL) as actor 0 so sender-id works
        _actor_local.actor_id = 0

        # Phase 3: routing table for distributed actors
        if not hasattr(ForthActors, '_route_table'):
            ForthActors._route_table    = {}   # {actor_id: route_dict}
            ForthActors._route_lock     = threading.Lock()
            ForthActors._ntp_offset     = 0.0  # seconds to add to time.time()

        # Per-instance actor state (None = not an actor / REPL)
        if not hasattr(self, '_actor_queue'):
            self._actor_queue    = None
        if not hasattr(self, '_actor_id_val'):
            self._actor_id_val   = 0
        if not hasattr(self, '_last_sender_id'):
            self._last_sender_id = 0

        # ── Phase 1 words ──────────────────────────────────────────────
        self.words['actor-spawn']     = self._actor_spawn
        self.words['actor-send']      = self._actor_send
        self.words['receive']         = self._receive
        self.words['receive-timeout'] = self._receive_timeout
        self.words['actor-kill']      = self._actor_kill
        self.words['actor-run']       = self._actor_run
        self.words['actor-id']        = self._actor_id
        self.words['actor-alive?']    = self._actor_alive
        self.words['actor-list']      = self._actor_list
        self.words['reactive']        = self._reactive
        self.words['proactive']       = self._proactive
        self.words['ms']              = self._ms
        self.words['s']               = self._s_to_ms
        # ── Phase 2 words ──────────────────────────────────────────────
        self.words['sender-id']       = self._sender_id
        self.words['reply']           = self._reply
        self.words['broadcast']       = self._broadcast
        self.words['actor-wait']      = self._actor_wait
        self.words['actor-watchdog']  = self._actor_watchdog
        self.words['actor-log-start'] = self._actor_log_start
        self.words['log-info']        = self._log_info
        self.words['log-warn']        = self._log_warn
        self.words['log-error']       = self._log_error
        # ── Phase 3 words ──────────────────────────────────────────────
        # Routing table (generic)
        self.words['registrar-ruta']      = self._registrar_ruta
        self.words['ruta-buscar']         = self._ruta_buscar
        self.words['ruta-del']            = self._ruta_del
        self.words['rutas']               = self._rutas
        # Convenience wrappers (auto-start transport actor + register route)
        self.words['wifi-ruta-add']       = self._wifi_ruta_add
        self.words['uart-ruta-add']       = self._uart_ruta_add
        self.words['spi-ruta-add']        = self._spi_ruta_add
        # Outgoing transport actors
        self.words['actor-wifi-out']      = self._actor_wifi_out
        self.words['actor-wifi-tcp-out']  = self._actor_wifi_tcp_out
        self.words['actor-uart-out']      = self._actor_uart_out
        self.words['actor-spi-out']       = self._actor_spi_out
        # Incoming transport actors
        self.words['actor-wifi-in']       = self._actor_wifi_in
        self.words['actor-wifi-tcp-in']   = self._actor_wifi_tcp_in
        self.words['actor-uart-in']       = self._actor_uart_in
        self.words['actor-spi-in']        = self._actor_spi_in
        # NTP / time
        self.words['actor-ntp']           = self._actor_ntp
        self.words['actor-time']          = self._actor_time

    # ── Time helpers ───────────────────────────────────────────────────

    def _ms(self):
        """( n -- n ) n is already milliseconds — readability word."""
        pass

    def _s_to_ms(self):
        """( n -- n*1000 ) Convert seconds to milliseconds."""
        if self.stack:
            self.stack[-1] = int(self.stack[-1]) * 1000

    # ── Creation ───────────────────────────────────────────────────────

    def _actor_spawn(self):
        """( xt|name -- actor-id ) Create a new actor (pending, not started).

        Accepts either:
          - an execution token (xt) obtained via ' word     e.g. ' pong-loop actor-spawn
          - a string word name obtained via s" name"       e.g. s" pong-loop" actor-spawn
        """
        if not self.stack:
            print("Error: actor-spawn requiere xt o nombre en la pila")
            return
        word_or_xt = self.stack.pop()
        if callable(word_or_xt):
            # xt from ' (tick) — reverse-lookup the Forth name
            word_name = next(
                (k for k, v in self.words.items() if v is word_or_xt),
                None
            )
            if word_name is None:
                print("Error: actor-spawn: xt sin nombre conocido "
                      "(usa :noname … ; o s\" nombre\" actor-spawn)")
                return
        else:
            word_name = str(word_or_xt)

        with ForthActors._registry_lock:
            actor_id = ForthActors._next_id
            ForthActors._next_id += 1

        child = self._create_child_forth(actor_id)

        def actor_body():
            _actor_local.actor_id = actor_id
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = True
            try:
                child.execute(word_name)
            except _ActorKilled:
                pass
            except Exception as e:
                print(f"\nActor {actor_id} ({word_name}) error: {e}")
            finally:
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = False
                    entry = ForthActors._registry.get(actor_id, {})
                    stop = entry.get('_timer_stop')
                    if stop:
                        stop.set()

        thread = threading.Thread(
            target=actor_body,
            daemon=True,
            name=f"actor-{actor_id}-{word_name}",
        )

        with ForthActors._registry_lock:
            ForthActors._registry[actor_id] = {
                'thread':        thread,
                'queue':         child._actor_queue,
                'name':          word_name,
                'forth':         child,
                'alive':         False,
                'pending':       True,
                'type':          'reactive',
                '_timer_stop':   None,
                '_timer_thread': None,
            }

        self.stack.append(actor_id)
        print(f"Actor {actor_id} ({word_name}) creado — usa actor-run para iniciarlo")

    def _create_child_forth(self, actor_id):
        """Create a fresh Forth instance with inherited user-defined words.
        The child gets its own queue, identity, and fully child-bound actor words.
        Only receive, receive-timeout, actor-id, sender-id and reply need overriding."""
        from pfforth.repl import InteractiveForth as ForthClass
        child = ForthClass()

        # Give the child its own message queue, identity and sender tracking
        child._actor_queue    = queue.Queue()
        child._actor_id_val   = actor_id
        child._last_sender_id = 0

        # Override only the words that must use child's queue/identity.
        # All other actor words (actor-send, actor-spawn, …) are already correctly
        # bound to child via _register_actor_words() called in __init__.
        child.words['receive']         = lambda: _receive_in(child)
        child.words['receive-timeout'] = lambda: _receive_timeout_in(child)
        child.words['actor-id']        = lambda: child.stack.append(child._actor_id_val)
        child.words['sender-id']       = lambda: child.stack.append(child._last_sender_id)
        child.words['reply']           = lambda: _reply_in(child)

        # Inherit all user definitions in declaration order.
        # Errors are suppressed; set ACTOR_DEBUG=1 to surface them.
        import os as _os
        _debug = _os.environ.get('ACTOR_DEBUG')

        for def_type, name in self._definition_order:
            try:
                if def_type == 'word':
                    # Re-execute the Forth source of the word
                    source = self._definition_source.get(name)
                    if source:
                        child.execute(source)

                elif def_type == 'variable':
                    # Create variable in child and copy the current value
                    child.execute(f'variable {name}')
                    if name in self.variables:
                        val = self.variables[name]
                        if isinstance(val, int):
                            child.execute(f'{val} {name} !')

                elif def_type == 'value':
                    # Values may hold Python objects (e.g. xt from '); set directly
                    if name in self.values:
                        val = self.values[name]
                        child.values[name] = val
                        child.words[name] = (
                            lambda _n=name: child.stack.append(child.values[_n])
                        )

                elif def_type == 'constant':
                    if name in self.constants:
                        val = self.constants[name]
                        child.constants[name] = val
                        child.words[name] = (lambda _v=val: lambda: child.stack.append(_v))(val)

            except Exception as _e:
                if _debug:
                    print(f"[actor-spawn] advertencia al heredar {def_type} '{name}': {_e}")

        return child

    # ── Messaging ─────────────────────────────────────────────────────

    def _receive(self):
        """( -- msg ) Block current actor (or REPL) until a message arrives."""
        q = getattr(self, '_actor_queue', None)
        if q is None:
            # REPL / main thread: use actor-0 queue
            q = ForthActors._main_queue
        msg = q.get(block=True)
        if msg is _KILL_SENTINEL:
            raise _ActorKilled()
        self._last_sender_id = msg.sender_id
        self.stack.append(msg.value)

    def _receive_timeout(self):
        """( ms -- msg found ) Receive with timeout; pushes 0 0 if nothing arrives."""
        if not self.stack:
            self.stack += [0, 0]
            return
        timeout_ms = int(self.stack.pop())
        q = getattr(self, '_actor_queue', None)
        if q is None:
            # REPL / main thread: use actor-0 queue
            q = ForthActors._main_queue
        try:
            msg = q.get(block=True, timeout=timeout_ms / 1000.0)
            if msg is _KILL_SENTINEL:
                raise _ActorKilled()
            self._last_sender_id = msg.sender_id
            self.stack.append(msg.value)
            self.stack.append(-1)   # found = true
        except queue.Empty:
            self.stack += [0, 0]    # value=0, found=false

    def _actor_send(self):
        """( value actor-id -- ) Send a message to a local or remote actor.

        Phase 3: if the actor-id has a route in the routing table,
        the message is serialised and dispatched via the registered
        transport (WiFi/MQTT or UART) instead of a local queue.
        """
        if len(self.stack) < 2:
            print("Error: actor-send requiere ( valor actor-id -- )")
            return
        actor_id  = int(self.stack.pop())
        value     = self.stack.pop()
        sender_id = getattr(_actor_local, 'actor_id', 0)

        # ── Phase 3: check routing table ───────────────────────────────
        with ForthActors._route_lock:
            route = ForthActors._route_table.get(actor_id)

        if route:
            ta_id = route['transport_actor_id']
            with ForthActors._registry_lock:
                ta_entry = ForthActors._registry.get(ta_id)
            if ta_entry and ta_entry.get('alive'):
                # Deliver (to_id, value) to the transport actor's queue
                ta_entry['queue'].put(_ActorMsg(sender_id, (actor_id, value)))
            else:
                print(f"Error: actor-send: transport actor {ta_id} "
                      f"({route.get('transport','?')}) no disponible")
            return

        # ── Local delivery ────────────────────────────────────────────
        with ForthActors._registry_lock:
            entry = ForthActors._registry.get(actor_id)
        if entry:
            entry['queue'].put(_ActorMsg(sender_id, value))
        else:
            print(f"Error: actor {actor_id} no existe (ni local ni remoto)")

    # ── Phase 2: Advanced messaging ────────────────────────────────────

    def _sender_id(self):
        """( -- id ) Return id of actor that sent the last received message."""
        self.stack.append(getattr(self, '_last_sender_id', 0))

    def _reply(self):
        """( value -- ) Send value to the sender of the last received message."""
        if not self.stack:
            print("Error: reply requiere un valor en la pila")
            return
        value = self.stack.pop()
        sid   = getattr(self, '_last_sender_id', 0)
        my_id = getattr(self, '_actor_id_val', 0)
        with ForthActors._registry_lock:
            entry = ForthActors._registry.get(sid)
        if entry:
            entry['queue'].put(_ActorMsg(my_id, value))
        else:
            print(f"Error: reply: sender {sid} ya no existe")

    def _broadcast(self):
        """( value -- ) Send value to all alive actors except self."""
        if not self.stack:
            print("Error: broadcast requiere un valor en la pila")
            return
        value  = self.stack.pop()
        my_id  = getattr(_actor_local, 'actor_id', 0)
        with ForthActors._registry_lock:
            targets = [
                (aid, e) for aid, e in ForthActors._registry.items()
                if aid != my_id and e.get('alive')
            ]
        for aid, e in targets:
            e['queue'].put(_ActorMsg(my_id, value))
        if not targets:
            print("broadcast: ningún actor activo para recibir")

    def _actor_wait(self):
        """( actor-id -- ) Block caller until the actor terminates."""
        if not self.stack:
            print("Error: actor-wait requiere actor-id")
            return
        actor_id = int(self.stack.pop())
        with ForthActors._registry_lock:
            entry = ForthActors._registry.get(actor_id)
        if not entry:
            print(f"Error: actor-wait: actor {actor_id} no existe")
            return
        thread = entry.get('thread')
        if thread:
            thread.join()

    # ── Phase 2: Watchdog ─────────────────────────────────────────────

    def _actor_watchdog(self):
        """( interval-ms max-retries actor-id -- watchdog-id )

        Creates a watchdog that monitors actor-id and restarts it if it dies.
        max-retries = -1 means unlimited restarts.
        watchdog-id can be used with actor-kill to stop monitoring.
        """
        if len(self.stack) < 3:
            print("Error: actor-watchdog requiere ( interval-ms max-retries actor-id -- )")
            return
        actor_id    = int(self.stack.pop())
        max_retries = int(self.stack.pop())
        interval_ms = int(self.stack.pop())

        with ForthActors._registry_lock:
            watched_entry = ForthActors._registry.get(actor_id)
        if not watched_entry:
            print(f"Error: actor-watchdog: actor {actor_id} no existe")
            return

        word_name     = watched_entry['name']
        parent_forth  = self
        stop_evt      = threading.Event()

        with ForthActors._registry_lock:
            wdg_id = ForthActors._next_id
            ForthActors._next_id += 1

        def watchdog_body():
            retries = 0
            try:
                while not stop_evt.wait(timeout=interval_ms / 1000.0):
                    with ForthActors._registry_lock:
                        e = ForthActors._registry.get(actor_id)
                        if not e:
                            break
                        alive   = e.get('alive', False)
                        pending = e.get('pending', False)

                    if not alive and not pending:
                        if max_retries != -1 and retries >= max_retries:
                            ts = datetime.now().strftime('%H:%M:%S')
                            print(f"[{ts}] watchdog: actor {actor_id} ({word_name}) "
                                  f"agotó reintentos ({max_retries}), deteniendo watchdog")
                            break

                        retries += 1
                        ts = datetime.now().strftime('%H:%M:%S')
                        print(f"[{ts}] watchdog: reiniciando actor {actor_id} "
                              f"({word_name}) — intento {retries}")

                        # Send log if logger is running
                        _send_to_log(wdg_id,
                                     f"watchdog: reinicio #{retries} del actor {actor_id} ({word_name})",
                                     level='warn')

                        ok = _respawn_actor(parent_forth, actor_id)
                        if not ok:
                            break

                        time.sleep(0.05)  # give the new thread a moment to start
            finally:
                # Mark watchdog as dead in registry so actor-list reflects correct state
                with ForthActors._registry_lock:
                    if wdg_id in ForthActors._registry:
                        ForthActors._registry[wdg_id]['alive'] = False

        wdg_thread = threading.Thread(
            target=watchdog_body,
            daemon=True,
            name=f"watchdog-{actor_id}",
        )

        with ForthActors._registry_lock:
            ForthActors._registry[wdg_id] = {
                'thread':        wdg_thread,
                'queue':         queue.Queue(),
                'name':          f'watchdog({word_name})',
                'forth':         None,
                'alive':         True,
                'pending':       False,
                'type':          'watchdog',
                '_timer_stop':   stop_evt,
                '_timer_thread': None,
            }

        wdg_thread.start()
        self.stack.append(wdg_id)
        print(f"Watchdog {wdg_id} monitorizando actor {actor_id} ({word_name}), "
              f"intervalo={interval_ms}ms, max_reintentos={max_retries}")

    # ── Phase 2: Centralized logger ────────────────────────────────────

    def _actor_log_start(self):
        """( -- log-id ) Start the centralized logger actor (idempotent).

        If a logger is already alive, pushes its id and returns immediately.
        The logger receives dicts {'level': ..., 'msg': ..., 'from': ...}
        or plain strings/values and prints them formatted with timestamp.
        Use the log() helper word to send messages easily.
        """
        # Idempotent: return existing logger if still alive
        with ForthActors._registry_lock:
            existing = getattr(ForthActors, '_log_actor_id', None)
            if existing is not None:
                entry = ForthActors._registry.get(existing)
                if entry and entry.get('alive'):
                    print(f"Logger ya activo (id={existing})")
                    self.stack.append(existing)
                    return

        stop_evt = threading.Event()

        with ForthActors._registry_lock:
            log_id = ForthActors._next_id
            ForthActors._next_id += 1

        log_queue = queue.Queue()

        LEVEL_PREFIX = {
            'info':  '[INFO ]',
            'warn':  '[WARN ]',
            'error': '[ERROR]',
        }

        def log_body():
            while True:
                msg = log_queue.get(block=True)
                if msg is _KILL_SENTINEL:
                    break
                ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                if isinstance(msg, _ActorMsg):
                    inner = msg.value
                    from_id = msg.sender_id
                else:
                    inner = msg
                    from_id = 0

                if isinstance(inner, dict):
                    level = inner.get('level', 'info')
                    text  = inner.get('msg', '')
                    fid   = inner.get('from', from_id)
                else:
                    level = 'info'
                    text  = str(inner)
                    fid   = from_id

                prefix = LEVEL_PREFIX.get(level, '[INFO ]')
                actor_tag = f"actor-{fid}" if fid else "REPL"
                print(f"{ts} {prefix} [{actor_tag}] {text}")

        log_thread = threading.Thread(
            target=log_body,
            daemon=True,
            name=f"actor-log-{log_id}",
        )

        with ForthActors._registry_lock:
            ForthActors._registry[log_id] = {
                'thread':        log_thread,
                'queue':         log_queue,
                'name':          'actor-log',
                'forth':         None,
                'alive':         True,
                'pending':       False,
                'type':          'logger',
                '_timer_stop':   stop_evt,
                '_timer_thread': None,
            }
            ForthActors._log_actor_id = log_id

        log_thread.start()
        self.stack.append(log_id)
        print(f"Logger centralizado iniciado (id={log_id})")

    # ── Phase 2: Log helper primitives ───────────────────────────────

    def _log_at_level(self, level):
        """Internal: pop a string and send it to the log actor at given level."""
        if not self.stack:
            return
        text = str(self.stack.pop())
        log_id = getattr(ForthActors, '_log_actor_id', None)
        if log_id is None:
            print(f"[{level.upper():5}] {text}")
            return
        with ForthActors._registry_lock:
            entry = ForthActors._registry.get(log_id)
        if entry and entry.get('alive'):
            my_id = getattr(self, '_actor_id_val',
                            getattr(_actor_local, 'actor_id', 0))
            payload = {'level': level, 'msg': text, 'from': my_id}
            entry['queue'].put(_ActorMsg(my_id, payload))
        else:
            print(f"[{level.upper():5}] {text}")

    def _log_info(self):
        """( str -- ) Send INFO log message to the centralized logger."""
        self._log_at_level('info')

    def _log_warn(self):
        """( str -- ) Send WARN log message to the centralized logger."""
        self._log_at_level('warn')

    def _log_error(self):
        """( str -- ) Send ERROR log message to the centralized logger."""
        self._log_at_level('error')

    # ── Lifecycle ─────────────────────────────────────────────────────

    def _actor_kill(self):
        """( actor-id -- ) Stop and remove an actor reliably.

        Sends _KILL_SENTINEL so receive/receive-timeout raise _ActorKilled
        inside the actor thread, unblocking it and allowing clean exit.
        Then waits up to 1 s for the thread to terminate.
        """
        if not self.stack:
            print("Error: actor-kill requiere actor-id")
            return
        actor_id = int(self.stack.pop())

        with ForthActors._registry_lock:
            entry = ForthActors._registry.pop(actor_id, None)
            if actor_id == getattr(ForthActors, '_log_actor_id', None):
                ForthActors._log_actor_id = None

        if not entry:
            print(f"Error: actor {actor_id} no existe")
            return

        # Stop proactive timer / watchdog stop event
        stop = entry.get('_timer_stop')
        if stop:
            stop.set()
        timer_t = entry.get('_timer_thread')
        if timer_t and timer_t.is_alive():
            timer_t.join(timeout=0.5)

        # Unblock actor thread via kill sentinel
        entry['queue'].put(_KILL_SENTINEL)

        # Wait briefly for the thread to terminate
        thread = entry.get('thread')
        if thread and thread.is_alive():
            thread.join(timeout=1.0)

        print(f"Actor {actor_id} ({entry['name']}) eliminado")

    def _actor_run(self):
        """( actor-id | -- ) Start a specific actor or all pending actors.

        Two modes:
          actor-id actor-run  — start just the actor with that id
          actor-run           — start ALL pending actors at once
        """
        # Check if top-of-stack is a pending actor-id
        specific_id = None
        if self.stack:
            candidate = self.stack[-1]
            if isinstance(candidate, (int, float)):
                cid = int(candidate)
                with ForthActors._registry_lock:
                    entry = ForthActors._registry.get(cid)
                if entry and entry.get('pending'):
                    self.stack.pop()
                    specific_id = cid

        if specific_id is not None:
            pending = [(specific_id, ForthActors._registry[specific_id])]
        else:
            with ForthActors._registry_lock:
                pending = [
                    (aid, e) for aid, e in ForthActors._registry.items()
                    if e.get('pending')
                ]

        for actor_id, entry in pending:
            entry['thread'].start()
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['pending'] = False
            # Start timer thread if proactive
            with ForthActors._registry_lock:
                current = ForthActors._registry.get(actor_id, {})
                timer_t = current.get('_timer_thread')
            if timer_t and not timer_t.is_alive():
                timer_t.start()

        if pending:
            print(f"{len(pending)} actor(s) iniciado(s)")
        else:
            print("No hay actores pendientes")

    # ── Introspection ──────────────────────────────────────────────────

    def _actor_id(self):
        """( -- id ) Return current actor id; 0 if called from REPL."""
        self.stack.append(getattr(_actor_local, 'actor_id', 0))

    def _actor_alive(self):
        """( actor-id -- flag ) Push -1 if alive, 0 if not."""
        if not self.stack:
            self.stack.append(0)
            return
        actor_id = int(self.stack.pop())
        with ForthActors._registry_lock:
            entry = ForthActors._registry.get(actor_id)
        self.stack.append(-1 if entry and entry.get('alive') else 0)

    def _actor_list(self):
        """( -- ) Print a table of all registered actors."""
        with ForthActors._registry_lock:
            actors = list(ForthActors._registry.items())

        out = getattr(self, '_forth_output', sys.stdout)
        if not actors:
            out.write("No hay actores registrados\n")
            out.flush()
            return

        out.write(f"{'ID':>4}  {'Nombre':<22}  {'Tipo':<10}  {'Estado':<10}  {'Cola':>5}\n")
        out.write("-" * 58 + "\n")
        for actor_id, entry in sorted(actors):
            name  = entry['name'][:22]
            tipo  = entry.get('type', 'reactive')[:10]
            if entry.get('pending'):
                estado = 'pendiente'
            elif entry.get('alive'):
                estado = 'activo'
            else:
                estado = 'muerto'
            cola = entry['queue'].qsize()
            out.write(f"{actor_id:>4}  {name:<22}  {tipo:<10}  {estado:<10}  {cola:>5}\n")
        out.flush()

    # ── Behaviour ─────────────────────────────────────────────────────

    def _reactive(self):
        """( actor-id -- ) Mark actor as reactive (message-driven, default)."""
        if not self.stack:
            print("Error: reactive requiere actor-id")
            return
        actor_id = int(self.stack.pop())
        with ForthActors._registry_lock:
            if actor_id in ForthActors._registry:
                ForthActors._registry[actor_id]['type'] = 'reactive'

    def _proactive(self):
        """( interval-ms actor-id -- ) Mark actor as proactive;
        timer sends 'tick every N ms."""
        if len(self.stack) < 2:
            print("Error: proactive requiere ( interval-ms actor-id -- )")
            return
        actor_id    = int(self.stack.pop())
        interval_ms = int(self.stack.pop())

        with ForthActors._registry_lock:
            entry = ForthActors._registry.get(actor_id)
            if not entry:
                print(f"Error: actor {actor_id} no existe")
                return

            # Guard: don't spawn a second timer if one is already set
            if entry.get('_timer_thread') and entry['_timer_thread'].is_alive():
                print(f"Actor {actor_id} ya tiene un timer activo")
                return

            stop_evt  = threading.Event()
            msg_queue = entry['queue']

            def tick_loop(stop=stop_evt, aid=actor_id, q=msg_queue,
                          iv=interval_ms):
                while not stop.wait(timeout=iv / 1000.0):
                    with ForthActors._registry_lock:
                        if aid not in ForthActors._registry:
                            break
                    q.put(_ActorMsg(0, "'tick"))

            timer_thread = threading.Thread(
                target=tick_loop,
                daemon=True,
                name=f"timer-{actor_id}",
            )

            entry['type']           = 'proactive'
            entry['_timer_stop']    = stop_evt
            entry['_timer_thread']  = timer_thread

        # Start immediately only if actor is already running
        if entry.get('alive'):
            timer_thread.start()

    # ══ Phase 3: Distributed routing ══════════════════════════════════════

    # ── Routing table (generic) ────────────────────────────────────────

    def _registrar_ruta(self):
        """( actor-id transport-str transport-actor-id -- )

        Low-level routing primitive.  Associate *actor-id* with a remote actor
        reachable through the local transport actor *transport-actor-id*.

        transport-str — human label ('mqtt', 'tcp', 'uart', 'spi', ...)
        transport-actor-id — id of an already-running OUT transport actor

        After this call, actor-send will deliver messages for *actor-id* to
        the transport actor's queue as a (actor-id, value) tuple.
        """
        if len(self.stack) < 3:
            print("Error: registrar-ruta requiere ( actor-id transport-str transport-actor-id -- )")
            return
        transport_actor_id = int(self.stack.pop())
        transport          = str(self.stack.pop())
        actor_id           = int(self.stack.pop())

        with ForthActors._registry_lock:
            ta_entry = ForthActors._registry.get(transport_actor_id)
        if not ta_entry:
            print(f"Error: registrar-ruta: transport actor {transport_actor_id} no existe")
            return

        desc = ta_entry.get('name', str(transport_actor_id))
        route = {
            'transport':          transport,
            'transport_actor_id': transport_actor_id,
            'desc':               desc,
        }
        with ForthActors._route_lock:
            ForthActors._route_table[actor_id] = route

        print(f"Ruta registrada: actor-{actor_id} → [{transport}] actor-{transport_actor_id} ({desc})")

    def _ruta_buscar(self):
        """( actor-id -- endpoint-str | 0 )

        Return a string describing the remote endpoint associated with *actor-id*
        (e.g. "mqtt:192.168.1.10:1883/pfforth/rpi/in"), or 0 (integer) if the
        actor has no route and is local.

        The returned string can be inspected with . or stored in a VALUE.
        To get the transport actor-id use: ruta-buscar dup 0 <> if ... then
        (ruta-buscar always returns a string for remote actors, 0 for local).

        For low-level transport actor lookup, inspect the routes table printed
        by 'rutas' or use ruta-buscar with 0<> test.
        """
        if not self.stack:
            print("Error: ruta-buscar requiere actor-id")
            return
        actor_id = int(self.stack.pop())
        with ForthActors._route_lock:
            route = ForthActors._route_table.get(actor_id)
        if route:
            transport = route.get('transport', '?')
            desc      = route.get('desc', '?')
            ta_id     = route.get('transport_actor_id', 0)
            endpoint  = f"{transport}:{desc}  (via actor-{ta_id})"
            self.stack.append(endpoint)
        else:
            self.stack.append(0)

    # ── Convenience wrappers (auto-start transport + register) ─────────

    def _wifi_ruta_add(self):
        """( actor-id host port topic -- ) Start an MQTT OUT actor (if needed)
        and register the route for *actor-id*.  Reuses an existing MQTT OUT
        actor if one for the same (host, port, topic) is already alive.
        Does NOT register the route if the transport actor fails to start.
        """
        if len(self.stack) < 4:
            print("Error: wifi-ruta-add requiere ( actor-id host port topic -- )")
            return
        topic    = str(self.stack.pop())
        port     = int(self.stack.pop())
        host     = str(self.stack.pop())
        actor_id = int(self.stack.pop())

        key = ('mqtt', host, port, topic)
        ta_id = _get_or_start_transport_out(self, key,
                    lambda: _start_mqtt_out_actor(self, host, port, topic))
        if not ta_id:
            print(f"Error: wifi-ruta-add: transporte MQTT no disponible — "
                  f"actor-{actor_id} sin ruta (mensajes irán a actor local si existe)")
            return
        route = {'transport': 'mqtt', 'transport_actor_id': ta_id,
                 'desc': f"{host}:{port}/{topic}"}
        with ForthActors._route_lock:
            ForthActors._route_table[actor_id] = route
        print(f"Ruta WiFi MQTT: actor-{actor_id} → actor-{ta_id} ({host}:{port}/{topic})")

    def _uart_ruta_add(self):
        """( actor-id device baud -- ) Start a UART OUT actor (if needed)
        and register the route for *actor-id*.
        Does NOT register the route if the transport actor fails to start.
        """
        if len(self.stack) < 3:
            print("Error: uart-ruta-add requiere ( actor-id device baud -- )")
            return
        baud     = int(self.stack.pop())
        device   = str(self.stack.pop())
        actor_id = int(self.stack.pop())

        key = ('uart', device, baud)
        ta_id = _get_or_start_transport_out(self, key,
                    lambda: _start_uart_out_actor(self, device, baud))
        if not ta_id:
            print(f"Error: uart-ruta-add: transporte UART no disponible — "
                  f"actor-{actor_id} sin ruta")
            return
        route = {'transport': 'uart', 'transport_actor_id': ta_id,
                 'desc': f"{device}@{baud}"}
        with ForthActors._route_lock:
            ForthActors._route_table[actor_id] = route
        print(f"Ruta UART: actor-{actor_id} → actor-{ta_id} ({device}@{baud})")

    def _spi_ruta_add(self):
        """( actor-id device speed -- ) Start an SPI OUT actor (if needed)
        and register the route for *actor-id*.

        device — spidev bus.device string, e.g. '0.0' for /dev/spidev0.0
        speed  — bus speed in Hz, e.g. 500000
        Does NOT register the route if the transport actor fails to start.
        """
        if len(self.stack) < 3:
            print("Error: spi-ruta-add requiere ( actor-id device speed -- )")
            return
        speed    = int(self.stack.pop())
        device   = str(self.stack.pop())
        actor_id = int(self.stack.pop())

        key = ('spi', device, speed)
        ta_id = _get_or_start_transport_out(self, key,
                    lambda: _start_spi_out_actor(self, device, speed))
        if not ta_id:
            print(f"Error: spi-ruta-add: transporte SPI no disponible — "
                  f"actor-{actor_id} sin ruta")
            return
        route = {'transport': 'spi', 'transport_actor_id': ta_id,
                 'desc': f"{device}@{speed}Hz"}
        with ForthActors._route_lock:
            ForthActors._route_table[actor_id] = route
        print(f"Ruta SPI: actor-{actor_id} → actor-{ta_id} ({device}@{speed}Hz)")

    def _ruta_del(self):
        """( actor-id -- ) Remove routing entry for actor-id."""
        if not self.stack:
            print("Error: ruta-del requiere actor-id")
            return
        actor_id = int(self.stack.pop())
        with ForthActors._route_lock:
            removed = ForthActors._route_table.pop(actor_id, None)
        if removed:
            print(f"Ruta de actor-{actor_id} eliminada")
        else:
            print(f"actor-{actor_id} no tenía ruta registrada")

    def _rutas(self):
        """( -- ) Print the current routing table."""
        out = getattr(self, '_forth_output', sys.stdout)
        with ForthActors._route_lock:
            routes = list(ForthActors._route_table.items())
        if not routes:
            out.write("Tabla de rutas vacía (todos los actores son locales)\n")
            out.flush()
            return
        out.write(f"{'Actor-ID':>9}  {'Transport':>5}  {'TA-ID':>6}  Endpoint\n")
        out.write("-" * 64 + "\n")
        for actor_id, r in sorted(routes):
            t    = r.get('transport', '?')
            taid = r.get('transport_actor_id', '?')
            desc = r.get('desc', '')
            out.write(f"{actor_id:>9}  {t:>5}  {str(taid):>6}  {desc}\n")
        out.flush()

    # ── Outgoing transport actors ──────────────────────────────────────

    def _actor_wifi_out(self):
        """( host port topic -- actor-id ) Start an MQTT OUT transport actor.

        The actor sits in a receive loop.  Each received message must be a
        tuple (to_id, value) produced by actor-send when routing remotely.
        It serialises the message to a JSON pfforth-actor envelope and
        publishes it to *topic* on the MQTT broker at host:port.
        Requires: paho-mqtt
        """
        if len(self.stack) < 3:
            print("Error: actor-wifi-out requiere ( host port topic -- )")
            return
        topic = str(self.stack.pop())
        port  = int(self.stack.pop())
        host  = str(self.stack.pop())

        actor_id = _start_mqtt_out_actor(self, host, port, topic)
        self.stack.append(actor_id)

    def _actor_wifi_tcp_out(self):
        """( host port -- actor-id ) Start a TCP OUT transport actor.

        Connects to host:port for each outgoing message (stateless; sufficient
        for low-frequency IoT use).  Sends a JSON pfforth-actor envelope
        followed by a newline so the remote side can frame it easily.
        Each received queue message must be (to_id, value) from actor-send.
        """
        if len(self.stack) < 2:
            print("Error: actor-wifi-tcp-out requiere ( host port -- )")
            return
        port = int(self.stack.pop())
        host = str(self.stack.pop())

        actor_id = _start_tcp_out_actor(self, host, port)
        self.stack.append(actor_id)

    def _actor_uart_out(self):
        """( device baud -- actor-id ) Start a UART OUT transport actor.

        Writes binary-framed JSON envelopes to the serial port for each
        message.  Frame: [0xAC][0xE0][len_hi][len_lo][json_bytes…]
        Requires: pyserial
        """
        if len(self.stack) < 2:
            print("Error: actor-uart-out requiere ( device baud -- )")
            return
        baud   = int(self.stack.pop())
        device = str(self.stack.pop())

        actor_id = _start_uart_out_actor(self, device, baud)
        self.stack.append(actor_id)

    def _actor_spi_out(self):
        """( device speed -- actor-id ) Start an SPI OUT transport actor.

        Uses spidev (Linux) to write binary-framed JSON envelopes.
        Frame format identical to UART: [0xAC][0xE0][len_hi][len_lo][json…]
        device — spidev bus.device string, e.g. '0.0' for /dev/spidev0.0
        speed  — SPI bus speed in Hz, e.g. 500000
        Requires: spidev (Linux only)
        """
        if len(self.stack) < 2:
            print("Error: actor-spi-out requiere ( device speed -- )")
            return
        speed  = int(self.stack.pop())
        device = str(self.stack.pop())

        actor_id = _start_spi_out_actor(self, device, speed)
        self.stack.append(actor_id)

    # ── Incoming transport actors ──────────────────────────────────────

    def _actor_wifi_in(self):
        """( host port topic -- actor-id ) Start MQTT listener that delivers
        incoming remote messages to their local actor targets.

        Subscribes to *topic* on the MQTT broker at host:port.
        Each received MQTT message must be a pfforth-actor JSON envelope:
          {"proto":"pfforth-actor","v":1,"to":<int>,"from":<int>,"msg":<value>}
        The message is delivered to the local actor whose id matches "to".
        """
        if len(self.stack) < 3:
            print("Error: actor-wifi-in requiere ( host port topic -- )")
            return
        topic = str(self.stack.pop())
        port  = int(self.stack.pop())
        host  = str(self.stack.pop())

        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            print("Error: actor-wifi-in requiere paho-mqtt (pip install paho-mqtt)")
            self.stack.append(0)
            return

        with ForthActors._registry_lock:
            actor_id = ForthActors._next_id
            ForthActors._next_id += 1

        stop_evt  = threading.Event()
        in_queue  = queue.Queue()   # internal queue (not used for messaging)

        def on_message(client, userdata, message):
            try:
                payload = json.loads(message.payload.decode('utf-8'))
            except Exception:
                return
            if payload.get('proto') != 'pfforth-actor':
                return
            to_id   = payload.get('to', 0)
            from_id = payload.get('from', 0)
            value   = payload.get('msg')
            with ForthActors._registry_lock:
                entry = ForthActors._registry.get(to_id)
            if entry:
                entry['queue'].put(_ActorMsg(from_id, value))
            else:
                ts = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts}] actor-wifi-in: actor local {to_id} no encontrado")

        def wifi_in_body():
            client = mqtt.Client()
            client.on_message = on_message
            try:
                client.connect(host, port, keepalive=60)
                client.subscribe(topic)
                ts = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts}] actor-wifi-in ({actor_id}): escuchando {host}:{port}/{topic}")
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = True
                while not stop_evt.is_set():
                    client.loop(timeout=0.5)
            except Exception as e:
                print(f"actor-wifi-in error: {e}")
            finally:
                try:
                    client.disconnect()
                except Exception:
                    pass
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = False

        thread = threading.Thread(
            target=wifi_in_body,
            daemon=True,
            name=f"actor-wifi-in-{actor_id}",
        )
        with ForthActors._registry_lock:
            ForthActors._registry[actor_id] = {
                'thread':        thread,
                'queue':         in_queue,
                'name':          f'wifi-in({topic})',
                'forth':         None,
                'alive':         False,
                'pending':       False,
                'type':          'wifi-in',
                '_timer_stop':   stop_evt,
                '_timer_thread': None,
            }

        thread.start()
        self.stack.append(actor_id)
        print(f"actor-wifi-in {actor_id} iniciado → {host}:{port}/{topic}")

    # ── UART IN transport ──────────────────────────────────────────────

    def _actor_uart_in(self):
        """( device baud -- actor-id ) Start UART listener.

        Reads framed messages from the serial port and delivers them to
        the appropriate local actor.  Frame format:
          [0xAC] [0xE0] [len_hi] [len_lo] [json_bytes…]
        JSON must be a pfforth-actor envelope (same as WiFi).
        """
        if len(self.stack) < 2:
            print("Error: actor-uart-in requiere ( device baud -- )")
            return
        baud   = int(self.stack.pop())
        device = str(self.stack.pop())

        try:
            import serial
        except ImportError:
            print("Error: actor-uart-in requiere pyserial (pip install pyserial)")
            self.stack.append(0)
            return

        with ForthActors._registry_lock:
            actor_id = ForthActors._next_id
            ForthActors._next_id += 1

        stop_evt  = threading.Event()
        in_queue  = queue.Queue()

        def uart_in_body():
            import serial
            try:
                ser = serial.Serial(device, baud, timeout=0.5)
            except Exception as e:
                print(f"actor-uart-in: no se puede abrir {device}: {e}")
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = False
                return

            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = True
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] actor-uart-in ({actor_id}): escuchando {device} @{baud}")

            buf = bytearray()
            try:
                while not stop_evt.is_set():
                    chunk = ser.read(64)
                    if not chunk:
                        continue
                    buf.extend(chunk)
                    while True:
                        # Find frame header 0xAC 0xE0
                        idx = _find_uart_frame_start(buf)
                        if idx < 0:
                            buf = buf[-1:] if len(buf) > 1 else bytearray()
                            break
                        if idx > 0:
                            del buf[:idx]
                        if len(buf) < 4:
                            break
                        length = (buf[2] << 8) | buf[3]
                        if len(buf) < 4 + length:
                            break
                        frame = bytes(buf[4: 4 + length])
                        del buf[:4 + length]
                        try:
                            payload = json.loads(frame.decode('utf-8'))
                        except Exception:
                            continue
                        if payload.get('proto') != 'pfforth-actor':
                            continue
                        to_id   = payload.get('to', 0)
                        from_id = payload.get('from', 0)
                        value   = payload.get('msg')
                        with ForthActors._registry_lock:
                            entry = ForthActors._registry.get(to_id)
                        if entry:
                            entry['queue'].put(_ActorMsg(from_id, value))
            except Exception as e:
                print(f"actor-uart-in error: {e}")
            finally:
                try:
                    ser.close()
                except Exception:
                    pass
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = False

        thread = threading.Thread(
            target=uart_in_body,
            daemon=True,
            name=f"actor-uart-in-{actor_id}",
        )
        with ForthActors._registry_lock:
            ForthActors._registry[actor_id] = {
                'thread':        thread,
                'queue':         in_queue,
                'name':          f'uart-in({device})',
                'forth':         None,
                'alive':         False,
                'pending':       False,
                'type':          'uart-in',
                '_timer_stop':   stop_evt,
                '_timer_thread': None,
            }

        thread.start()
        self.stack.append(actor_id)
        print(f"actor-uart-in {actor_id} iniciado → {device} @{baud}")

    def _actor_wifi_tcp_in(self):
        """( port -- actor-id ) Start a TCP server that listens for incoming
        pfforth-actor JSON messages (newline-terminated) and delivers them
        to the appropriate local actor.

        Each line received must be a valid pfforth-actor JSON envelope.
        """
        if not self.stack:
            print("Error: actor-wifi-tcp-in requiere ( port -- )")
            return
        port = int(self.stack.pop())

        with ForthActors._registry_lock:
            actor_id = ForthActors._next_id
            ForthActors._next_id += 1

        stop_evt = threading.Event()
        in_queue = queue.Queue()

        def tcp_in_body():
            try:
                srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                srv.bind(('', port))
                srv.listen(5)
                srv.settimeout(0.5)
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = True
                ts = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts}] actor-wifi-tcp-in ({actor_id}): escuchando TCP :{port}")
                while not stop_evt.is_set():
                    try:
                        conn, addr = srv.accept()
                    except socket.timeout:
                        continue
                    threading.Thread(
                        target=_handle_tcp_in_conn,
                        args=(conn,),
                        daemon=True,
                    ).start()
            except Exception as e:
                print(f"actor-wifi-tcp-in error: {e}")
            finally:
                try:
                    srv.close()
                except Exception:
                    pass
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = False

        thread = threading.Thread(
            target=tcp_in_body,
            daemon=True,
            name=f"actor-wifi-tcp-in-{actor_id}",
        )
        with ForthActors._registry_lock:
            ForthActors._registry[actor_id] = {
                'thread':        thread,
                'queue':         in_queue,
                'name':          f'tcp-in(:{port})',
                'forth':         None,
                'alive':         False,
                'pending':       False,
                'type':          'tcp-in',
                '_timer_stop':   stop_evt,
                '_timer_thread': None,
            }
        thread.start()
        self.stack.append(actor_id)
        print(f"actor-wifi-tcp-in {actor_id} iniciado → TCP :{port}")

    def _actor_spi_in(self):
        """( device speed -- actor-id ) Start an SPI IN transport actor.

        Reads binary-framed JSON messages from an spidev device and delivers
        them to the appropriate local actor.
        Frame: [0xAC][0xE0][len_hi][len_lo][json_bytes…]
        device — spidev bus.device string, e.g. '0.0'
        speed  — bus speed in Hz
        Requires: spidev (Linux only)
        """
        if len(self.stack) < 2:
            print("Error: actor-spi-in requiere ( device speed -- )")
            return
        speed  = int(self.stack.pop())
        device = str(self.stack.pop())

        try:
            import spidev as _spidev  # noqa: F401
        except ImportError:
            print("Error: actor-spi-in requiere spidev (pip install spidev, Linux)")
            self.stack.append(0)
            return

        with ForthActors._registry_lock:
            actor_id = ForthActors._next_id
            ForthActors._next_id += 1

        stop_evt = threading.Event()
        in_queue = queue.Queue()

        def spi_in_body():
            import spidev
            parts = str(device).split('.')
            bus, dev_num = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            spi = spidev.SpiDev()
            try:
                spi.open(bus, dev_num)
                spi.max_speed_hz = speed
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = True
                ts = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts}] actor-spi-in ({actor_id}): "
                      f"escuchando SPI /dev/spidev{device} @{speed}Hz")
                buf = bytearray()
                while not stop_evt.is_set():
                    chunk = spi.readbytes(64)
                    if not any(chunk):
                        time.sleep(0.01)
                        continue
                    buf.extend(chunk)
                    while True:
                        idx = _find_uart_frame_start(buf)
                        if idx < 0:
                            buf = buf[-1:] if len(buf) > 1 else bytearray()
                            break
                        if idx > 0:
                            del buf[:idx]
                        if len(buf) < 4:
                            break
                        length = (buf[2] << 8) | buf[3]
                        if len(buf) < 4 + length:
                            break
                        frame = bytes(buf[4: 4 + length])
                        del buf[:4 + length]
                        try:
                            payload = json.loads(frame.decode('utf-8'))
                        except Exception:
                            continue
                        if payload.get('proto') != 'pfforth-actor':
                            continue
                        to_id   = payload.get('to', 0)
                        from_id = payload.get('from', 0)
                        value   = payload.get('msg')
                        with ForthActors._registry_lock:
                            entry = ForthActors._registry.get(to_id)
                        if entry:
                            entry['queue'].put(_ActorMsg(from_id, value))
            except Exception as e:
                print(f"actor-spi-in error: {e}")
            finally:
                try:
                    spi.close()
                except Exception:
                    pass
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = False

        thread = threading.Thread(
            target=spi_in_body,
            daemon=True,
            name=f"actor-spi-in-{actor_id}",
        )
        with ForthActors._registry_lock:
            ForthActors._registry[actor_id] = {
                'thread':        thread,
                'queue':         in_queue,
                'name':          f'spi-in({device})',
                'forth':         None,
                'alive':         False,
                'pending':       False,
                'type':          'spi-in',
                '_timer_stop':   stop_evt,
                '_timer_thread': None,
            }
        thread.start()
        self.stack.append(actor_id)
        print(f"actor-spi-in {actor_id} iniciado → SPI /dev/spidev{device}")

    # ── NTP sync ───────────────────────────────────────────────────────

    def _actor_ntp(self):
        """( interval-ms -- actor-id ) Start a proactive NTP sync actor.

        Performs an initial sync immediately on start, then re-syncs every
        *interval-ms* milliseconds.  The actor updates ForthActors._ntp_offset
        on each successful query; actor-time reads this offset.

        Use actor-kill to stop the sync actor.
        interval-ms = 0 means sync once and stop.

        Example: 300000 actor-ntp drop   ( sync every 5 minutes )
        """
        if not self.stack:
            print("Error: actor-ntp requiere ( interval-ms -- actor-id )")
            return
        interval_ms = int(self.stack.pop())

        with ForthActors._registry_lock:
            actor_id = ForthActors._next_id
            ForthActors._next_id += 1

        stop_evt  = threading.Event()
        ntp_queue = queue.Queue()

        def ntp_body():
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = True
            _do_ntp_sync()          # sync on start
            if interval_ms <= 0:
                with ForthActors._registry_lock:
                    if actor_id in ForthActors._registry:
                        ForthActors._registry[actor_id]['alive'] = False
                return
            while not stop_evt.wait(timeout=interval_ms / 1000.0):
                _do_ntp_sync()
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = False

        thread = threading.Thread(
            target=ntp_body,
            daemon=True,
            name=f"actor-ntp-{actor_id}",
        )
        with ForthActors._registry_lock:
            ForthActors._registry[actor_id] = {
                'thread':        thread,
                'queue':         ntp_queue,
                'name':          f'actor-ntp({interval_ms}ms)',
                'forth':         None,
                'alive':         False,
                'pending':       False,
                'type':          'ntp',
                '_timer_stop':   stop_evt,
                '_timer_thread': None,
            }

        thread.start()
        self.stack.append(actor_id)
        label = f"cada {interval_ms}ms" if interval_ms > 0 else "una vez"
        print(f"actor-ntp {actor_id} iniciado ({label}, servidor=pool.ntp.org)")

    def _actor_time(self):
        """( -- ms ) Push current Unix time in milliseconds, NTP-adjusted."""
        t_ms = int((time.time() + ForthActors._ntp_offset) * 1000)
        self.stack.append(t_ms)


# ── Module-level Phase 3 helpers ─────────────────────────────────────────────

def _make_actor_envelope(to_id, from_id, value):
    """Build a JSON-serialisable pfforth-actor message envelope."""
    try:
        json.dumps(value)
        safe_value = value
    except (TypeError, ValueError):
        safe_value = str(value)
    return {
        'proto': 'pfforth-actor',
        'v':     1,
        'to':    to_id,
        'from':  from_id,
        'msg':   safe_value,
    }


def _make_transport_frame(to_id, from_id, value):
    """Return a binary-framed JSON envelope for UART/SPI transport."""
    env     = _make_actor_envelope(to_id, from_id, value)
    payload = json.dumps(env, separators=(',', ':')).encode('utf-8')
    length  = len(payload)
    return bytes([0xAC, 0xE0, (length >> 8) & 0xFF, length & 0xFF]) + payload


def _find_uart_frame_start(buf):
    """Return index of 0xAC 0xE0 header in *buf*, or -1 if not found."""
    for i in range(len(buf) - 1):
        if buf[i] == 0xAC and buf[i + 1] == 0xE0:
            return i
    return -1


def _handle_tcp_in_conn(conn):
    """Handle a single incoming TCP connection: read newline-delimited JSON
    and deliver pfforth-actor envelopes to local actors."""
    try:
        buf = b''
        conn.settimeout(30)
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf += chunk
            while b'\n' in buf:
                line, buf = buf.split(b'\n', 1)
                try:
                    payload = json.loads(line.decode('utf-8'))
                except Exception:
                    continue
                if payload.get('proto') != 'pfforth-actor':
                    continue
                to_id   = payload.get('to', 0)
                from_id = payload.get('from', 0)
                value   = payload.get('msg')
                with ForthActors._registry_lock:
                    entry = ForthActors._registry.get(to_id)
                if entry:
                    entry['queue'].put(_ActorMsg(from_id, value))
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ── Transport OUT actor factories ──────────────────────────────────────────────

# Global cache: transport_key → actor_id  (avoids duplicate transport actors)
_transport_actor_cache = {}
_transport_cache_lock  = threading.Lock()


def _get_or_start_transport_out(forth_instance, key, start_fn):
    """Return an existing alive transport actor for *key*, or start a new one."""
    with _transport_cache_lock:
        ta_id = _transport_actor_cache.get(key)

    if ta_id is not None:
        with ForthActors._registry_lock:
            entry = ForthActors._registry.get(ta_id)
        if entry and entry.get('alive'):
            return ta_id

    # Start a fresh transport actor
    ta_id = start_fn()
    with _transport_cache_lock:
        _transport_actor_cache[key] = ta_id
    return ta_id


def _start_mqtt_out_actor(forth_instance, host, port, topic):
    """Start an MQTT OUT transport actor; return its actor_id.

    The actor receives _ActorMsg(sender_id, (to_id, value)) from the routing
    layer and publishes a JSON pfforth-actor envelope to *topic* via MQTT.
    """
    try:
        import paho.mqtt.client as mqtt  # noqa: F401
    except ImportError:
        print("Error: actor-wifi-out requiere paho-mqtt (pip install paho-mqtt)")
        return 0

    with ForthActors._registry_lock:
        actor_id = ForthActors._next_id
        ForthActors._next_id += 1

    ta_queue  = queue.Queue()
    stop_evt  = threading.Event()

    def body():
        with ForthActors._registry_lock:
            if actor_id in ForthActors._registry:
                ForthActors._registry[actor_id]['alive'] = True
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] actor-wifi-out ({actor_id}): "
              f"MQTT {host}:{port}/{topic} listo")
        while True:
            msg = ta_queue.get(block=True)
            if msg is _KILL_SENTINEL:
                break
            if not isinstance(msg, _ActorMsg) or not isinstance(msg.value, tuple):
                continue
            to_id, value = msg.value
            sender_id    = msg.sender_id
            env     = _make_actor_envelope(to_id, sender_id, value)
            payload = json.dumps(env, separators=(',', ':')).encode('utf-8')
            try:
                import paho.mqtt.client as mqtt
                client = mqtt.Client()
                client.connect(host, port, keepalive=10)
                client.publish(topic, payload, qos=1)
                client.disconnect()
            except Exception as e:
                ts2 = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts2}] actor-wifi-out error: {e}")
        with ForthActors._registry_lock:
            if actor_id in ForthActors._registry:
                ForthActors._registry[actor_id]['alive'] = False

    thread = threading.Thread(target=body, daemon=True,
                               name=f"actor-wifi-out-{actor_id}")
    with ForthActors._registry_lock:
        ForthActors._registry[actor_id] = {
            'thread':        thread,
            'queue':         ta_queue,
            'name':          f'wifi-out({host}:{port}/{topic})',
            'forth':         None,
            'alive':         False,
            'pending':       False,
            'type':          'wifi-out',
            '_timer_stop':   stop_evt,
            '_timer_thread': None,
        }
    thread.start()
    print(f"actor-wifi-out {actor_id} iniciado → MQTT {host}:{port}/{topic}")
    return actor_id


def _start_tcp_out_actor(forth_instance, host, port):
    """Start a TCP OUT transport actor; return its actor_id."""
    with ForthActors._registry_lock:
        actor_id = ForthActors._next_id
        ForthActors._next_id += 1

    ta_queue = queue.Queue()
    stop_evt = threading.Event()

    def body():
        with ForthActors._registry_lock:
            if actor_id in ForthActors._registry:
                ForthActors._registry[actor_id]['alive'] = True
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] actor-wifi-tcp-out ({actor_id}): TCP {host}:{port} listo")
        while True:
            msg = ta_queue.get(block=True)
            if msg is _KILL_SENTINEL:
                break
            if not isinstance(msg, _ActorMsg) or not isinstance(msg.value, tuple):
                continue
            to_id, value = msg.value
            sender_id    = msg.sender_id
            env     = _make_actor_envelope(to_id, sender_id, value)
            line    = (json.dumps(env, separators=(',', ':')) + '\n').encode('utf-8')
            try:
                s = socket.create_connection((host, port), timeout=5)
                s.sendall(line)
                s.close()
            except Exception as e:
                ts2 = datetime.now().strftime('%H:%M:%S')
                print(f"[{ts2}] actor-wifi-tcp-out error: {e}")
        with ForthActors._registry_lock:
            if actor_id in ForthActors._registry:
                ForthActors._registry[actor_id]['alive'] = False

    thread = threading.Thread(target=body, daemon=True,
                               name=f"actor-wifi-tcp-out-{actor_id}")
    with ForthActors._registry_lock:
        ForthActors._registry[actor_id] = {
            'thread':        thread,
            'queue':         ta_queue,
            'name':          f'tcp-out({host}:{port})',
            'forth':         None,
            'alive':         False,
            'pending':       False,
            'type':          'tcp-out',
            '_timer_stop':   stop_evt,
            '_timer_thread': None,
        }
    thread.start()
    print(f"actor-wifi-tcp-out {actor_id} iniciado → TCP {host}:{port}")
    return actor_id


def _start_uart_out_actor(forth_instance, device, baud):
    """Start a UART OUT transport actor; return its actor_id.

    Requires pyserial.  Each message is written as a binary frame.
    """
    try:
        import serial  # noqa: F401
    except ImportError:
        print("Error: UART transport requiere pyserial (pip install pyserial)")
        return 0

    with ForthActors._registry_lock:
        actor_id = ForthActors._next_id
        ForthActors._next_id += 1

    ta_queue = queue.Queue()
    stop_evt = threading.Event()

    def body():
        import serial as _serial
        try:
            ser = _serial.Serial(device, baud, timeout=2)
        except Exception as e:
            print(f"actor-uart-out: no se puede abrir {device}: {e}")
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = False
            return
        with ForthActors._registry_lock:
            if actor_id in ForthActors._registry:
                ForthActors._registry[actor_id]['alive'] = True
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] actor-uart-out ({actor_id}): {device}@{baud} listo")
        try:
            while True:
                msg = ta_queue.get(block=True)
                if msg is _KILL_SENTINEL:
                    break
                if not isinstance(msg, _ActorMsg) or not isinstance(msg.value, tuple):
                    continue
                to_id, value = msg.value
                sender_id    = msg.sender_id
                frame = _make_transport_frame(to_id, sender_id, value)
                try:
                    ser.write(frame)
                except Exception as e:
                    ts2 = datetime.now().strftime('%H:%M:%S')
                    print(f"[{ts2}] actor-uart-out error: {e}")
        finally:
            try:
                ser.close()
            except Exception:
                pass
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = False

    thread = threading.Thread(target=body, daemon=True,
                               name=f"actor-uart-out-{actor_id}")
    with ForthActors._registry_lock:
        ForthActors._registry[actor_id] = {
            'thread':        thread,
            'queue':         ta_queue,
            'name':          f'uart-out({device}@{baud})',
            'forth':         None,
            'alive':         False,
            'pending':       False,
            'type':          'uart-out',
            '_timer_stop':   stop_evt,
            '_timer_thread': None,
        }
    thread.start()
    print(f"actor-uart-out {actor_id} iniciado → {device}@{baud}")
    return actor_id


def _start_spi_out_actor(forth_instance, device, speed):
    """Start an SPI OUT transport actor; return its actor_id.

    Requires spidev (Linux).  Writes binary-framed JSON envelopes.
    device — bus.device string, e.g. '0.0'
    """
    try:
        import spidev  # noqa: F401
    except ImportError:
        print("Error: SPI transport requiere spidev (pip install spidev, Linux)")
        return 0

    with ForthActors._registry_lock:
        actor_id = ForthActors._next_id
        ForthActors._next_id += 1

    ta_queue = queue.Queue()
    stop_evt = threading.Event()

    def body():
        import spidev as _spidev
        parts = str(device).split('.')
        bus, dev_num = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        spi = _spidev.SpiDev()
        try:
            spi.open(bus, dev_num)
            spi.max_speed_hz = speed
        except Exception as e:
            print(f"actor-spi-out: no se puede abrir /dev/spidev{device}: {e}")
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = False
            return
        with ForthActors._registry_lock:
            if actor_id in ForthActors._registry:
                ForthActors._registry[actor_id]['alive'] = True
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] actor-spi-out ({actor_id}): "
              f"/dev/spidev{device}@{speed}Hz listo")
        try:
            while True:
                msg = ta_queue.get(block=True)
                if msg is _KILL_SENTINEL:
                    break
                if not isinstance(msg, _ActorMsg) or not isinstance(msg.value, tuple):
                    continue
                to_id, value = msg.value
                sender_id    = msg.sender_id
                frame = _make_transport_frame(to_id, sender_id, value)
                try:
                    spi.writebytes(list(frame))
                except Exception as e:
                    ts2 = datetime.now().strftime('%H:%M:%S')
                    print(f"[{ts2}] actor-spi-out error: {e}")
        finally:
            try:
                spi.close()
            except Exception:
                pass
            with ForthActors._registry_lock:
                if actor_id in ForthActors._registry:
                    ForthActors._registry[actor_id]['alive'] = False

    thread = threading.Thread(target=body, daemon=True,
                               name=f"actor-spi-out-{actor_id}")
    with ForthActors._registry_lock:
        ForthActors._registry[actor_id] = {
            'thread':        thread,
            'queue':         ta_queue,
            'name':          f'spi-out({device}@{speed}Hz)',
            'forth':         None,
            'alive':         False,
            'pending':       False,
            'type':          'spi-out',
            '_timer_stop':   stop_evt,
            '_timer_thread': None,
        }
    thread.start()
    print(f"actor-spi-out {actor_id} iniciado → SPI /dev/spidev{device}@{speed}Hz")
    return actor_id


def _do_ntp_sync(server='pool.ntp.org'):
    """Perform one NTP query and update ForthActors._ntp_offset in-place."""
    offset = _ntp_query(server)
    ts = datetime.now().strftime('%H:%M:%S')
    if offset is not None:
        ForthActors._ntp_offset = offset
        print(f"[{ts}] actor-ntp: sync OK offset={offset:+.3f}s")
    else:
        print(f"[{ts}] actor-ntp: sync falló (sin red o timeout)")


def _ntp_query(server='pool.ntp.org'):
    """Return NTP offset (seconds) to add to time.time() for accurate UTC.

    Uses a raw UDP NTP v3 query — no extra libraries needed.
    Returns None on failure.
    """
    NTP_DELTA = 2208988800   # seconds between 1 Jan 1900 and 1 Jan 1970
    NTP_QUERY = b'\x1b' + 47 * b'\x00'   # NTP v3 client packet
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(4)
        t0 = time.time()
        s.sendto(NTP_QUERY, (server, 123))
        data, _ = s.recvfrom(48)
        t1 = time.time()
        s.close()
    except Exception:
        return None

    if len(data) < 48:
        return None

    # Transmit timestamp is at bytes 40-47 (two 32-bit words: seconds + fraction)
    tx_sec  = struct.unpack('!I', data[40:44])[0]
    tx_frac = struct.unpack('!I', data[44:48])[0]
    ntp_time = tx_sec + tx_frac / 2**32 - NTP_DELTA

    # Offset = NTP_time − local_time (midpoint of the round trip)
    local_mid = (t0 + t1) / 2
    return ntp_time - local_mid


# ── Module-level log helper (used by watchdog) ────────────────────────────────

def _send_to_log(from_id, text, level='info'):
    """Send a message to the centralized logger if it is running."""
    log_id = getattr(ForthActors, '_log_actor_id', None)
    if log_id is None:
        return
    with ForthActors._registry_lock:
        entry = ForthActors._registry.get(log_id)
    if entry and entry.get('alive'):
        payload = {'level': level, 'msg': text, 'from': from_id}
        entry['queue'].put(_ActorMsg(from_id, payload))
