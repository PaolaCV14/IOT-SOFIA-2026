# ==============================================================
# FUNCIONES AUXILIARES PARA MANOS Y DEDOS
# Aquí calculamos distancias y revisamos si un dedo está estirado
# o doblado para saber qué gesto está haciendo el usuario.
# ==============================================================

def distancia_3d(p1, p2):
    """Calcula la distancia real en 3D entre dos puntos (x, y, z)."""
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2) ** 0.5


def dedo_extendido(mano, punta, pip, mcp):
    """
    Un dedo está estirado si la punta está más lejos de la muñeca
    que su nudillo del medio (articulación PIP).
    """
    d_punta = distancia_3d(mano[punta], mano[0])
    d_pip = distancia_3d(mano[pip], mano[0])
    return d_punta > (d_pip * 1.15)


def dedo_doblado(mano, punta, pip, mcp):
    """
    Un dedo está doblado si la punta se acerca a la muñeca o a la palma.
    """
    d_punta = distancia_3d(mano[punta], mano[0])
    d_pip = distancia_3d(mano[pip], mano[0])
    return d_punta <= (d_pip * 1.05)


def es_mano_abierta(mano):
    """Revisa si los 5 dedos están estirados (mano abierta)."""
    # 8: Índice, 12: Medio, 16: Anular, 20: Meñique
    indices = [(8, 6, 5), (12, 10, 9), (16, 14, 13), (20, 18, 17)]
    cuatro_dedos = all(dedo_extendido(mano, punta, pip, mcp) for punta, pip, mcp in indices)
    
    # El pulgar se mide comparando la punta (4) contra la base (2)
    pulgar = distancia_3d(mano[4], mano[0]) > distancia_3d(mano[2], mano[0]) * 1.2
    return cuatro_dedos and pulgar


def es_puno(mano):
    """Revisa si la mano está cerrada en forma de puño."""
    indices = [(8, 6, 5), (12, 10, 9), (16, 14, 13), (20, 18, 17)]
    cuatro_doblados = all(dedo_doblado(mano, punta, pip, mcp) for punta, pip, mcp in indices)
    
    # Además de doblados, checamos que las puntas estén recogidas hacia la base
    tamano_mano = distancia_3d(mano[0], mano[9])
    if tamano_mano < 0.01:
        return False
    compacto = all(distancia_3d(mano[t], mano[0]) < (tamano_mano * 1.6) for t in [8, 12, 16, 20])
    return cuatro_doblados and compacto
