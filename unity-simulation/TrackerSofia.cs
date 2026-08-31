using UnityEngine;

/// <summary>
/// Sigue un punto objetivo usando las ecuaciones del modelo cinemático
/// inverso (Lab-DST): q2 = asin(ux), q1 = atan2(-uy, uz). Para evitar que
/// el panel "gire como llanta" (roll parásito alrededor del eje de mira),
/// la rotación final se arma con FromToRotation sobre el vector
/// RECONSTRUIDO a partir de q1 y q2 (ec. 16) — igual que el script
/// original, pero pasando explícitamente por las fórmulas.
/// </summary>
public class TrackerSofiaIK : MonoBehaviour
{
    [Header("¿A quién seguimos?")]
    public Transform objetivo;

    [Header("Límite mecánico de los servos (grados)")]
    [Tooltip("Grados máximos que puede inclinarse. Ejemplo: 45")]
    public float limiteGrados = 45f;

    [Header("Modo de operación")]
    public bool detectarPersona = true;

    private Quaternion rotacionCero;

    void Start()
    {
        rotacionCero = transform.rotation;
    }

    void Update()
    {
        if (objetivo == null) return;

        if (!detectarPersona)
        {
            transform.rotation = rotacionCero;
            return;
        }

        // Bloqueo físico del piso (igual que antes)
        if (objetivo.position.y <= transform.position.y)
        {
            transform.rotation = rotacionCero;
            return;
        }

        // 1) Vector o2 -> p, en MUNDO (igual que tu script original)
        Vector3 direccion = objetivo.position - transform.position;
        Vector3 u = direccion.normalized;

        // 2) Mapeo de ejes: el eje "neutral" de la fórmula (z2,3 -> vector base (0,0,1))
        //    corresponde aquí a Vector3.up del mundo, como en tu script original.
        //    Los otros dos ejes de la fórmula (x, y) se mapean a x y z de Unity.
        float ux = u.x;
        float uy = u.z;
        float uz = u.y;

        // 3) ---------- ECUACIONES ----------
        float q2 = Mathf.Asin(Mathf.Clamp(ux, -1f, 1f));   // (19) q2 = asin(ux)
        float q1 = Mathf.Atan2(-uy, uz);                    // (21) q1 = atan2(-uy, uz)
        // ------------------------------------

        // 4) Reconstruir el vector unitario A PARTIR de q1 y q2 usando la
        //    misma fórmula (16): [sin q2, -cos q2 sin q1, cos q1 cos q2]
        float rx = Mathf.Sin(q2);
        float ry = -Mathf.Cos(q2) * Mathf.Sin(q1);
        float rz = Mathf.Cos(q1) * Mathf.Cos(q2);

        // 5) Devolver ese vector reconstruido a coordenadas de Unity
        //    (invirtiendo el mapeo del paso 2)
        Vector3 direccionReconstruida = new Vector3(rx, rz, ry);

        // 6) Rotación SIN roll parásito: rota Vector3.up hacia la dirección
        //    reconstruida (misma técnica robusta que tu script original)
        Quaternion rotacionIdeal = Quaternion.FromToRotation(Vector3.up, direccionReconstruida);

        // 7) Tope mecánico del servo (igual que antes)
        transform.rotation = Quaternion.RotateTowards(rotacionCero, rotacionIdeal, limiteGrados);
    }
}