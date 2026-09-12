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
