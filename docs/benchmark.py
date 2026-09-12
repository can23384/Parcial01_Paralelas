#!/usr/bin/env python3
"""
benchmark.py
------------
Automatiza la medicion pedida en "Resultados y Metricas":
  1. Compila blur_secuencial y blur_paralelo.
  2. Corre el secuencial (baseline) varias veces y promedia.
  3. Corre el paralelo con 1, 2, 4, 8 hilos (y cualquier otro que agregues
     en LISTA_HILOS), varias veces cada uno, y promedia.
  4. Calcula speedup = T_secuencial / T_paralelo(p)
     y eficiencia = speedup / p
  5. Guarda una tabla en docs/resultados/resultados_<integrante>.csv
  6. Genera 3 graficas en docs/graficas/:
       tiempos_<integrante>.png     (tiempo vs. hilos)
       speedup_<integrante>.png     (speedup vs. hilos, con la recta ideal)
       eficiencia_<integrante>.png  (eficiencia vs. hilos)

Cada integrante debe correr este script EN SU PROPIA COMPUTADORA
(el reporte pide explícitamente las mediciones individuales de cada
quien), y usar --nombre para que sus archivos no se sobreescriban con
los del compañero.

Uso:
    python3 benchmark.py --nombre integrante2 --ancho 3840 --alto 2160

Requisitos:
    pip install matplotlib   (si no lo tienes ya instalado)
    Un compilador con soporte OpenMP (gcc/mingw con -fopenmp).
"""

import argparse
import csv
import statistics
import subprocess
import sys
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECUENCIAL_SRC = RAIZ / "secuencial" / "blur_secuencial.c"
PARALELO_SRC = RAIZ / "paralelo" / "blur_paralelo.c"
DOCS = RAIZ / "docs"
RESULTADOS_DIR = DOCS / "resultados"
GRAFICAS_DIR = DOCS / "graficas"

TIEMPO_SEC_RE = re.compile(r"Tiempo secuencial:\s*([\d.]+)\s*segundos")
TIEMPO_PAR_RE = re.compile(r"Tiempo paralelo:\s*([\d.]+)\s*segundos")


def compilar():
    exe_sec = RAIZ / ("blur_secuencial.exe" if sys.platform == "win32" else "blur_secuencial")
    exe_par = RAIZ / ("blur_paralelo.exe" if sys.platform == "win32" else "blur_paralelo")

    print(">> Compilando version secuencial...")
    subprocess.run(
        ["gcc", "-O2", "-std=c11", "-Wall", "-Wextra", "-Wpedantic",
         str(SECUENCIAL_SRC), "-o", str(exe_sec)],
        check=True,
    )

    print(">> Compilando version paralela (OpenMP)...")
    subprocess.run(
        ["gcc", "-O2", "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-fopenmp",
         str(PARALELO_SRC), "-o", str(exe_par)],
        check=True,
    )
    return exe_sec, exe_par


def correr_secuencial(exe_sec, ancho, alto, repeticiones):
    tiempos = []
    for i in range(repeticiones):
        salida = subprocess.run(
            [str(exe_sec), str(ancho), str(alto)],
            check=True, capture_output=True, text=True,
        ).stdout
        m = TIEMPO_SEC_RE.search(salida)
        if not m:
            raise RuntimeError(f"No se pudo leer el tiempo secuencial:\n{salida}")
        t = float(m.group(1))
        tiempos.append(t)
        print(f"   secuencial corrida {i + 1}/{repeticiones}: {t:.6f} s")
    return statistics.median(tiempos)


def correr_paralelo(exe_par, ancho, alto, hilos, repeticiones):
    tiempos = []
    for i in range(repeticiones):
        salida = subprocess.run(
            [str(exe_par), str(ancho), str(alto), "-", str(hilos)],
            check=True, capture_output=True, text=True,
        ).stdout
        m = TIEMPO_PAR_RE.search(salida)
        if not m:
            raise RuntimeError(f"No se pudo leer el tiempo paralelo:\n{salida}")
        t = float(m.group(1))
        tiempos.append(t)
        print(f"   {hilos} hilo(s) corrida {i + 1}/{repeticiones}: {t:.6f} s")
    return statistics.median(tiempos)


