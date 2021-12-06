import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt


def predictLatestPriceForAll():
    csv_list = ["./data/final/bored-ape-kennel-club-data-cleaned.csv", "./data/final/mutant-ape-yacht-club-data-cleaned.csv", "./data/final/boredapeyachtclub-data-cleaned.csv", "./data/final/data-cleaned-combined.csv"]
    for csv in csv_list:
        df = pd.read_csv(csv)

        X = df[["rarity-ranking", "created_date"]]
        y = df["total_price"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        trained_model = LinearRegression().fit(X_train, y_train)

        predictions = trained_model.predict(X_test)
        actuals = []

        times = []

        i = 0
        pred_offsets = []
        max_pred = 0
        max_index = 0
        for sale in y_test:
            actuals.append(int(sale) / 1000000000000000000)
            pred_offsets.append((int(sale) - int(predictions[i])) / 1000000000000000000)
            if int(predictions[i]) > max_pred:
                max_pred = int(predictions[i])
                max_index = i
            #print(int(sale) - predictions[i])
            i += 1

        print(max_pred)
        print(max_index)

        j = 0
        for info in X_test["rarity-ranking"]:
            if j == max_index:
                print(info)
            j += 1


        avg_pred_offset = sum(pred_offsets) / len(pred_offsets)

        for ts in X_test["created_date"]:
            times.append(ts)

        title = csv.split("/")[len(csv.split("/")) - 1]
        #print(title, avg_pred_offset)
        #plotGraph(times, actuals, predictions, title)



def plotGraph(x, y, y2, title):
    plt.scatter(x, y, color="red")
    plt.scatter(x, y2, color="blue")
    plt.title(title)
    plt.xlabel('Unix Timestamp (s)')
    plt.ylabel('Sale Price (eth)')
    plt.show()



