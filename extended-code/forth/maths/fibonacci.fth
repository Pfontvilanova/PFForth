\ Forth definitions saved by PFForth
\ Date: 2026-01-26 21:55:17

: fibo { a b c -- } 0 to a 1 to b c 0 do a . a b + b to a to b loop ;

: fibonacci 0 1 rot 0 do swap over + loop drop ;

: nfibo 0 1 rot 0 do over . swap over + loop ;

: pfibo py[
import sympy
n=pop()
r=fibonacci(n)
push(r)
]py ;