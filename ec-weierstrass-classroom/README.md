---
noteId: "994aaf903fc211f1b060eda75de4cd30"
tags: []

---

# Elliptic Curves Classroom Lab

Herramienta didáctica en Python para enseñar:

- suma geométrica de puntos en curvas elípticas de Weierstrass,
- suma y multiplicación escalar sobre campos finitos,
- intercambio de claves ECDH,
- conexión con el uso actual de curvas elípticas en protocolos modernos.

## Requisitos

- Python 3.10+
- `streamlit`
- `plotly`
- `pandas`
- `numpy`

## Ejecución

```bash
streamlit run app.py
```

## Contenido

- `app.py`: interfaz gráfica con Streamlit.
- `ecc_core.py`: operaciones matemáticas de curvas de Weierstrass y demo de P-256.
- `requirements.txt`: dependencias mínimas.
- `run.bat` y `run.sh`: scripts rápidos de arranque.

## Uso recomendado en clase

1. Mostrar la suma geométrica en la pestaña 1.
2. Pasar a la curva sobre `F_p` en la pestaña 2.
3. Construir ECDH con secretos pequeños en la pestaña 3.
4. Cerrar con la pestaña 4 para explicar cómo se hace hoy en TLS 1.3 y con curvas estándar.
