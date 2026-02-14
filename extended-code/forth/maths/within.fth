\ WITHIN - Check if value is within range
\ ( n lo hi -- flag )
\ Returns true (-1) if lo <= n < hi, false (0) otherwise

: within  ( n lo hi -- flag )
  over over >=    \ n >= lo
  -rot >          \ n < hi
  and swap drop ;
