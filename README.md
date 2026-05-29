# DermalAI: Sistema de Diagnóstico Dermatológico Inteligente y MLOps Pipeline

¡Bienvenido al proyecto de Primera Unidad de **Aprendizaje de Máquina**!
Este proyecto integra un clasificador de enfermedades de la piel de **22 clases** usando la arquitectura de aprendizaje profundo **DenseNet121** optimizada y exportada en formato **TensorFlow Lite (TFLite)**, dentro de un ciclo de vida de desarrollo de software formal con mantenimiento (deriva de datos) e integración continua (CI/CD) automatizada.

---

## 🚀 Cómo Iniciar la Aplicación (Guía Rápida)

### Paso 1: Instalar Dependencias
Abre tu consola de comandos (PowerShell o CMD) en este directorio y ejecuta:
```bash
pip install Flask tensorflow pillow numpy pandas
```

### Paso 2: Ejecutar las Pruebas Unitarias de Calidad
Asegúrate de que todo funcione correctamente antes de encender el servidor ejecutando:
```bash
python -m unittest test_app.py
```
*(Deberás ver que se ejecutan 4 pruebas y retorna `OK` de forma exitosa).*

### Paso 3: Iniciar el Servidor Web
Lanza la aplicación Flask corriendo en tu terminal:
```bash
python app.py
```

### Paso 4: Abrir el Dashboard en tu Navegador
Una vez encendido, abre tu navegador web e ingresa a:
```text
http://localhost:5000
```
¡Listo! Verás el panel de control interactivo de nivel premium **DermalAI** en modo oscuro, listo para tus demostraciones clínicas, simulación de deriva de datos, reentrenamientos en tiempo real y flujos CI/CD.

---

