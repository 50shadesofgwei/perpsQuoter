from flask import Flask, jsonify, request
from callers.masterCaller import MasterQuoter
import json
import time
import threading
from utils.logger import logger

app = Flask(__name__)
# QUOTER = MasterQuoter()

# def start_hourly_runner():
#     while True:
#         QUOTER.hourly_runner()
#         time.sleep(3600) 


# threading.Thread(target=start_hourly_runner, daemon=True).start()

# def load_most_recent_quotes():
#     try:
#         with open('most_recent_quotes.json', 'r') as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {}

@app.route('/health', methods=['GET'])
def health_check():
    print('HEALTH ENDPOINT CALLED')
    return "OK", 200

# @app.route('/api/quotes/<string:symbol>', methods=['GET'])
# def get_quotes(symbol: str):
#     MOST_RECENT_QUOTES = load_most_recent_quotes()
#     symbol_quotes = []
    
#     for exchange, quotes in MOST_RECENT_QUOTES.items():
#         for quote in quotes:
#             for position_type in ["long", "short"]:
#                 if position_type in quote:
#                     matching_quotes = [entry for entry in quote[position_type] if entry["symbol"] == symbol.upper()]
#                     symbol_quotes.extend(matching_quotes)

#     return jsonify(symbol_quotes)


