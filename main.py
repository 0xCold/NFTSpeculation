import pandas

import collect_and_preprocess_data as cpd
import init_and_train_model as itm
import make_predictions as mp

import pandas as pd
import requests
import time
from datetime import datetime
import json
import glob
import math
import csv


collect_data = False
init_model = False
train_model = True
make_predictions = True

if collect_data:
    collections = ["bored-ape-kennel-club", "mutant-ape-yacht-club", "boredapeyachtclub"]
    max_collected = 25000

    print("[COLLECTING SALE DATA]:", end="\n\t")
    for collection in collections:

        before_time = str(time.time())
        total_collected = 0
        chunk = 0
        print("Collection " + str(collections.index(collection)) + ": " + collection, end="\n\t\t")

        while True:
            api_url = cpd.constructAPICall("event",
                                           ["event-type", "vetted", "collection", "occurred-before", "limit"],
                                           ["successful", "True", collection, before_time, "300"])
            api_response = cpd.callOpenSeaAPI(api_url)
            print("Chunk " + str(chunk) + ": " + str(len(json.loads(api_response)["asset_events"])) + " sale events received from API", end="\n\t\t\t")

            cleaned_response = cpd.preprocessData(api_response, ["payment_token", "symbol", "ETH"])
            csv_name = "./data/sales/" + collection + "-sales-data-" + str(chunk) + ".csv"
            with open(csv_name, "a+", newline="") as new_csv:
                new_csv.truncate(0)
                writer = csv.writer(new_csv)
                writer.writerow(["token_id", "created_date", "total_price"])
                for event in cleaned_response:
                    writer.writerow([event["token_id"], event["created_date"], event["total_price"]])

            last_chunk = pd.read_csv(csv_name)
            chunk_size = len(last_chunk["created_date"])
            total_collected += len(last_chunk["created_date"])
            print(str(chunk_size) + " sale events remaining in chunk after preprocessing. Total events collected for collection: " + str(total_collected) + "/" + str(max_collected), end="\n\t\t\t\t")

            before_time = str(last_chunk["created_date"][len(last_chunk["created_date"]) - 1])
            print("Earliest sale in chunk is " + str(datetime.fromtimestamp(int(before_time))) + ". Re-Calling API with this timestamp...", end="\n\t\t")

            chunk += 1
            if total_collected > max_collected or chunk_size < 3:
                print("Completed collecting sale event data for " + collection + "!", end="\n\n\t")
                break

            time.sleep(2)

    print("All collections scraped!", end="\n\n")

    print("[COLLECTING ASSET DATA]:", end="\n\t")
    for collection in collections:
        print("Collection " + str(collections.index(collection)) + ": " + collection, end="\n\t\t")
        path = "./data/sales/" + collection + "-sales-data-*.csv"
        file_list = glob.glob(path)
        tokens_seen = []
        for chunk_csv in file_list:
            chunk_df = pandas.read_csv(chunk_csv)
            unique_tokens = chunk_df["token_id"].unique()
            for token in unique_tokens:
                if token not in tokens_seen:
                    tokens_seen.append(token)
        print("Total unique tokens seen for collection: " + str(len(tokens_seen)), end="\n\t\t")

        num_calls_to_make = math.ceil(len(tokens_seen) / 30)
        offset = 30
        end_index = 0
        asset_data = []
        total_collected = 0
        chunk = 0
        for call_num in range(num_calls_to_make):
            start_index = end_index
            end_index = end_index + offset
            call_tokens = tokens_seen[start_index:end_index]
            chunk_assets = cpd.getAssetData(collection, call_tokens)
            print("Chunk " + str(chunk) + ": " + str(len(chunk_assets)) + " assets retireved from API", end="\n\t\t\t")

            asset_data += chunk_assets
            total_collected += len(chunk_assets)
            print(str(len(chunk_assets)) + " assets remaining in chunk after preprocessing. Total assets collected for collection: " + str(len(asset_data)) + " / " + str(len(tokens_seen)), end="\n\t\t")
            chunk += 1
            time.sleep(5)

        with open("./data/assets/" + collection + "-assets.csv", "a+", newline="") as new_csv:
            new_csv.truncate(0)
            writer = csv.writer(new_csv)
            writer.writerow(["token_id", "traits", "num_sales", "latest_sale_value"])
            for asset in asset_data:
                writer.writerow(asset)

        print("Completed collecting asset data for " + collection + "!", end="\n\n\t")

    print("All assets retrieved!", end="\n\n")

    print("[COLLECTING COLLECTION DATA]:", end="\n\t")
    with open("./data/collections/collection-stats.csv", "a+", newline="") as new_csv:
        new_csv.truncate(0)
        writer = csv.writer(new_csv)
        writer.writerow(
            ["name", "one_day_volume", "one_day_change", "one_day_sales", "one_day_average_price", "seven_day_volume",
             "seven_day_change", "seven_day_sales", "seven_day_average_price", "thirty_day_volume", "thirty_day_change",
             "thirty_day_sales", "thirty_day_average_price", "total_volume", "total_sales", "total_supply", "count",
             "num_owners", "average_price", "num_reports", "market_cap", "floor_price"])

    for collection in collections:
        print("Collection " + str(collections.index(collection)) + ": " + collection, end="\n\t\t")
        collection_stats = cpd.getCollectionStats(collection)
        with open("./data/collections/collection-stats.csv", "a+", newline="") as new_csv:
            writer = csv.writer(new_csv)
            new_row = [collection]
            for stat in collection_stats:
                new_row.append(stat[1])
            writer.writerow(new_row)

    print("All collection stats retrieved!", end="\n")

    print("[PREPROCESSING + CLEANING DATA]:", end="\n\t")

    to_append = []
    for collection in collections:
        print("Collection " + str(collections.index(collection)) + ": " + collection, end="\n\t\t")

        to_combine = []
        sales_files = glob.glob("./data/sales/" + collection + "-sales-data-*.csv")
        for file in sales_files:
            to_combine.append(pd.read_csv(file))
        base = pd.concat(to_combine, axis=0, ignore_index=True)

        collection_stats = pd.read_csv("./data/collections/collection-stats.csv")
        for stat in collection_stats.columns:
            base[stat] = collection_stats[stat][collections.index(collection)]

        assets_df = pd.read_csv("./data/assets/" + collection + "-assets.csv")
        rarity_rankings = cpd.calculteRarityValues(assets_df)
        assets_df["rarity-ranking"] = rarity_rankings
        with_asset_data = pd.merge(assets_df, base, on='token_id', how='inner')

        cols_to_multiply = ["one_day_volume", "one_day_average_price", "one_day_change", "seven_day_volume", "seven_day_average_price", "seven_day_change", "thirty_day_volume", "thirty_day_change", "thirty_day_average_price", "total_volume", "market_cap", "average_price", "floor_price"]
        for col_name in cols_to_multiply:
            count = 0
            for col in with_asset_data[col_name]:
                in_eth = with_asset_data[col_name][count] * 1000000000000000000
                with_asset_data[col_name][count] = in_eth
                count += 1

        to_append.append(with_asset_data)
        with_asset_data.to_csv("./data/final/" + collection + "-data-cleaned.csv")

    cleaned_combined = pd.concat(to_append, axis=0, ignore_index=True)
    cleaned_combined.to_csv("./data/final/data-cleaned-combined.csv")


if init_model:
    csv_list = ["./data/final/bored-ape-kennel-club-data-cleaned.csv", "./data/final/mutant-ape-yacht-club-data-cleaned.csv", "./data/final/boredapeyachtclub-data-cleaned.csv", "./data/final/data-cleaned-combined.csv"]
    all_results = []
    for csv in csv_list:
        print(csv)
        results = itm.testAndCompareModels(csv)
        all_results.append(results)
    print(all_results)

if train_model:
    mp.predictLatestPriceForAll()