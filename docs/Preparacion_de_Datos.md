# Preparación de la Imagen / Datos de Prueba

**Responsable de esta sección:** Integrante 2

## 1. Origen de los datos

En vez de cargar una imagen satelital real desde disco (lo cual añadiría una
dependencia externa —una librería para decodificar JPEG/PNG— que no aporta
nada a la comparación secuencial vs. paralelo), ambos programas
(`blur_secuencial.c` y `blur_paralelo.c`) **generan su propia imagen de
prueba de forma sintética y determinista**, con la función `generar_imagen`:

```c
static void generar_imagen(unsigned char *imagen, size_t bytes) {
    uint32_t estado = 12345;
    for (size_t i = 0; i < bytes; ++i) {
        estado = estado * 1664525u + 1013904223u;
        imagen[i] = (unsigned char)(estado >> 24);
    }
}
```

Esto es un generador congruencial lineal (LCG) con una semilla fija
(`12345`). Es determinista: **para las mismas dimensiones, siempre genera
exactamente los mismos bytes**, tanto en la versión secuencial como en la
paralela. Esto es clave para la validez del experimento, porque permite:

- Comparar el **checksum** de la imagen resultante entre la versión
  secuencial y la paralela para confirmar que ambas producen el mismo
  resultado (correctitud del paralelismo), sin importar cuántos hilos se
  usen.
- Que cualquier integrante del equipo, en cualquier máquina, reproduzca
  exactamente la misma carga de trabajo al medir tiempos.

## 2. Representación en memoria

- La imagen se representa como un **arreglo unidimensional de bytes**
  (`unsigned char *`) de tamaño `ancho * alto * 3`.
- Es un formato **RGB intercalado (interleaved)**: por cada píxel se guardan
  3 bytes consecutivos (`R`, `G`, `B`), uno tras otro, fila por fila (formato
  "row-major"). El píxel `(x, y)` empieza en el índice
  `(y * ancho + x) * 3`.
- Se usa `unsigned char` (0–255) por canal porque es la representación
  estándar de una imagen de 24 bits (8 bits por canal), igual que un archivo
  PPM binario P6 o un mapa de bits sin comprimir. De hecho, el programa puede
  guardar el resultado directamente en ese formato (`guardar_ppm`), sin
  necesitar ninguna librería externa de imágenes.
- Se calcula un **checksum** (suma de todos los bytes de la imagen de
  salida) como forma barata de verificar que el resultado paralelo es
  idéntico al secuencial, y también para forzar al compilador a no eliminar
  el cálculo del blur como código "muerto" si no se guarda archivo de salida.

## 3. Tamaño de la muestra usado en las pruebas

- **Por defecto**, ambos programas usan **7680 × 4320 (8K UHD)**, tal como
  pide el enunciado del Problema 5 ("imagen satelital de 8K"). Esto equivale
  a `7680 * 4320 * 3 = 99 532 800` bytes (~95 MB) por cada arreglo, y se
  necesitan dos arreglos de ese tamaño (`original` y `salida`) al mismo
  tiempo, es decir, ~190 MB de RAM en total.
- Para las corridas de benchmarking (medir 1, 2, 4 y 8 hilos varias veces
  cada uno) se usa un tamaño configurable más pequeño
  (`--ancho` / `--alto` en `docs/benchmark.py`, por defecto **3840 × 2160,
  4K UHD**) para que cada corrida individual tome pocos segundos y se puedan
  repetir varias veces sin que el benchmarking completo tome demasiado
  tiempo. El tamaño 8K completo también se puede usar pasando
  `--ancho 7680 --alto 4320`, y sigue siendo la imagen que se debe usar para
  el reporte final si la máquina de prueba tiene RAM suficiente.
- Las dimensiones son configurables por línea de comandos en ambos programas
  (`./blur_secuencial ancho alto`, `./blur_paralelo ancho alto salida hilos`)
  precisamente para poder correr el mismo experimento con distintos tamaños
  de imagen sin tener que recompilar.

## 4. Por qué esta imagen es representativa del problema real

El Problema 5 dice que hay que promediar cada píxel con sus 8 vecinos
inmediatos. El *contenido* real de la imagen (si es una foto satelital, una
fotografía o ruido aleatorio) no afecta el costo computacional del filtro:
siempre se hacen las mismas operaciones aritméticas por píxel
(9 lecturas + 1 suma + 1 división, por canal). Por eso, para efectos de medir
tiempos de ejecución, speedup y eficiencia, una imagen sintética generada de
forma determinista es equivalente a una imagen satelital real, pero evita
tener que distribuir un archivo de imagen pesado dentro del repositorio y
elimina la dependencia de librerías externas de decodificación de imágenes.
