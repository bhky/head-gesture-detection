"""
Inference utilities.
"""
import os
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np
from tensorflow.keras.models import Model

from hgd._download import get_default_weights_path, download_weights_to
from hgd.config import Config
from hgd.data import NDFloat32Array, preprocess
from hgd.model import make_model
from hgd.video import video_to_landmarks


def load_pretrained_model(weights_path: str = get_default_weights_path()) -> Model:
    model = make_model()
    if not os.path.isfile(weights_path):
        download_weights_to(weights_path)
    model.load_weights(weights_path)
    return model


def postprocess(
        prediction: Sequence[float],
        is_moving_threshold: float = 0.5,
        class_threshold: float = 0.9
) -> Dict[str, Any]:
    if prediction[0] < is_moving_threshold:
        label = Config.stationary_label
    else:
        class_probs = prediction[1:]
        if np.max(class_probs) < class_threshold:
            label = Config.undefined_class_label
        else:
            label = Config.class_labels[int(np.argmax(class_probs))]
    return {
        "gesture": label,
        "is_moving_probability": prediction[0],
        "gesture_probabilities": prediction[1:]
    }


def predict_video(
        video_path: Optional[str] = None,  # None will start a webcam.
        model: Optional[Model] = None,
        max_num_frames: int = Config.seq_length,  # For the pre-trained model.
        padding: bool = True,
        preprocess_fn: Callable[[List[List[float]]], NDFloat32Array] = preprocess
) -> Dict[str, Any]:
    if model is None:
        model = load_pretrained_model()
    landmarks = video_to_landmarks(video_path, max_num_frames, padding)
    prediction: Sequence[float] = model.predict(
        np.expand_dims(preprocess_fn(landmarks), axis=0)
    )[0].tolist()
    return postprocess(prediction)


# if __name__ == "__main__":
#     print(predict_video(model=load_pretrained_model(f"../training/{Config.weights_filename}")))
