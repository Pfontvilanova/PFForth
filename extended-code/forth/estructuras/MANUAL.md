# Manual de la Librería de Estructuras

Cálculo de vigas con pfforth. Unidades: **mm · N · N/mm² · N·mm**

---

## Carga

Desde el directorio `extended-code/forth/`:

```forth
s" estructuras/estructuras" load
```

---

## Flujo de trabajo

```
1. Material   →   2. Perfil   →   3. Apoyo   →   4. Cargas   →   5. Resultados
```

```forth
acero           \ 1. material
ipe200          \ 2. perfil
biapoyada       \ 3. condición de apoyo + tipo de carga
5000.0 L!       \ 4a. longitud en mm  (5 m = 5000 mm)
0.5    q!       \ 4b. carga distribuida en N/mm  (0.5 kN/m = 0.5 N/mm)
flecha          \ 5. calcular y mostrar la flecha
```

---

## Materiales

| Palabra    | E (N/mm²) | fy (N/mm²) |
|------------|-----------|------------|
| `acero`    | 210 000   | 355        |
| `aluminio` |  70 000   | 150        |
| `madera`   |  11 000   |  24        |
| `hormigon` |  30 000   |  30        |

---

## Perfiles

### IPE  (alas paralelas, uso general)

| Palabra   | I (cm⁴)  | I (mm⁴)      |
|-----------|---------|--------------|
| `ipe80`   |    80   |    801 000   |
| `ipe100`  |   171   |  1 710 000   |
| `ipe120`  |   318   |  3 180 000   |
| `ipe140`  |   541   |  5 410 000   |
| `ipe160`  |   869   |  8 690 000   |
| `ipe180`  |  1 317  | 13 170 000   |
| `ipe200`  |  1 943  | 19 430 000   |
| `ipe220`  |  2 772  | 27 720 000   |
| `ipe240`  |  3 892  | 38 920 000   |
| `ipe270`  |  5 790  | 57 900 000   |
| `ipe300`  |  8 356  | 83 560 000   |
| `ipe330`  | 11 770  |117 700 000   |
| `ipe360`  | 16 270  |162 700 000   |
| `ipe400`  | 23 130  |231 300 000   |
| `ipe450`  | 33 740  |337 400 000   |
| `ipe500`  | 48 200  |482 000 000   |
| `ipe550`  | 67 120  |671 200 000   |
| `ipe600`  | 92 080  |920 800 000   |

### HEB  (sección ancha, alta rigidez)

| Palabra   | I (cm⁴)  | Palabra   | I (cm⁴)  |
|-----------|---------|-----------|---------|
| `heb100`  |    450  | `heb320`  | 30 820  |
| `heb120`  |    864  | `heb340`  | 36 660  |
| `heb140`  |  1 509  | `heb360`  | 43 190  |
| `heb160`  |  2 492  | `heb400`  | 57 680  |
| `heb180`  |  3 831  | `heb450`  | 79 890  |
| `heb200`  |  5 696  | `heb500`  |107 200  |
| `heb220`  |  8 091  | `heb550`  |136 700  |
| `heb240`  | 11 260  | `heb600`  |171 000  |
| `heb260`  | 14 920  |           |         |
| `heb280`  | 19 270  |           |         |
| `heb300`  | 25 170  |           |         |

### IPN  (ala inclinada, DIN)

| Palabra   | I (cm⁴) | Palabra   | I (cm⁴)  |
|-----------|---------|-----------|---------|
| `ipn100`  |   171   | `ipn280`  |  7 590  |
| `ipn120`  |   328   | `ipn300`  |  9 800  |
| `ipn140`  |   573   | `ipn320`  | 12 510  |
| `ipn160`  |   935   | `ipn340`  | 15 700  |
| `ipn180`  |  1 450  | `ipn360`  | 19 610  |
| `ipn200`  |  2 140  | `ipn380`  | 24 010  |
| `ipn220`  |  3 060  | `ipn400`  | 29 210  |
| `ipn240`  |  4 250  | `ipn450`  | 45 850  |
| `ipn260`  |  5 740  | `ipn500`  | 68 740  |

### Tubo rectangular hueco

```forth
\ tubo ( b h t -- )   b=ancho  h=alto  t=espesor  (mm)
100.0 60.0 4.0 tubo   \ calcula I y lo guarda internamente
```

Para solo calcular el valor de I sin guardarlo:
```forth
100.0 60.0 4.0 tubo-I .   \ imprime I en mm⁴
```

---

## Condiciones de apoyo

Cada palabra fija la configuración completa (apoyo + tipo de carga):

| Palabra                  | Apoyo                      | Carga       | k₁        | k₂      |
|--------------------------|----------------------------|-------------|-----------|---------|
| `biapoyada`              | dos apoyos simples         | distribuida | 5/384     | 1/8     |
| `biapoyada-puntual`      | dos apoyos simples         | puntual cen.| 1/48      | 1/4     |
| `biapoyada-puntual-pos`  | dos apoyos simples         | puntual en a| 1/48 (ap.)| 1/4     |
| `empotrada`              | ambos extremos empotrados  | distribuida | 1/384     | 1/12    |
| `empotrada-puntual`      | ambos extremos empotrados  | puntual cen.| 1/192     | 1/8     |
| `empotrada-apoyada`      | un extremo emp., otro libre| distribuida | 1/185     | 3/8     |
| `voladizo`               | un extremo emp., otro libre| distribuida | 1/8       | 1/2     |
| `voladizo-puntual`       | un extremo emp., otro libre| puntual ext.| 1/3       | 1       |

