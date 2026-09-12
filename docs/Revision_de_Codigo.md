# Revisión de Código Cruzada

## Integrante 2 revisando `secuencial/blur_secuencial.c` (de Integrante 1)

- **Manejo de bordes**: correcto. Se copian los píxeles de borde con
  `memcpy` antes de calcular el blur, y el ciclo principal recorre
  `y` en `[1, alto-2]` y `x` en `[1, ancho-2]`, evitando accesos fuera de
  rango al leer los 8 vecinos.
- **Aritmética de índices**: usa `size_t` para los cálculos de offsets
  (`(size_t)y * (size_t)ancho + ...`), lo que evita overflow de `int` en
  imágenes grandes (8K tiene más de 33 millones de píxeles).
- **Validación de entrada**: `dimension()` rechaza correctamente valores no
  numéricos, negativos, menores a 3 y overflow de `long`. La verificación
  `(size_t)ancho > SIZE_MAX / 3 / (size_t)alto` antes de reservar memoria
  también previene overflow al calcular `bytes`.
- **Reproducibilidad**: el generador de imagen (`generar_imagen`) usa una
  semilla fija, por lo que el checksum es reproducible entre corridas y
  entre la versión secuencial y la paralela — esto es lo que permitió
  validar que `blur_paralelo.c` produce exactamente el mismo checksum que
  `blur_secuencial.c` con cualquier número de hilos.
- **Portabilidad**: el manejo de tiempo (`segundos()`) separa correctamente
  la ruta de Windows (`QueryPerformanceCounter`) de la de Linux/POSIX
  (`clock_gettime`), y las macros al inicio del archivo evitan problemas de
  compilación en MinGW.
- **Sugerencia (no crítica)**: los tres ciclos anidados
  (`canal` → `dy` → `dx`) podrían reordenarse a `dy` → `dx` → `canal` para
  mejorar la localidad de acceso a memoria (leer los 9 vecinos por completo
  antes de cambiar de canal), pero con `-O2` el compilador ya vectoriza bien
  este patrón y no se observó una diferencia relevante en las pruebas, así
  que no se justifica el cambio.

**Conclusión**: el código secuencial es correcto, robusto ante entradas
inválidas y ya estaba escrito de una forma que facilitó la paralelización
(bordes separados del cálculo principal, sin estado global, sin efectos
colaterales entre iteraciones). Se aprueba sin cambios obligatorios.
