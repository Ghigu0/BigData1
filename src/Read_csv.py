import pandas as pd

df = pd.read_csv("../porto/porto.csv", nrows=10000)

print(df.head())
print(df.info())