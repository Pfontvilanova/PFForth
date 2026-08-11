\ life.fth — Joc de la Vida de Conway per a pfforth
\
\ Regles d'evolucio (comptant els 8 veins de cada cel·la):
\   1. Viva amb menys de 2 veins  -> mor (soledat)
\   2. Viva amb 2 o 3 veins       -> sobreviu
\   3. Viva amb mes de 3 veins    -> mor (superpoblacio)
\   4. Morta amb exactament 3     -> neix
\
\ Mon toroidal: les vores es connecten (dreta<->esquerra, dalt<->baix).
\
\ Us:
\   load forth/life.fth
\   glider   life-show          ( posa un glider i mostra'l )
\   20 life-run                 ( 20 generacions animades )
\   gosper   100 life-run       ( pistola de Gosper, 100 generacions )
\   blinker  6 life-run         ( oscil·lador simple )

70 constant cols
30 constant rows

create grid   cols rows * cells allot
create grid2  cols rows * cells allot

\ --- acces a la graella ---
: xy>addr   ( x y -- addr )   cols * + cells grid  + ;
: xy>addr2  ( x y -- addr )   cols * + cells grid2 + ;
: cell@     ( x y -- v )      xy>addr @ ;
: cell!     ( v x y -- )      xy>addr ! ;
: cell2!    ( v x y -- )      xy>addr2 ! ;

: wrap-x    ( x -- x' )       cols + cols mod ;
: wrap-y    ( y -- y' )       rows + rows mod ;

: life-clear  ( -- )
    cols rows * 0 do
        0 grid  i cells + !
        0 grid2 i cells + !
    loop ;

: set  ( x y -- )   1 -rot cell! ;

\ --- comptar els 8 veins (amb embolcall toroidal) ---
variable ncount
: neighbors  ( x y -- n )
    0 ncount !
    2 -1 do                          \ j = dy : -1 0 1
        2 -1 do                      \ i = dx : -1 0 1
            i 0= j 0= and not if
                over i + wrap-x      ( x y x' )
                over j + wrap-y      ( x y x' y' )
                cell@ ncount +!
            then
        loop
    loop
    2drop ncount @ ;

\ --- cami rapid: cel·les interiors (sense embolcall, offsets directes) ---
: xy>i  ( x y -- i )   cols * + ;
: g@    ( i -- v )     cells grid + @ ;

: fast-n  ( i -- n )                 \ suma els 8 veins per index directe
    dup cols - 1- g@
    over cols -    g@ +
    over cols - 1+ g@ +
    over 1-        g@ +
    over 1+        g@ +
    over cols + 1- g@ +
    over cols +    g@ +
    swap cols + 1+ g@ + ;

: in-range   ( v lim -- f )   1- over > swap 0 > and ;   \ 0 < v < lim-1
: interior?  ( x y -- f )     rows in-range swap cols in-range and ;

\ --- les 4 regles ---
: rule  ( n viva? -- v )
    if   \ viva: sobreviu amb 2 o 3 (regles 1,2,3)
        dup 2 = swap 3 = or if 1 else 0 then
    else \ morta: neix amb exactament 3 (regla 4)
        3 = if 1 else 0 then
    then ;

: new-state  ( x y -- v )
    2dup interior? if
        2dup xy>i fast-n             ( x y n )  \ interior: sense mod
    else
        2dup neighbors               ( x y n )  \ vora: amb embolcall
    then
    -rot cell@ rule ;

\ --- una generacio: calcula a grid2, despres copia a grid ---
: life-step  ( -- )
    rows 0 do
        cols 0 do
            i j new-state  i j cell2!
        loop
    loop
    cols rows * 0 do
        grid2 i cells + @  grid i cells + !
    loop ;

\ --- visualitzacio: * = viva, sp = morta ---
: life-show  ( -- )
    rows 0 do
        cols 0 do
            i j cell@ if 42 else 32 then emit
        loop cr
    loop ;

\ --- animacio: esborra pantalla entre generacions ---
10 value life-delay              \ pausa entre generacions en ms

: life-run  ( n -- )
    0 do
        page
        life-show
        life-step
        life-delay ms
    loop ;

\ --- patrons ---

\ Glider: camina en diagonal avall-dreta
: glider  ( -- )
    life-clear
    2 1 set
    3 2 set
    1 3 set  2 3 set  3 3 set ;

\ Blinker: oscil·lador de periode 2
: blinker  ( -- )
    life-clear
    18 11 set  19 11 set  20 11 set ;

\ Pistola de Gosper: genera un glider cada 30 generacions
: gosper  ( -- )
    life-clear
    \ quadrat esquerre
    2 6 set   3 6 set   2 7 set   3 7 set
    \ cos principal
    12 6 set  12 7 set  12 8 set
    13 5 set  13 9 set
    14 4 set  14 10 set
    15 4 set  15 10 set
    16 7 set
    17 5 set  17 9 set
    18 6 set  18 7 set  18 8 set
    19 7 set
    \ segona nau
    22 4 set  22 5 set  22 6 set
    23 4 set  23 5 set  23 6 set
    24 3 set  24 7 set
    26 2 set  26 3 set  26 7 set  26 8 set
    \ quadrat dret
    36 4 set  37 4 set  36 5 set  37 5 set ;

." life.fth carregat. Graella " cols . ." x" rows . cr
." Patrons: glider  blinker  gosper" cr
." Us: glider life-show   |   gosper 100 life-run" cr
