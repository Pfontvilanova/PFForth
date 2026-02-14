\ Forth definitions saved by PFForth
\ Date: 2026-01-23 15:16:00
\ fa servir variables locals.
: fibo { a b c -- } 0 to a 1 to b c 0 do a . a b + b to a to b loop ;

