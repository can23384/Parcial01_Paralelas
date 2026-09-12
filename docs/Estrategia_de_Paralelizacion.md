# Estrategia de Paralelización

**Problema:** Problema 5 — Filtro de Desenfoque de Imagen (Blur)
**Responsable de esta sección:** Integrante 2

## 1. Directivas de OpenMP utilizadas

El programa paralelo (`paralelo/blur_paralelo.c`) parte exactamente del mismo
algoritmo que la versión secuencial (`secuencial/blur_secuencial.c`): para
cada píxel que no está en el borde, se promedian los 3 canales (R, G, B) del
píxel y de sus 8 vecinos inmediatos (ventana de 3×3), y el resultado se
trunca hacia abajo (división entera entre 9).

Se utilizó una sola directiva:

```c
#pragma omp parallel for schedule(static) default(none) \
    shared(original, salida, ancho, alto)
for (int y = 1; y < alto - 1; ++y) {
    ...
}
```

- **`parallel for`**: reparte las iteraciones del ciclo externo (el recorrido
  por filas, variable `y`) entre los hilos disponibles. Se eligió paralelizar
  el ciclo de filas y no el de columnas ni el de canales porque es el que
  tiene más iteraciones (miles en una imagen 8K) y porque cada fila es
  completamente independiente de las demás una vez que se tiene la copia de
  `original` — así el overhead de crear la región paralela se paga una sola
  vez para todo el trabajo, no por cada fila o por cada canal.

- **`schedule(static)`**: el costo de calcular cualquier píxel es siempre el
  mismo (siempre se leen y promedian exactamente 9 vecinos, no hay ramas que
  hagan que unas filas tarden más que otras). Como la carga de trabajo es
  perfectamente uniforme, dividir el rango de filas en bloques contiguos de
  tamaño fijo entre los hilos (lo que hace `static`) ya reparte el trabajo de
  forma equitativa, y evita el overhead de sincronización que tendría
  `dynamic` o `guided` al estar pidiendo constantemente nuevas iteraciones.
  `dynamic` tendría sentido si, por ejemplo, el filtro fuera adaptativo
  (más cómputo en zonas con bordes/alto contraste), pero no es el caso aquí.

- **`default(none)` + `shared(...)`**: se declara explícitamente qué
  variables se comparten entre hilos (`original`, `salida`, `ancho`, `alto`).
  Esto obliga al compilador a rechazar el código si alguna variable queda sin
  clasificar, evitando el error común de compartir por accidente una
  variable que debía ser privada.

## 2. Cómo se evitan las condiciones de carrera (race conditions)

No se necesitó ningún `critical`, `atomic` ni `reduction` porque el problema
se presta a un reparto sin dependencias entre hilos:

- **Lecturas**: todos los hilos únicamente *leen* del arreglo `original`.
  Ese arreglo nunca se modifica durante el cálculo del blur, así que no
  importa que varios hilos lo lean al mismo tiempo (no hay escritura
  concurrente sobre él).
- **Escrituras**: cada hilo escribe únicamente en las filas de `salida` que
  le tocaron según `schedule(static)`. Como el reparto es por filas
  completas y ninguna fila se le asigna a más de un hilo, dos hilos nunca
  escriben en la misma posición de memoria al mismo tiempo.
- El único dato compartido que se *lee y escribe* fuera del ciclo paralelo
  (el `memcpy` inicial que copia los bordes) se ejecuta **antes** de entrar
  a la región paralela, en la parte secuencial de la función, así que no
  compite con las escrituras de los hilos.
- Cada hilo usa sus propias variables locales (`x`, `canal`, `suma`, `dy`,
  `dx`, `vecino`, `indice`) declaradas dentro del cuerpo del ciclo `for`, por
  lo que OpenMP las trata automáticamente como privadas a cada hilo/iteración
  y no hay posibilidad de que un hilo pise el acumulador `suma` de otro.

En resumen: se logró un paralelismo "embarazosamente paralelo" (*embarrassingly
parallel*) por diseño del problema — el resultado final no depende del orden
en que los hilos terminen sus filas, así que no hace falta ninguna primitiva
de sincronización adicional más allá de la barrera implícita al final del
`parallel for` (que garantiza que todos los hilos terminaron antes de medir
el tiempo y calcular el checksum).

## 3. Cómo se maneja el desbalance de carga

Como se explicó en el punto de `schedule(static)`, en este problema no existe
desbalance de carga entre filas: procesar la fila 1 cuesta exactamente lo
mismo que procesar la fila 4000, porque siempre son las mismas operaciones
aritméticas sobre 9 vecinos por canal. Por eso el reparto estático (bloques
de filas contiguas, uno por hilo) es suficiente para lograr que todos los
hilos terminen aproximadamente al mismo tiempo, sin necesidad de scheduling
dinámico ni de dividir el trabajo en chunks más pequeños.

Donde sí puede aparecer un ligero desbalance es en los extremos: si el número
de filas útiles (`alto - 2`) no es múltiplo exacto del número de hilos, uno o
dos hilos reciben una fila más que el resto. Con imágenes de miles de filas
(por ejemplo, 4318 filas útiles en 8K) ese desbalance de ±1 fila es
insignificante frente al total de trabajo por hilo.

## 4. Manejo de los bordes

Los píxeles de la primera/última fila y primera/última columna no tienen 8
vecinos completos, así que —igual que en la versión secuencial— se copian
directamente de `original` a `salida` mediante `memcpy` antes de la región
paralela, y el ciclo paralelo solo recorre `y` desde `1` hasta `alto - 2` y
`x` desde `1` hasta `ancho - 2`. Esto evita accesos fuera de los límites del
arreglo y mantiene el mismo comportamiento que el programa secuencial del
compañero (mismo checksum de salida cuando se corre con el mismo número de
hilos que compilaciones secuenciales, verificado durante la revisión de
código).
