"""
PFForth Persistence - SAVE/LOAD, CODE/ENDCODE
"""

import os
import sys
import math
import time
import subprocess
import platform
from collections import defaultdict


class ForthPersistence:
    """Mixin providing persistence operations"""
    
    def _sanitize_code_path(self, path, allow_extension=False):
        """Sanitiza y valida un path para CODE/IMPORT/RMCODE"""
        base_dir = os.path.abspath(os.path.join(self._base_dir, 'extended-code'))
        try:
            return self._sanitize_relative_path(path, base_dir)
        except ValueError:
            return None
    
    def _sanitize_save_path(self, path):
        """Sanitiza y valida un path para SAVE/LOAD"""
        if not path.endswith('.fth'):
            path = path + '.fth'
        base_dir = os.path.abspath(self._base_dir)
        try:
            return self._sanitize_relative_path(path, base_dir)
        except ValueError:
            return None
    
    def _register_persistence_words(self):
        """Register persistence words"""
        self.words['save'] = self._save_words
        self.words['load'] = self._load_file
        self.words['lssave'] = self._lssave
        self.words['rmsave'] = self._rmsave_stub
        
        self.words['code'] = self._code_stub
        self.words['endcode'] = self._endcode_stub
        self.words['import'] = self._import_stub
        self.words['lscode'] = self._lscode
        self.words['vlist'] = self._vlist
        self.words['rmcode'] = self._rmcode_stub
        self.words['seecode'] = self._seecode_stub
        self.words['edit'] = self._edit_file
    
    def _save_words(self):
        """Save user definitions to a file"""
        if not self.stack:
            print("Error: SAVE requiere nombre de archivo")
            return
        
        filename = self.stack.pop()
        if not isinstance(filename, str):
            print("Error: nombre de archivo debe ser string")
            return
        
        if not filename.endswith('.fth'):
            filename += '.fth'
        
        try:
            dir_path = os.path.dirname(filename)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            with open(filename, 'w') as f:
                f.write("\\ Forth definitions saved by PFForth\n")
                f.write(f"\\ Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for def_type, name in self._definition_order:
                    if name in self._definition_source:
                        f.write(self._definition_source[name] + "\n\n")
                    elif def_type == 'variable':
                        f.write(f"variable {name}\n")
                    elif def_type == 'constant' and name in self.constants:
                        f.write(f"{self.constants[name]} constant {name}\n")
                    elif def_type == 'value' and name in self.values:
                        f.write(f"{self.values[name]} value {name}\n")
            
            print(f"Guardado: {filename}")
        except Exception as e:
            print(f"Error guardando: {e}")
    
    def _load_file(self):
        """Load and execute Forth code from a file"""
        if not self.stack:
            print("Error: LOAD requiere nombre de archivo")
            return
        
        filename = self.stack.pop()
        if not isinstance(filename, str):
            print("Error: nombre de archivo debe ser string")
            return
        
        if not filename.endswith('.fth'):
            filename += '.fth'
        
        search_paths = [
            filename,
            os.path.join(self._base_dir, 'extended-code', filename),
            os.path.join(self._base_dir, 'extended-code', 'forth', filename),
        ]
        
        found_path = None
        for path in search_paths:
            if os.path.exists(path):
                found_path = path
                break
        
        if not found_path:
            print(f"Error: archivo no encontrado: {filename}")
            return
        
        try:
            with open(found_path, 'r') as f:
                code = f.read()
            self.execute(code)
            print(f"Cargado: {found_path}")
        except Exception as e:
            print(f"Error cargando: {e}")
    
    def _lssave(self):
        """List saved .fth files including extended-code/forth/"""
        print("\n=== Archivos Forth Disponibles ===\n")
        
        files_by_dir = defaultdict(list)
        seen_files = set()
        
        forth_dir = os.path.join(self._base_dir, 'extended-code', 'forth')
        
        if os.path.exists(forth_dir):
            for root, dirs, files in os.walk(forth_dir):
                for file in files:
                    if file.endswith('.fth'):
                        full_path = os.path.join(root, file)
                        sub_path = os.path.relpath(root, forth_dir)
                        if sub_path == '.':
                            rel_dir = 'forth'
                        else:
                            rel_dir = 'forth/' + sub_path
                        stat = os.stat(full_path)
                        file_key = (rel_dir, file)
                        if file_key not in seen_files:
                            seen_files.add(file_key)
                            files_by_dir[rel_dir].append({
                                'name': file,
                                'size': stat.st_size,
                                'mtime': stat.st_mtime
                            })
        
        if not files_by_dir:
            print("No hay archivos .fth")
            return self
        
        for dir_name in sorted(files_by_dir.keys()):
            if dir_name == '.':
                print("./")
            else:
                print(f"{dir_name}/")
            
            for file_info in sorted(files_by_dir[dir_name], key=lambda x: x['name']):
                size = file_info['size']
                mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(file_info['mtime']))
                print(f"   {file_info['name']:30} {size:6} bytes  {mtime}")
            print()
        
        return self
    
    def _rmsave_stub(self):
        print("Error: RMSAVE requiere nombre de archivo")
    
    def _code_stub(self):
        print("Error: CODE requiere nombre (grupo/nombre)")
    
    def _endcode_stub(self):
        print("Error: ENDCODE sin CODE previo")
    
    def _import_stub(self):
        print("Error: IMPORT requiere nombre (grupo/nombre)")
    
    def _lscode(self):
        """List available CODE words (.py only)"""
        base_dir = os.path.join(self._base_dir, 'extended-code')
        
        if not os.path.exists(base_dir):
            print("No hay palabras CODE (carpeta extended-code/ no existe)")
            return self
        
        print("\n=== Palabras CODE Disponibles ===\n")
        
        groups = {}
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.py'):
                    group = os.path.relpath(root, base_dir)
                    if group == '.':
                        group = '(raiz)'
                    word_name = file[:-3]
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(word_name)
        
        if not groups:
            print("No hay palabras CODE")
            return self
        
        for group in sorted(groups.keys()):
            print(f"📁 {group}/")
            for word in sorted(groups[group]):
                is_loaded = word in self.words or word in self.immediate_words
                status = "✓" if is_loaded else "○"
                print(f"   {status} {word}")
            print()
        
        print("Leyenda: ✓=cargada  ○=no cargada")
        print("Uso: import grupo/nombre")
        
        return self
    
    def _vlist(self):
        """List available vocabularies"""
        base_dir = os.path.join(self._base_dir, 'extended-code')
        
        if not os.path.exists(base_dir):
            print("No hay vocabularios")
            return self
        
        print("\n=== Vocabularios Disponibles ===\n")
        
        vocabularies = set()
        for root, dirs, files in os.walk(base_dir):
            has_code = any(f.endswith('.py') for f in files)
            if has_code:
                vocab = os.path.relpath(root, base_dir)
                if vocab != '.':
                    vocabularies.add(vocab)
        
        if not vocabularies:
            print("No hay vocabularios con palabras CODE")
            return self
        
        for vocab in sorted(vocabularies):
            print(f"📁 {vocab}/")
        
        print(f"\nTotal: {len(vocabularies)} vocabulario(s)")
        
        return self
    
    def _rmcode_stub(self):
        print("Error: RMCODE requiere nombre (grupo/nombre)")
    
    def _seecode_stub(self):
        print("Error: SEECODE requiere nombre (grupo/nombre)")
    
    def _rmcode(self, import_name):
        """Delete a CODE word file (.py only)"""
        if '/' not in import_name:
            print(f"Error: nombre RMCODE debe incluir path, ej: 'utils/double'")
            return
        
        try:
            import_name = self._sanitize_code_path(import_name)
        except ValueError as e:
            print(f"Error: path inválido '{import_name}': {e}")
            return
        
        parts = import_name.split('/')
        word_name = parts[-1]
        relative_path = '/'.join(parts[:-1])
        
        base_dir = os.path.join(self._base_dir, 'extended-code')
        file_path = os.path.join(base_dir, relative_path, f"{word_name}.py")
        
        if not os.path.exists(file_path):
            print(f"Error: archivo no encontrado: extended-code/{import_name}.py")
            return
        
        try:
            os.remove(file_path)
            print(f"✓ Archivo eliminado: extended-code/{import_name}.py")
            
            if relative_path:
                dir_path = os.path.abspath(os.path.join(base_dir, relative_path))
                base_dir_abs = os.path.abspath(base_dir)
                
                try:
                    while dir_path != base_dir_abs:
                        try:
                            common = os.path.commonpath([base_dir_abs, dir_path])
                            if common != base_dir_abs:
                                break
                        except ValueError:
                            break
                        
                        if os.path.isdir(dir_path):
                            contents = os.listdir(dir_path)
                            if contents == ['__pycache__']:
                                pycache_dir = os.path.join(dir_path, '__pycache__')
                                if os.path.isdir(pycache_dir):
                                    for item in os.listdir(pycache_dir):
                                        os.remove(os.path.join(pycache_dir, item))
                                    os.rmdir(pycache_dir)
                                contents = []
                            if not contents:
                                os.rmdir(dir_path)
                                dir_path = os.path.dirname(dir_path)
                            else:
                                break
                        else:
                            break
                except OSError:
                    pass
            
            if word_name in self.words or word_name in self.immediate_words:
                print(f"  (La palabra '{word_name}' sigue en memoria - usa FORGET {word_name} para eliminarla)")
            
        except Exception as e:
            print(f"Error eliminando {import_name}: {e}")
    
    def _seecode(self, import_name):
        """Display the code of a CODE word (.py only)"""
        if '/' not in import_name:
            print(f"Error: nombre SEECODE debe incluir path, ej: 'utils/double'")
            return
        
        try:
            import_name = self._sanitize_code_path(import_name)
        except ValueError as e:
            print(f"Error: path inválido '{import_name}': {e}")
            return
        
        parts = import_name.split('/')
        word_name = parts[-1]
        relative_path = '/'.join(parts[:-1])
        
        base_dir = os.path.join(self._base_dir, 'extended-code')
        file_path = os.path.join(base_dir, relative_path, f"{word_name}.py")
        
        if not os.path.exists(file_path):
            print(f"Error: archivo no encontrado: extended-code/{import_name}.py")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n=== CÓDIGO: {import_name} ===\n")
            print(content)
            print(f"=== FIN ===\n")
            
        except Exception as e:
            print(f"Error leyendo {import_name}: {e}")
    
    def _create_code_word(self, full_name, code_text):
        """Create a CODE word from Python code"""
        try:
            parts = full_name.split('/')
            word_name = parts[-1]
            
            if self._is_system_word(word_name):
                print(f"Error: '{word_name}' es palabra del sistema")
                return
            
            def push(val):
                self.stack.append(val)
            
            def pop():
                if not self.stack:
                    raise IndexError("Stack underflow")
                return self.stack.pop()
            
            def peek():
                if not self.stack:
                    raise IndexError("Stack empty")
                return self.stack[-1]
            
            local_namespace = {
                'self': self,
                'push': push,
                'pop': pop,
                'peek': peek,
                'math': math,
            }
            
            try:
                compiled_code = compile(code_text, f'<CODE {full_name}>', 'exec')
            except SyntaxError as e:
                print(f"Error de sintaxis: {e}")
                return
            
            def code_word_wrapper():
                try:
                    exec(compiled_code, local_namespace)
                except Exception as e:
                    print(f"Error: {e}")
            
            self.words[word_name] = code_word_wrapper
            self._definition_order.append(('code', word_name))
            self._definition_source[word_name] = f"CODE {full_name}\n{code_text}\nENDCODE"
            self._last_defined_word = word_name
            
            self._save_code_word_to_file(full_name, word_name, code_text)
            
            print(f"✓ Palabra CODE '{word_name}' creada")
            
        except Exception as e:
            print(f"Error: {e}")
    
    def _save_code_word_to_file(self, full_name, word_name, code_text):
        """Save CODE word to file"""
        try:
            parts = full_name.split('/')
            relative_path = '/'.join(parts[:-1])
            
            base_dir = os.path.join(self._base_dir, 'extended-code')
            os.makedirs(base_dir, exist_ok=True)
            
            path_dir = os.path.join(base_dir, relative_path)
            os.makedirs(path_dir, exist_ok=True)
            
            file_path = os.path.join(path_dir, f"{word_name}.py")
            
            forth_code_lines = '\n'.join('# ' + line for line in code_text.split('\n'))
            
            content = f'''# FORTH CODE WORD: {full_name}
# Auto-generated by CODE/ENDCODE
#
# === CÓDIGO FORTH ORIGINAL ===
# CODE {full_name}
{forth_code_lines}
# ENDCODE
# === FIN CÓDIGO FORTH ===

def execute(forth):
    def push(val):
        forth.stack.append(val)
    def pop():
        if not forth.stack:
            raise IndexError("Stack underflow")
        return forth.stack.pop()
    def peek():
        if not forth.stack:
            raise IndexError("Stack empty")
        return forth.stack[-1]
    
{chr(10).join("    " + line for line in code_text.split(chr(10)))}
'''
            
            with open(file_path, 'w') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Advertencia: no se pudo guardar: {e}")
    
    def _import_code_word(self, full_name):
        """Import a CODE word from file (.py)"""
        try:
            parts = full_name.split('/')
            word_name = parts[-1]
            
            base_dir = os.path.join(self._base_dir, 'extended-code')
            file_path = os.path.join(base_dir, full_name + '.py')
            
            if not os.path.exists(file_path):
                print(f"Error: no existe {full_name}")
                return
            
            import importlib.util
            spec = importlib.util.spec_from_file_location(word_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'execute'):
                def wrapper():
                    module.execute(self)
                
                actual_name = getattr(module, 'WORD_NAME', word_name)
                self.words[actual_name] = wrapper
                self._definition_order.append(('code', actual_name))
                self._last_defined_word = actual_name
                
                print(f"✓ Importada: {actual_name}")
            else:
                print(f"Error: {full_name} no tiene funcion execute()")
                
        except Exception as e:
            print(f"Error importando: {e}")

    def _edit_file(self):
        """( str -- ) Abre un archivo para editar con el editor del sistema"""
        if not self.stack:
            print("Error: edit requiere nombre de archivo")
            print("Uso: s\" nombre\" edit")
            print("  Busca en: extended-code/code/*.py y extended-code/forth/*.fth")
            return

        name = self.stack.pop()
        if not isinstance(name, str):
            print("Error: edit requiere un string")
            return

        file_path = self._find_editable_file(name)
        if not file_path:
            return

        rel_path = os.path.relpath(file_path, self._base_dir)
        print(f"Editando: {rel_path}")

        if self._open_system_editor(file_path):
            return

        if self._is_replit():
            print(f"(En Replit puedes editar este archivo desde el panel de archivos)")
        self._mini_editor(file_path)

    def _find_editable_file(self, name):
        """Busca archivo en code/ (.py) o forth/ (.fth)"""
        base = os.path.join(self._base_dir, 'extended-code')
        candidates = []

        code_path = os.path.join(base, 'code', name + '.py')
        if os.path.exists(code_path):
            candidates.append(code_path)

        code_path2 = os.path.join(base, name + '.py')
        if os.path.exists(code_path2):
            candidates.append(code_path2)

        forth_path = os.path.join(base, 'forth', name + '.fth')
        if os.path.exists(forth_path):
            candidates.append(forth_path)

        forth_path2 = os.path.join(self._base_dir, name + '.fth')
        if os.path.exists(forth_path2):
            candidates.append(forth_path2)

        if name.endswith('.py') or name.endswith('.fth'):
            direct = os.path.join(base, name)
            if os.path.exists(direct):
                candidates.append(direct)
            direct2 = os.path.join(base, 'code', name)
            if os.path.exists(direct2):
                candidates.append(direct2)
            direct3 = os.path.join(base, 'forth', name)
            if os.path.exists(direct3):
                candidates.append(direct3)

        seen = []
        for c in candidates:
            c = os.path.abspath(c)
            if c not in seen:
                seen.append(c)

        if not seen:
            print(f"Error: archivo '{name}' no encontrado")
            print("Buscado en:")
            print(f"  extended-code/code/{name}.py")
            print(f"  extended-code/forth/{name}.fth")
            return None

        if len(seen) == 1:
            return seen[0]

        print("Varios archivos encontrados:")
        for i, path in enumerate(seen, 1):
            rel = os.path.relpath(path, self._base_dir)
            print(f"  {i}. {rel}")
        try:
            choice = input("Elige (numero): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(seen):
                return seen[idx]
        except (ValueError, EOFError):
            pass
        print("Seleccion no valida")
        return None

    def _is_replit(self):
        """Detecta si estamos en entorno Replit"""
        return bool(os.environ.get('REPL_ID') or os.environ.get('REPLIT_DB_URL') or os.environ.get('REPL_SLUG'))

    def _open_system_editor(self, file_path):
        """Intenta abrir el editor del sistema segun la plataforma"""
        if self._is_replit():
            return False

        system = platform.system()

        try:
            if hasattr(sys, '_running_in_ashell') or os.environ.get('ASHELL'):
                os.system(f'open "{file_path}"')
                input("Pulsa Enter cuando termines de editar...")
                return True
        except Exception:
            pass

        try:
            if system == 'Darwin':
                subprocess.Popen(['open', '-t', '-W', file_path])
                return True
            elif system == 'Windows':
                os.startfile(file_path)
                input("Pulsa Enter cuando termines de editar...")
                return True
            elif system == 'Linux':
                editor = os.environ.get('EDITOR', '')
                if editor:
                    os.system(f'{editor} "{file_path}"')
                    return True
                try:
                    subprocess.Popen(['xdg-open', file_path])
                    input("Pulsa Enter cuando termines de editar...")
                    return True
                except FileNotFoundError:
                    pass
        except Exception:
            pass

        return False

    def _mini_editor(self, file_path):
        """Editor de lineas simple como fallback"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
        except Exception:
            lines = []

        lines = [l.rstrip('\n') for l in lines]

        print("\n=== Mini Editor ===")
        print("Comandos: [numero] edita linea, +[texto] añade linea")
        print("  d[numero] borra linea, i[numero] inserta antes")
        print("  l lista, s guarda, q sale, sq guarda y sale")
        print()
        self._show_lines(lines)

        while True:
            try:
                cmd = input("edit> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not cmd:
                continue
            elif cmd == 'q':
                print("Saliendo sin guardar")
                break
            elif cmd == 's':
                self._save_lines(file_path, lines)
                print(f"Guardado: {file_path}")
            elif cmd == 'sq':
                self._save_lines(file_path, lines)
                print(f"Guardado: {file_path}")
                break
            elif cmd == 'l':
                self._show_lines(lines)
            elif cmd.startswith('+'):
                lines.append(cmd[1:])
                print(f"  {len(lines):4}: {cmd[1:]}")
            elif cmd.startswith('d'):
                try:
                    n = int(cmd[1:])
                    if 1 <= n <= len(lines):
                        removed = lines.pop(n - 1)
                        print(f"Borrada linea {n}: {removed}")
                    else:
                        print(f"Linea {n} fuera de rango (1-{len(lines)})")
                except ValueError:
                    print("Uso: d[numero]  Ej: d3")
            elif cmd.startswith('i'):
                try:
                    n = int(cmd[1:])
                    if 1 <= n <= len(lines) + 1:
                        text = input(f"  Texto para linea {n}: ")
                        lines.insert(n - 1, text)
                        print(f"  Insertada linea {n}")
                    else:
                        print(f"Posicion {n} fuera de rango (1-{len(lines) + 1})")
                except ValueError:
                    print("Uso: i[numero]  Ej: i3")
            else:
                try:
                    n = int(cmd)
                    if 1 <= n <= len(lines):
                        print(f"  Actual: {lines[n - 1]}")
                        new_text = input(f"  Nueva : ")
                        lines[n - 1] = new_text
                        print(f"  {n:4}: {new_text}")
                    else:
                        print(f"Linea {n} fuera de rango (1-{len(lines)})")
                except ValueError:
                    print("Comando no reconocido. Usa 'l' para listar, 'q' para salir")

    def _show_lines(self, lines):
        """Muestra las lineas numeradas"""
        if not lines:
            print("  (archivo vacio)")
        else:
            for i, line in enumerate(lines, 1):
                print(f"  {i:4}: {line}")
        print()

    def _save_lines(self, file_path, lines):
        """Guarda las lineas al archivo"""
        with open(file_path, 'w') as f:
            for line in lines:
                f.write(line + '\n')
