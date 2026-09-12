# Consultora HPC

Proyecto 1

## Integrantes

- Eliazar José Pablo Canastuj Matías, 23384
- Nelson Escalant, 22046


## Compilar y ejecutar


### SECUENCIAL:
Desde esta carpeta, con GCC:

```sh
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic blur_secuencial.c -o blur_secuencial
```

En Linux:

```sh
./blur_secuencial
./blur_secuencial 1920 1080 salida.ppm
```

En PowerShell con MinGW:

```powershell
.\blur_secuencial.exe
.\blur_secuencial.exe 1920 1080 salida.ppm
```

Sin argumentos se usa 7680 × 4320 (8K UHD). Las dimensiones mínimas son 3 × 3. El tercer argumento es opcional: guarda el resultado en formato PPM binario P6. No es un archivo PNG ni JPG.

### PARALELO (OpenMP):

Desde esta carpeta, con GCC:

```sh
gcc -O2 -std=c11 -Wall -Wextra -Wpedantic -fopenmp paralelo/blur_paralelo.c -o blur_paralelo
```

En Linux:

```sh
./blur_paralelo
./blur_paralelo 1920 1080 salida.ppm
./blur_paralelo 1920 1080 salida.ppm 4   # forzar 4 hilos
./blur_paralelo 1920 1080 -      8       # sin guardar imagen, 8 hilos
```

En PowerShell con MinGW:

```powershell
.\blur_paralelo.exe
.\blur_paralelo.exe 1920 1080 salida.ppm 4
```

Mismos valores por defecto y las mismas dimensiones mínimas que la versión
secuencial. El cuarto argumento (opcional) fija el número de hilos OpenMP; si
se omite, se usa `OMP_NUM_THREADS` o el máximo de hilos disponible en la
máquina. Usar `-` como nombre de salida corre el filtro sin escribir ningún
archivo PPM (útil para benchmarking).

## Estructura del repositorio

```
/secuencial   -> Algoritmo base (blur_secuencial.c)
/paralelo     -> Solución optimizada con OpenMP (blur_paralelo.c)
/docs         -> Reportes, gráficas y análisis de datos
    Estrategia_de_Paralelizacion.md
    Preparacion_de_Datos.md
    benchmark.py           (automatiza las mediciones de speedup/eficiencia)
    /resultados            (CSV con tiempos, speedup y eficiencia por integrante)
    /graficas               (PNG: tiempo/speedup/eficiencia vs. hilos)
```

## Medir speedup y eficiencia (cada integrante, en su propia máquina)

```sh
pip install matplotlib
python3 docs/benchmark.py --nombre integrante2 --ancho 3840 --alto 2160
```

Esto compila ambos programas, corre el secuencial y el paralelo con 1, 2, 4
y 8 hilos (varias repeticiones cada uno), y guarda una tabla CSV y tres
gráficas (tiempo, speedup y eficiencia vs. número de hilos) en `docs/`. Cada
integrante debe correrlo con su propio `--nombre` para no sobreescribir los
resultados del compañero, y adjuntar screenshot/video de sus corridas según
pide el enunciado.
