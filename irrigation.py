import pandas as pd

def irrigation_advice(crop, rainfall):

    df = pd.read_csv("irrigation_dataset.csv")

    result = df[
        (df["Crop"] == crop) &
        (df["Rainfall_Min"] <= rainfall) &
        (df["Rainfall_Max"] >= rainfall)
    ]

    if not result.empty:
        return result.iloc[0]["Advice"]

    return "No Irrigation Advice Available"
