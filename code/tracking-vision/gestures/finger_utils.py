# ==============================================================
# HELPERS GEOMÉTRICOS Y ANATÓMICOS PARA GESTOS
# ==============================================================

def distancia_3d(p1, p2):
    """Distancia euclidiana 3D entre dos landmarks de MediaPipe."""
    return ((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2) ** 0.5


def dedo_extendido(mano, punta, pip, mcp):
    """
    Un dedo está extendido si su punta está significativamente más lejos 
    de la muñeca que su articulación media (PIP). Invariante a la rotación.
    """
    d_punta = distancia_3d(mano[punta], mano[0])
    d_pip = distancia_3d(mano[pip], mano[0])
    return d_punta > (d_pip * 1.15)


def dedo_doblado(mano, punta, pip, mcp):
    """
    Un dedo está doblado si su punta está más cerca de la muñeca que el PIP 
    o muy cerca de los nudillos (puño).
    """
    d_punta = distancia_3d(mano[punta], mano[0])
    d_pip = distancia_3d(mano[pip], mano[0])
    return d_punta <= (d_pip * 1.05)


def es_mano_abierta(mano):
    """Verifica si los dedos están extendidos (mano abierta)."""
    # 8: Índice, 12: Medio, 16: Anular, 20: Meñique
    indices = [(8, 6, 5), (12, 10, 9), (16, 14, 13), (20, 18, 17)]
    cuatro = all(dedo_extendido(mano, punta, pip, mcp) for punta, pip, mcp in indices)
    pulgar = distancia_3d(mano[4], mano[0]) > distancia_3d(mano[2], mano[0]) * 1.2
    return cuatro and pulgar


def es_puno(mano):
    """Verifica si los 4 dedos están doblados hacia adentro formando un puño."""
    indices = [(8, 6, 5), (12, 10, 9), (16, 14, 13), (20, 18, 17)]
    cuatro_doblados = all(dedo_doblado(mano, punta, pip, mcp) for punta, pip, mcp in indices)
    
    # En un puño, las puntas de los dedos están recogidas hacia la base
    escala = distancia_3d(mano[0], mano[9])
    if escala < 0.01:
        return False
    compacto = all(distancia_3d(mano[t], mano[0]) < (escala * 1.6) for t in [8, 12, 16, 20])
    return cuatro_doblados and compacto
