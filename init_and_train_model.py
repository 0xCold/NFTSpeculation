import pandas as pd
import numpy as np
from sklearn import datasets
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import itertools


def generateXColCombinations(cols):
    combos = []
    for L in range(1, len(cols) + 1):
        for subset in itertools.combinations(cols, L):
            as_array = []
            for val in subset:
                as_array.append(val)
            combos.append(as_array)
    return combos


def testAndCompareModels(path):
    df = pd.read_csv(path)

    X = df[["num_sales", "rarity-ranking", "created_date"]]
    y = df["total_price"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)

    models = [LinearRegression(), LogisticRegression()]
    model_results = []
    for model in models:
        trained_model = model.fit(X_train, y_train)
        model_score = trained_model.score(X_test, y_test)
        model_results.append(model_score)
        print(model, model_score)

    return model_results


