import requests
import os.path
import csv
import json
import time
import datetime


opensea_api_key = "6f2a6401539a4560ab0c4a4e8983bc1f"
base_url = "https://api.opensea.io/api/v1"
model_type_urls = {
    "event": "/events?",
    "collections": "/collections?",
    "collection-stats": "/collection/*/stats?"
}
query_param_urls = {
    "event": {
        "event-type": "event_type=",
        "collection": "collection_slug=",
        "vetted": "only_opensea=",
        "auction-type": "auction_type=",
        "occurred-before": "occurred_before=",
        "limit": "limit="
    }
}
contract_address_to_slug = {
    "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d": "boredapeyachtclub"
}


def constructAPICall(model, query_params, values):
    url = base_url + model_type_urls[model] + query_param_urls[model][query_params[0]] + values[0]
    for i in range(len(query_params) - 1):
        url += "&" + query_param_urls[model][query_params[i+1]] + values[i+1]
    return url


def callOpenSeaAPI(url):
    headers = {"X-API-KEY": opensea_api_key}
    response = requests.request("GET", url, headers=headers)
    return response.text


def getCollectionStats(collection_slug):
    url = "https://api.opensea.io/api/v1/collection/" + collection_slug + "/stats"
    stats = json.loads(callOpenSeaAPI(url))
    new_cols = []
    for stat in stats["stats"]:
        new_cols.append([stat, stats["stats"][stat]])
    return new_cols


def getAssetData(collection, tokens):
    url = "https://api.opensea.io/api/v1/assets?order_direction=desc&offset=0&limit=30&collection=" + collection
    for token_num in tokens:
        url += "&token_ids=" + str(token_num)
    response = json.loads(callOpenSeaAPI(url))
    assets = []
    for asset in response["assets"]:
        traits = asset["traits"]
        traits_cleaned = []
        for trait in traits:
            traits_cleaned.append([trait["value"], trait["trait_count"]])

        last_sale = 0
        if asset["last_sale"] != None:
            last_sale = asset["last_sale"]["total_price"]

        assets.append([asset["token_id"], traits_cleaned, asset["num_sales"], last_sale])

    return assets


def calculteRarityValues(assets):
    rarity_values = []
    for traits in assets["traits"]:
        total_trait_count = 0
        traits = traits.split("],")
        for trait in traits:
            trait = trait.split(",")
            trait_count = trait[1]
            if trait_count[len(trait_count) - 1] == "]":
                trait_count = int(trait_count[:-2])
            else:
                trait_count = int(trait_count[1:])
            total_trait_count += trait_count
        rarity_values.append(total_trait_count)
    return rarity_values


def preprocessData(data, filters):
    collections_seen = []
    collection_stats = []
    processed_data = []
    data_json = json.loads(data)
    for event in data_json["asset_events"]:
        valid_entry = (event[filters[0]][filters[1]] == filters[2]) and (event["asset"] is not None) \
                      and (int(event["total_price"]) > 0)
        if valid_entry:
            event["token_id"] = event["asset"]["token_id"]
            event["created_date"] = timeToUnixTimestamp(event["created_date"])
            processed_data.append(event)

    return processed_data


def addDataToCSV(data, type, path, is_new):
    data_dir = "./data/" + type + "/"
    path = data_dir + path
    file_exists = os.path.exists(path)
    with open(path, "a+", newline="") as new_csv:
        writer = csv.writer(new_csv)
        if is_new or (not file_exists):
            new_csv.truncate(0)
            writer.writerow(["collection", "total_volume", "total_sales", "total_supply", "num_owners", "average_price", "market_cap", "floor_price", "token_num", "created_date", "total_price"])
        for event in data:
            writer.writerow([event["collection"], event["total_volume"], event["total_sales"], event["total_supply"], event["num_owners"], event["average_price"], event["market_cap"], event["floor_price"], event["token_num"], event["created_date"], event["total_price"]])
    return path


def timeToUnixTimestamp(timestamp):
    a = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
    b = datetime.datetime.strptime('1970-1-01T00:00:00.000000', '%Y-%m-%dT%H:%M:%S.%f')
    delta = a - b
    total = (delta.days * 86400) + delta.seconds
    return total




