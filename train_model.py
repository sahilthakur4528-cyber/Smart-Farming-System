import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

# Load Dataset
data = pd.read_csv("crop_dataset_100_records1.csv")

print("Dataset Loaded Successfully!\n")

# Features
X = data[['N','P','K','Temperature','Humidity','Rainfall','pH']]

# Target
y = data['Crop']

# Encode Crop Names
encoder = LabelEncoder()
y = encoder.fit_transform(y)

# Split Dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

# Create Model
model = DecisionTreeClassifier(random_state=42)

# Train Model
model.fit(X_train, y_train)

# Prediction
y_pred = model.predict(X_test)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)

print("Model Accuracy :", round(accuracy * 100,2), "%")

# Save Model
joblib.dump(model, "crop_model.pkl")
joblib.dump(encoder, "crop_encoder.pkl")

print("\nModel Saved Successfully!")
print("Encoder Saved Successfully!")