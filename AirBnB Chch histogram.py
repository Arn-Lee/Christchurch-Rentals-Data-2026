import pandas as pd
import matplotlib.pyplot as plt

#Load base workflow spreadsheet
df = pd.read_csv("data/AirBnB_all_chch.csv")

#Plot histogram of prices for Christchurch AirBnBs
plt.hist(df["price"], bins=50, edgecolor="black")
plt.title("Histogram of AirBnB price - Christchurch")
plt.xlabel("AirBnB price")
plt.ylabel("Frequency")
plt.show()