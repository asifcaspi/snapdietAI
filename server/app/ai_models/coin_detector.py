import os
import numpy as np
import tensorflow as tf
from app.constants.coins import coins_names

coin_model_path = os.path.join(os.path.dirname(__file__), "../../coin_detection.keras")
if not os.path.exists(coin_model_path):
    url = "1_Nb8SS0mUhQc-ZSjbTHxCsqpjOP4QB8r"

    os.system(f"gdown {url} -O {coin_model_path}")


class CoinDetector:
    def __init__(self):
        self.coin_detection_model = tf.keras.models.load_model(coin_model_path)

    def image_preprocess(self, img):
        image = img.copy()
        image = tf.image.resize(image, (224, 224))
        image = np.array(image)
        image = tf.keras.applications.resnet50.preprocess_input(image)
        return tf.expand_dims(image, 0)

    def coin_detection(self, image):
        image = self.image_preprocess(image)
        preds = self.coin_detection_model.predict(image)
        idx = np.argmax(preds[0])
        conf = preds[0][idx]
        print(
            f"Coin detected class: {idx} → “{coins_names[idx]}”  (confidence: {conf:.3f})"
        )

        return coins_names[idx], conf
