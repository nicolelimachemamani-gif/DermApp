import os
import json
import unittest
import numpy as np
from PIL import Image

# Forzar a usar el directorio base correcto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from predict_image import preprocess_image, ORDERED_CLASSES, predict_skin_disease

class TestDermalAI(unittest.TestCase):
    
    def setUp(self):
        """Prepara el entorno de pruebas creando una imagen temporal."""
        self.test_img_path = os.path.join(BASE_DIR, "temp_test_image.jpg")
        
        # Crear una imagen RGB aleatoria de prueba y guardarla
        img_array = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img.save(self.test_img_path)

    def tearDown(self):
        """Limpia el archivo de imagen temporal."""
        if os.path.exists(self.test_img_path):
            os.remove(self.test_img_path)

    def test_ordered_classes(self):
        """Verifica que el sistema tenga registradas las 22 clases requeridas."""
        self.assertEqual(len(ORDERED_CLASSES), 22)
        self.assertIn("Acne", ORDERED_CLASSES)
        self.assertIn("SkinCancer", ORDERED_CLASSES)
        self.assertIn("Unknown_Normal", ORDERED_CLASSES)

    def test_image_preprocessing(self):
        """Prueba que el preprocesador de imagen redimensione y normalice correctamente."""
        processed = preprocess_image(self.test_img_path, target_size=(224, 224))
        
        self.assertIsNotNone(processed)
        # Debe tener la forma del lote: (1, 224, 224, 3)
        self.assertEqual(processed.shape, (1, 224, 224, 3))
        # Debe ser de tipo float32
        self.assertEqual(processed.dtype, np.float32)

    def test_inference_results_format(self):
        """Verifica que el formato de salida de las predicciones sea correcto."""
        res = predict_skin_disease(self.test_img_path)
        
        # Debe ser exitoso
        self.assertTrue(res["success"])
        # Debe contener la lista de predicciones
        self.assertIn("predictions", res)
        # La lista debe tener exactamente 22 predicciones (una por cada clase)
        self.assertEqual(len(res["predictions"]), 22)
        
        # Verificar la estructura del primer resultado (el más confiable)
        top_pred = res["predictions"][0]
        self.assertIn("class_id", top_pred)
        self.assertIn("name_es", top_pred)
        self.assertIn("probability", top_pred)
        self.assertIn("severity", top_pred)
        self.assertIn("recommendations", top_pred)
        
        # La probabilidad máxima debe estar entre 0 y 1
        self.assertTrue(0 <= top_pred["probability"] <= 1.0)
        
        # Las predicciones deben venir ordenadas de mayor a menor probabilidad
        probs = [p["probability"] for p in res["predictions"]]
        self.assertEqual(probs, sorted(probs, reverse=True))

    def test_metadata_existence(self):
        """Prueba la disponibilidad de los metadatos de las clases y del modelo."""
        class_names_path = os.path.join(BASE_DIR, "models", "class_names.json")
        metadata_path = os.path.join(BASE_DIR, "models", "metadata.json")
        
        self.assertTrue(os.path.exists(class_names_path), "Falta el archivo class_names.json")
        self.assertTrue(os.path.exists(metadata_path), "Falta el archivo metadata.json")
        
        # Validar JSONs
        with open(class_names_path, "r", encoding="utf-8") as f:
            classes = json.load(f)
            self.assertEqual(len(classes), 22)
            
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            self.assertTrue(len(meta) >= 1)

if __name__ == "__main__":
    unittest.main()
