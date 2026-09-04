using UnityEngine;

/// <summary>
/// Sigue un punto objetivo usando las ecuaciones del modelo cinemático
/// inverso (Lab-DST): q2 = asin(ux), q1 = atan2(-uy, uz).
/// La dirección del módulo se reconstruye a partir de q1 y q2
/// utilizando la ecuación (16) del modelo SOFIA.
/// </summary>
public class TrackerSofiaIK : MonoBehaviour
{
    [Header("¿A quién seguimos?")]
    public Transform objetivo;

    [Header("Límite mecánico de los servos (grados)")]
    [Tooltip("Límite máximo de cada servo. MG90S: ±90°")]
    public float limiteGrados = 90f;

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

        // Bloqueo físico del piso
        if (objetivo.position.y <= transform.position.y)
        {
            transform.rotation = rotacionCero;
            return;
        }

        // 1) Vector o2 -> p, en MUNDO
        Vector3 direccion = objetivo.position - transform.position;

        // Evitar una dirección de magnitud cero
        if (direccion.sqrMagnitude < 0.0001f)
        {
            transform.rotation = rotacionCero;
            return;
        }

        Vector3 u = direccion.normalized;

        // 2) Mapeo de ejes entre el modelo SOFIA y Unity
        float ux = u.x;
        float uy = u.z;
        float uz = u.y;

        // 3) ECUACIONES DEL MODELO CINEMÁTICO INVERSO
        // q2 = asin(ux)
        // q1 = atan2(-uy, uz)

        float q2 = Mathf.Asin(
            Mathf.Clamp(ux, -1f, 1f)
        );

        float q1 = Mathf.Atan2(
            -uy,
            uz
        );

        // 4) Convertir a grados para aplicar el límite mecánico
        float q1Grados = q1 * Mathf.Rad2Deg;
        float q2Grados = q2 * Mathf.Rad2Deg;

        // 5) CLAMP de los ángulos de los servos
        q1Grados = Mathf.Clamp(
            q1Grados,
            -limiteGrados,
            limiteGrados
        );

        q2Grados = Mathf.Clamp(
            q2Grados,
            -limiteGrados,
            limiteGrados
        );

        // 6) Regresar a radianes para las funciones trigonométricas
        q1 = q1Grados * Mathf.Deg2Rad;
        q2 = q2Grados * Mathf.Deg2Rad;

        // 7) Reconstruir el vector unitario a partir de q1 y q2
        //    r_hat_2,3 =
        //    [ sin(q2),
        //     -cos(q2) sin(q1),
        //      cos(q1) cos(q2) ]

        float rx = Mathf.Sin(q2);
        float ry = -Mathf.Cos(q2) * Mathf.Sin(q1);
        float rz = Mathf.Cos(q1) * Mathf.Cos(q2);

        // 8) Regresar el vector reconstruido a coordenadas de Unity
        Vector3 direccionReconstruida = new Vector3(
            rx,
            rz,
            ry
        );

        // 9) Orientar el módulo hacia la dirección calculada
        Quaternion rotacionIdeal =
            Quaternion.FromToRotation(
                Vector3.up,
                direccionReconstruida
            );

        // 10) Aplicar la orientación
        transform.rotation = rotacionIdeal;
    }
}