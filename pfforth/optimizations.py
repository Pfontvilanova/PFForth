"""
PFForth Optimizations - Inline caching
"""


class ForthOptimizations:
    """Mixin providing optimization controls"""
    
    def _register_optimization_words(self):
        """Register optimization words"""
        self.words['cache-on'] = self._cache_on
        self.words['cache-off'] = self._cache_off
        self.words['cache?'] = self._cache_status
    
    def _cache_on(self):
        self._use_inline_cache = True
        print("Inline caching activado")
    
    def _cache_off(self):
        self._use_inline_cache = False
        print("Inline caching desactivado")
    
    def _cache_status(self):
        status = "activado" if self._use_inline_cache else "desactivado"
        print(f"Inline caching: {status}")
    
    def enable_inline_cache(self):
        """Enable inline caching (Python API)"""
        self._use_inline_cache = True
        return self
    
    def disable_inline_cache(self):
        """Disable inline caching (Python API)"""
        self._use_inline_cache = False
        return self
