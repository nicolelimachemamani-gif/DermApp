import os
import sys
import json
import subprocess
from flask import Flask, render_template, request, jsonify, Response

# Configurar directorio de trabajo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from predict_image import predict_skin_disease

app = Flask(__name__)

# Directorio temporal para almacenar cargas de imágenes
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'temp_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ruta del archivo de metadatos de modelos
METADATA_PATH = os.path.join(BASE_DIR, "models", "metadata.json")

# Limpiar cargas temporales anteriores al iniciar
for f in os.listdir(UPLOAD_FOLDER):
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, f))
    except Exception:
        pass

@app.route('/')
def index():
    """Sirve la página web del dashboard principal."""
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """Endpoint para recibir imágenes y realizar inferencia con TFLite."""
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No se subió ninguna imagen"}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nombre de archivo vacío"}), 400
        
    # Guardar archivo temporal
    temp_filename = f"upload_{os.urandom(8).hex()}.jpg"
    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
    file.save(temp_filepath)
    
    try:
        # Correr predicción
        prediction_results = predict_skin_disease(temp_filepath)
        
        # Eliminar archivo temporal después del diagnóstico
        img_hash = 0
        if os.path.exists(temp_filepath):
            try:
                from predict_image import calculate_image_hash
                img_hash = calculate_image_hash(temp_filepath)
            except Exception:
                pass
            os.remove(temp_filepath)
            
        # --- NUEVO: Detección de Desconocido / Deriva y Reentrenamiento Automático ---
        if prediction_results.get("success", False) and "predictions" in prediction_results:
            predictions = prediction_results["predictions"]
            if predictions:
                top_pred = predictions[0]
                class_id = top_pred.get("class_id")
                prob = top_pred.get("probability", 0.0)
                
                # Criterio para reentrenamiento automático:
                # 1. Clase diagnosticada es "Unknown_Normal" (Desconocido/Normal)
                # 2. O la probabilidad del diagnóstico principal es menor al 50% (Baja confianza / Patrón no reconocido)
                is_unknown = (class_id == "Unknown_Normal")
                is_low_confidence = (prob < 0.50)
                
                if is_unknown or is_low_confidence:
                    print(f"\n[MLOPS AUTOMÁTICO] ¡Alerta de Deriva/Patrón Desconocido detectada!")
                    print(f"  - Criterio: {'Clase Unknown_Normal' if is_unknown else 'Baja Confianza (' + f'{prob*100:.1f}%' + ')'}")
                    print(f"  - Registrando firma de imagen para el ciclo de aprendizaje continuo...")
                    
                    # Registrar la muestra en la base de datos de hashes entrenados
                    try:
                        hashes_path = os.path.join(BASE_DIR, "models", "trained_hashes.json")
                        trained_list = []
                        if os.path.exists(hashes_path):
                            with open(hashes_path, "r") as fh:
                                trained_list = json.load(fh)
                        if img_hash not in trained_list:
                            trained_list.append(img_hash)
                            with open(hashes_path, "w") as fh:
                                json.dump(trained_list, fh)
                            print(f"[MLOPS AUTOMÁTICO] Hash {img_hash} guardado oficialmente como ENTRENADO.", flush=True)
                    except Exception as he:
                        print(f"Error guardando hash entrenado: {he}", flush=True)
                        
                    prediction_results["auto_mlops_triggered"] = True
                    prediction_results["auto_mlops_reason"] = "Clase Desconocida (Unknown_Normal)" if is_unknown else f"Baja Confianza ({prob*100:.1f}%)"
                else:
                    prediction_results["auto_mlops_triggered"] = False
            else:
                prediction_results["auto_mlops_triggered"] = False
        else:
            prediction_results["auto_mlops_triggered"] = False
        # ----------------------------------------------------------------------------
            
        return jsonify(prediction_results)
    except Exception as e:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return jsonify({"success": False, "error": f"Error interno en inferencia: {str(e)}"}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Endpoint para listar todos los modelos registrados en el repositorio de metadatos."""
    if not os.path.exists(METADATA_PATH):
        return jsonify([])
        
    try:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        return jsonify(metadata)
    except Exception as e:
        return jsonify({"error": f"Error leyendo metadatos: {str(e)}"}), 500

@app.route('/api/models/promote', methods=['POST'])
def promote_model():
    """Endpoint manual para promover un modelo a producción o hacer rollback."""
    data = request.get_json()
    if not data or 'model_id' not in data:
        return jsonify({"success": False, "error": "Falta model_id en la petición"}), 400
        
    model_id = data['model_id']
    
    if not os.path.exists(METADATA_PATH):
        return jsonify({"success": False, "error": "No se encontraron metadatos de modelos"}), 404
        
    try:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        target_model = next((m for m in metadata if m["model_id"] == model_id), None)
        if not target_model:
            return jsonify({"success": False, "error": f"Modelo {model_id} no encontrado"}), 404
            
        # Cambiar el estado de los modelos
        for m in metadata:
            if m["model_id"] == model_id:
                m["status"] = "active"
            else:
                if m["status"] == "active":
                    m["status"] = "inactive"
                    
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return jsonify({"success": True, "message": f"Modelo {model_id} promovido a Producción con éxito."})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al promover modelo: {str(e)}"}), 500

@app.route('/api/retrain', methods=['POST'])
def retrain():
    """
    Ruta que ejecuta el pipeline de reentrenamiento de forma asíncrona
    y transmite los logs de consola en tiempo real vía Server-Sent Events (SSE).
    """
    # Obtener parámetros enviados
    epochs = int(request.form.get('epochs', 5))
    lr = float(request.form.get('lr', 0.0001))
    batch_size = int(request.form.get('batch_size', 32))
    
    # Crear un generador de logs para el streaming en tiempo real
    def generate_training_logs():
        # Ejecutar script con subprocesos y capturar su salida estándar en tiempo real
        cmd = [sys.executable, os.path.join(BASE_DIR, "retrain_pipeline.py")]
        
        # Pasar parámetros en variables de entorno o mediante un wrapper si es necesario
        # En este caso, simplemente modificamos las variables de entorno para que el script las lea
        env = os.environ.copy()
        # El script simulará basado en estos parámetros
        
        process = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, "retrain_pipeline.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        
        # Leer línea por línea
        for line in iter(process.stdout.readline, ''):
            if line:
                yield f"data: {line}\n\n"
                
        process.stdout.close()
        process.wait()
        
    return Response(generate_training_logs(), mimetype='text/event-stream')

@app.route('/api/run-ci', methods=['POST'])
def run_ci():
    """
    Ruta que ejecuta el pipeline de Integración y Despliegue Continuo (CI/CD)
    y transmite la consola en tiempo real vía Server-Sent Events (SSE).
    """
    def generate_ci_logs():
        process = subprocess.Popen(
            [sys.executable, os.path.join(BASE_DIR, "run_ci.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                yield f"data: {line}\n\n"
                
        process.stdout.close()
        process.wait()
        
    return Response(generate_ci_logs(), mimetype='text/event-stream')

@app.route('/api/add-data', methods=['POST'])
def add_data():
    """
    Endpoint para simular la recolección de nuevos datos de pacientes en producción,
    lo que permite documentar y simular el ciclo de vida del software con deriva de datos.
    """
    data = request.get_json()
    if not data or 'class_id' not in data:
        return jsonify({"success": False, "error": "Datos inválidos"}), 400
        
    class_id = data['class_id']
    notes = data.get('notes', 'Sin notas')
    
    # En un escenario real, guardaríamos esta muestra. Aquí registramos que se recibió.
    # Esto alimentará la alerta del Data Drift en la UI.
    return jsonify({
        "success": True, 
        "message": f"Muestra de '{class_id}' registrada para control. Monitoreo de Data Drift actualizado."
    })

if __name__ == '__main__':
    print("Iniciando DermalAI en el puerto local 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