def graficar(nombre, hilos_lista, tiempos, speedups, eficiencias, t_seq):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    GRAFICAS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Tiempo vs hilos ---
    plt.figure()
    plt.axhline(t_seq, linestyle="--", label="Secuencial (1 sola corrida base)")
    plt.plot(hilos_lista, tiempos, marker="o", label="Paralelo (OpenMP)")
    plt.xlabel("Numero de hilos")
    plt.ylabel("Tiempo (segundos)")
    plt.title(f"Tiempo de ejecucion vs. hilos ({nombre})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(GRAFICAS_DIR / f"tiempos_{nombre}.png", dpi=150, bbox_inches="tight")
    plt.close()

    # --- Speedup vs hilos ---
    plt.figure()
    plt.plot(hilos_lista, hilos_lista, linestyle="--", label="Speedup ideal (lineal)")
    plt.plot(hilos_lista, speedups, marker="o", label="Speedup medido")
    plt.xlabel("Numero de hilos")
    plt.ylabel("Speedup (T_secuencial / T_paralelo)")
    plt.title(f"Speedup vs. hilos ({nombre})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(GRAFICAS_DIR / f"speedup_{nombre}.png", dpi=150, bbox_inches="tight")
    plt.close()

    # --- Eficiencia vs hilos ---
    plt.figure()
    plt.axhline(1.0, linestyle="--", label="Eficiencia ideal (100%)")
    plt.plot(hilos_lista, eficiencias, marker="o", label="Eficiencia medida")
    plt.xlabel("Numero de hilos")
    plt.ylabel("Eficiencia (speedup / hilos)")
    plt.title(f"Eficiencia vs. hilos ({nombre})")
    plt.ylim(0, 1.2)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(GRAFICAS_DIR / f"eficiencia_{nombre}.png", dpi=150, bbox_inches="tight")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Benchmark secuencial vs. paralelo (blur OpenMP).")
    parser.add_argument("--nombre", required=True,
                         help="Identificador del integrante, ej. integrante1 / integrante2. "
                              "Se usa en los nombres de los archivos de salida.")
    parser.add_argument("--ancho", type=int, default=3840, help="Ancho de la imagen de prueba.")
    parser.add_argument("--alto", type=int, default=2160, help="Alto de la imagen de prueba.")
    parser.add_argument("--hilos", type=int, nargs="+", default=[1, 2, 4, 8],
                         help="Lista de cantidades de hilos a probar. Por defecto: 1 2 4 8.")
    parser.add_argument("--repeticiones", type=int, default=5,
                         help="Cuantas veces correr cada configuracion (se usa la mediana).")
    args = parser.parse_args()

    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

    exe_sec, exe_par = compilar()

    print(f"\n>> Corriendo secuencial ({args.repeticiones} repeticiones)...")
    t_seq = correr_secuencial(exe_sec, args.ancho, args.alto, args.repeticiones)
    print(f"   Tiempo secuencial (mediana): {t_seq:.6f} s\n")

    filas = []
    tiempos, speedups, eficiencias = [], [], []
    for h in args.hilos:
        print(f">> Corriendo paralelo con {h} hilo(s) ({args.repeticiones} repeticiones)...")
        t_par = correr_paralelo(exe_par, args.ancho, args.alto, h, args.repeticiones)
        speedup = t_seq / t_par
        eficiencia = speedup / h
        print(f"   Tiempo paralelo (mediana): {t_par:.6f} s | "
              f"speedup: {speedup:.3f} | eficiencia: {eficiencia:.3f}\n")

        filas.append({
            "hilos": h,
            "tiempo_secuencial_s": f"{t_seq:.6f}",
            "tiempo_paralelo_s": f"{t_par:.6f}",
            "speedup": f"{speedup:.4f}",
            "eficiencia": f"{eficiencia:.4f}",
        })
        tiempos.append(t_par)
        speedups.append(speedup)
        eficiencias.append(eficiencia)

    csv_path = RESULTADOS_DIR / f"resultados_{args.nombre}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hilos", "tiempo_secuencial_s", "tiempo_paralelo_s", "speedup", "eficiencia",
        ])
        writer.writeheader()
        writer.writerows(filas)
    print(f">> Tabla de resultados guardada en: {csv_path}")

    try:
        graficar(args.nombre, args.hilos, tiempos, speedups, eficiencias, t_seq)
        print(f">> Graficas guardadas en: {GRAFICAS_DIR}")
    except ImportError:
        print("!! matplotlib no esta instalado. Instalalo con: pip install matplotlib")
        print("   (la tabla CSV ya se genero correctamente).")


if __name__ == "__main__":
    main()
