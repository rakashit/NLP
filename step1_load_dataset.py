import pandas as pd

# Load dataset
df = pd.read_csv("data/train.csv")

print("✅ Dataset loaded!")
print("Shape:", df.shape)
print("\nFirst 5 rows:\n", df.head())
