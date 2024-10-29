from flask import Flask, jsonify, request
from callers.masterCaller import MasterQuoter
import json
import time

app = Flask(__name__)
app.run(host='0.0.0.0', port=8080)
QUOTER = MasterQuoter()
QUOTER.hourly_runner()
time.sleep(10)
with open('most_recent_quotes.json', 'r') as f:
    MOST_RECENT_QUOTES = json.load(f)

@app.route('/api/quotes/<string:symbol>', methods=['GET'])
def get_quotes(symbol: str):
    symbol_quotes = []
    
    for exchange, quotes in MOST_RECENT_QUOTES.items():
        for quote in quotes:
            for position_type in ["long", "short"]:
                if position_type in quote:
                    matching_quotes = [entry for entry in quote[position_type] if entry["symbol"] == symbol.upper()]
                    symbol_quotes.extend(matching_quotes)

    return jsonify(symbol_quotes)

