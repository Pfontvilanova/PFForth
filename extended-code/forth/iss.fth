\ ════════════════════════════════════════════════════════
\  ISS Position — International Space Station tracker
\  Uso: load iss
\       iss-pos    → deja ( lat lon ) en la pila
\       iss.       → muestra posición completa
\ ════════════════════════════════════════════════════════

import code/wifi/httpget
import code/wifi/httpjson
import code/utils/dictget

\ ── ISS posición: deja lat lon en la pila ───────────────
\ ( -- lat lon )

: iss-pos
  s" http://api.open-notify.org/iss-now.json"
  http-get http-json
  s" iss_position" dict@
  dup  s" latitude"  dict@
  swap s" longitude" dict@
;

\ ── Muestra posición completa con timestamp ─────────────
\ ( -- )

: iss.
  s" http://api.open-notify.org/iss-now.json"
  http-get http-json            \ ( dict )
  dup  s" timestamp"    dict@   \ ( dict timestamp )
  ." Timestamp : " . cr
  s" iss_position" dict@        \ ( pos-dict )
  dup  s" latitude"  dict@      \ ( pos-dict lat )
  ." Latitud   : " . cr
       s" longitude" dict@      \ ( lon )
  ." Longitud  : " . cr
;

.( ISS listo.  Palabras: iss-pos  iss.) cr
