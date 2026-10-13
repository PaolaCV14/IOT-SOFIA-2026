
from pathlib import Path
from stl import mesh
import numpy as np

# Carpeta donde están las cuatro mallas originales
CARPETA = Path("webots/protos/meshes")

archivos = [
    "BASE.stl",
    "EJE X.stl",
    "EJE Y.stl",
    "hexagono.stl",
]

print("\nCOMPROBACIÓN DE MALLAS STL DE SOFIA")
print("-" * 75)

for nombre in archivos:
    ruta = CARPETA / nombre

    if not ruta.exists():
        print(f"\nNo se encontró: {ruta}")
        continue

    modelo = mesh.Mesh.from_file(str(ruta))
    vertices = modelo.vectors.reshape(-1, 3)

    minimo = vertices.min(axis=0)
    maximo = vertices.max(axis=0)
    dimensiones = maximo - minimo

    print(f"\nArchivo: {nombre}")
    print(f"Triángulos: {len(modelo.vectors)}")
    print("Mínimo (x, y, z):",
          np.round(minimo, 6))
    print("Máximo (x, y, z):",
          np.round(maximo, 6))
    print("Dimensiones (x, y, z):",
          np.round(dimensiones, 6))

print("\nFin de la comprobación.")
