import joblib
import pandas as pd

model = joblib.load("crop_model.pkl")
encoder = joblib.load("crop_encoder.pkl")

def predict_crop(N, P, K, temperature, humidity, rainfall, ph):

    input_data = pd.DataFrame({
        "N": [N],
        "P": [P],
        "K": [K],
        "Temperature": [temperature],
        "Humidity": [humidity],
        "Rainfall": [rainfall],
        "pH": [ph]
    })

    prediction = model.predict(input_data)

    crop = encoder.inverse_transform(prediction)

    return crop[0]