> **Fórmulas aplicadas:**
> - Flecha (distribuida): `f = k₁ × q × L⁴ / (E × I)`
> - Flecha (puntual):     `f = k₁ × P × L³ / (E × I)`
> - Momento (distribuida): `M = k₂ × q × L²`
> - Momento (puntual):     `M = k₂ × P × L`

---

## Setters (fijar valores)

| Palabra        | Descripción                          | Ejemplo            |
|----------------|--------------------------------------|--------------------|
| `L! ( mm )`    | longitud de la viga                  | `5000.0 L!`        |
| `q! ( N/mm )`  | carga distribuida                    | `0.5 q!`           |
| `P! ( N )`     | carga puntual                        | `10000.0 P!`       |
| `a! ( mm )`    | posición de carga puntual            | `2000.0 a!`        |
| `I! ( mm⁴ )`   | inercia (si no se usa perfil)        | `50000000.0 I!`    |
| `W! ( mm³ )`   | módulo resistente                    | `500000.0 W!`      |
| `E! ( N/mm² )` | módulo elástico manual               | `210000.0 E!`      |
| `flim! ( n )`  | límite de flecha = L/n               | `300 flim!`        |

---

## Palabras de cálculo

### Bidireccionales

Estas palabras funcionan en dos modos:

- **Sin argumento** → calculan e imprimen el resultado
- **Con argumento** → fijan el valor para usarlo en cálculo inverso

```forth
flecha      \ calcula la flecha con los parámetros actuales
15.0 flecha \ fija f = 15 mm  (para calcular I o L mínimos)

longitud    \ calcula L máxima para la flecha fijada
inercia     \ calcula I mínimo para la flecha fijada
```

### Unidireccionales

```forth
Mmax        \ momento máximo  [N·mm]
Vmax        \ cortante máximo [N]
reacciones  \ reacciones R1 y R2 en los apoyos [N]
sigma       \ tensión máxima [N/mm²]  (requiere W! definido)
verifica    \ muestra flecha calculada vs límite y veredicto
estado      \ muestra todos los parámetros actuales
ayuda       \ lista de palabras disponibles
```

---

## Conversión de unidades

| De              | A              | Operación          |
|-----------------|----------------|--------------------|
| kN              | N              | × 1000             |
| kN/m            | N/mm           | = mismo número     |
| m               | mm             | × 1000             |
| t/m²            | N/mm²          | × 9.81 / 1000      |
| cm⁴             | mm⁴            | × 10 000           |

> 1 kN/m = 1 N/mm exactamente — la unidad más cómoda para esta librería.

---

## Ejemplos resueltos

### 1. Verificar una viga biapoyada

**Situación:** viga IPE300, acero, L=6 m, q=2 kN/m, límite L/300.

```forth
acero  ipe300  biapoyada
6000.0 L!   2.0 q!   300 flim!
flecha
```
Salida: `f = 5.854 mm  |  limite = 20.0 mm  → OK`

```forth
Mmax        \ 9 000 000 N·mm = 9 kN·m
reacciones  \ R1 = R2 = 6000 N = 6 kN
```

---

### 2. Encontrar el perfil mínimo (cálculo inverso)

**Situación:** misma viga, ¿qué IPE necesito para L/300?

```forth
acero  biapoyada
6000.0 L!   2.0 q!
20.0 flecha    \ fija el límite como f máximo
inercia        \ → I mínimo necesario
```
Resultado: `I = 10 120 000 mm⁴`  → el perfil más próximo por encima es **IPE300** (I=83,560,000 mm⁴).

---

### 3. Longitud máxima de voladizo

**Situación:** tubo 120×80×5, acero, carga puntual en el extremo P=500 N, límite f=10 mm.

```forth
acero
120.0 80.0 5.0 tubo    \ calcula I del tubo
voladizo-puntual
500.0 P!
10.0 flecha            \ fija f = 10 mm
longitud               \ → L máxima
```

---

### 4. Carga puntual en posición arbitraria

```forth
acero  ipe240  biapoyada-puntual-pos
8000.0 L!
3000.0 a!       \ carga a 3 m del apoyo 1
5000.0 P!
flecha
reacciones
Mmax
```

---

### 5. Viga empotrada: comparar con biapoyada

```forth
acero  ipe200
4000.0 L!   1.0 q!

biapoyada   flecha   Mmax
empotrada   flecha   Mmax
```

La empotrada da **flecha 8× menor** y momento menor en el centro (pero hay momentos en los apoyos).

---

## Notas técnicas

- Los valores de I son los de la tabla EN 10365 (2017) para IPE/HEB e EN 10034 para IPN.
- `flim!` actualiza el límite pero **no cambia `_f`** — para el cálculo inverso hay que fijar `_f` explícitamente con `valor flecha`.
- `reacciones` asume viga isostática; para empotrada-empotrada las reacciones son las de la biapoyada equivalente (correcto para verificación de apoyos, no para cálculo de momentos en empotramientos).
- `sigma` requiere el módulo resistente W — no se calcula automáticamente del perfil; hay que proporcionarlo con `W!`.
