#ifdef __MINGW32__
#define __USE_MINGW_ANSI_STDIO 1
#endif
#ifndef _WIN32
#define _POSIX_C_SOURCE 200809L
#endif
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <time.h>
#endif

static double segundos(void) {
#ifdef _WIN32
    LARGE_INTEGER frecuencia, contador;
    QueryPerformanceFrequency(&frecuencia);
    QueryPerformanceCounter(&contador);
    return (double)contador.QuadPart / (double)frecuencia.QuadPart;
#else
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
#endif
}

static int dimension(const char *texto, int *valor) {
    char *fin;
    errno = 0;
    long n = strtol(texto, &fin, 10);
    if (errno || fin == texto || *fin != '\0' || n < 3 || n > INT_MAX)
        return 0;
    *valor = (int)n;
    return 1;
}

/* Generador fijo: mismas dimensiones producen exactamente la misma imagen. */
static void generar_imagen(unsigned char *imagen, size_t bytes) {
    uint32_t estado = 12345;
    for (size_t i = 0; i < bytes; ++i) {
        estado = estado * UINT32_C(1664525) + UINT32_C(1013904223);
        imagen[i] = (unsigned char)(estado >> 24);
    }
}

static void blur(const unsigned char *original, unsigned char *salida,
                 int ancho, int alto) {
    size_t bytes = (size_t)ancho * (size_t)alto * 3;
    /* Copiar primero conserva los bordes, que no tienen ocho vecinos. */
    memcpy(salida, original, bytes);

    for (int y = 1; y < alto - 1; ++y) {
        for (int x = 1; x < ancho - 1; ++x) {
            for (int canal = 0; canal < 3; ++canal) {
                unsigned int suma = 0; /* Maximo: 9 * 255 = 2295. */
                for (int dy = -1; dy <= 1; ++dy) {
                    for (int dx = -1; dx <= 1; ++dx) {
                        size_t vecino = ((size_t)(y + dy) * (size_t)ancho
                                         + (size_t)(x + dx)) * 3;
                        suma += original[vecino + (size_t)canal];
                    }
                }
                size_t indice = ((size_t)y * (size_t)ancho + (size_t)x) * 3;
                /* Division entera: el promedio se trunca hacia abajo. */
                salida[indice + (size_t)canal] = (unsigned char)(suma / 9);
            }
        }
    }
}

static int guardar_ppm(const char *ruta, const unsigned char *imagen,
                       int ancho, int alto, size_t bytes) {
    FILE *archivo = fopen(ruta, "wb");
    if (!archivo) return 0;
    int ok = fprintf(archivo, "P6\n%d %d\n255\n", ancho, alto) > 0;
    if (ok) ok = fwrite(imagen, 1, bytes, archivo) == bytes;
    if (fclose(archivo) != 0) ok = 0;
    return ok;
}

int main(int argc, char *argv[]) {
    int ancho = 7680, alto = 4320;
    if ((argc != 1 && argc != 3 && argc != 4) ||
        (argc >= 3 && (!dimension(argv[1], &ancho) ||
                       !dimension(argv[2], &alto)))) {
        fprintf(stderr, "Uso: %s [ancho alto [salida.ppm]]\n"
                        "Las dimensiones deben ser enteros >= 3.\n", argv[0]);
        return EXIT_FAILURE;
    }
    if ((size_t)ancho > SIZE_MAX / 3 / (size_t)alto) {
        fprintf(stderr, "Dimensiones demasiado grandes.\n");
        return EXIT_FAILURE;
    }
    size_t bytes = (size_t)ancho * (size_t)alto * 3;
    unsigned char *original = malloc(bytes);
    unsigned char *salida = malloc(bytes);
    if (!original || !salida) {
        fprintf(stderr, "No hay memoria suficiente para las dos imagenes.\n");
        free(original);
        free(salida);
        return EXIT_FAILURE;
    }

    generar_imagen(original, bytes);
    double inicio = segundos();
    blur(original, salida, ancho, alto);
    double tiempo = segundos() - inicio;

    /* Consumir el resultado tambien cuando no se guarda una imagen. */
    uint64_t checksum = 0;
    for (size_t i = 0; i < bytes; ++i) checksum += salida[i];
    printf("Imagen: %d x %d, RGB\n", ancho, alto);
    printf("Tiempo secuencial: %.6f segundos\n", tiempo);
    printf("Checksum: %llu\n", (unsigned long long)checksum);

    int resultado = EXIT_SUCCESS;
    if (argc == 4 && !guardar_ppm(argv[3], salida, ancho, alto, bytes)) {
        fprintf(stderr, "No se pudo guardar la imagen PPM.\n");
        resultado = EXIT_FAILURE;
    }
    free(original);
    free(salida);
    return resultado;
}
