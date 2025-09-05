import pandas as pd
import re

# Load dataset
df = pd.read_csv("data/train.csv")

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)    # remove links
    text = re.sub(r"@\w+", "", text)       # remove mentions
    text = re.sub(r"#", "", text)          # remove hashtag symbol
    text = re.sub(r"[^a-z\s]", "", text)   # keep only letters
    return text.strip()

df["clean_text"] = df["text"].apply(clean_text)

print(df[["text", "clean_text"]].head())
