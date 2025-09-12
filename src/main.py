from flask import Flask, request, jsonify
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
DB_PATH = "records.db"

# table initialization
# for now assume that all fields are exactly those given in the sample
with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            gene_count INT NOT NULL, 
            sample_quality DECIMAL NOT NULL
        )
        """
    )

# ensures proper formatting of the record submitted
# return True if formatted properly, False otherwise 
def check_format(record):
    # first validate that "device_id", "timestamp", and "data_payload" all exist
    device_id = record.get("device_id")
    timestamp = record.get("timestamp")
    data_payload = record.get("data_payload")
    # check if any are missing
    if [entry for entry in (device_id, timestamp, data_payload) if entry is None or not entry]:
        return False
    # device_id and timestamp should be strings
    if not isinstance(device_id, str) or not isinstance(timestamp, str):  
        return False
    # avoid overly large input (256 I guess?)
    if len(device_id) > 256:
        return False
    # check formatting of timestamp
    try:
        datetime.fromisoformat(record.get("timestamp").replace('Z', '+00:00'))
    except: 
        return False
    # check that data_payload has a dictionary
    if not isinstance(data_payload, dict):
        return False
    # all fields present w/ acceptable formats
    return True

# ensures safe SQL may be generated for the record
# return True if formatted properly, False otherwise 
def check_safe_sql(record):
    return True

@app.post("/ingest")
def add_record():
    # ensure request is in JSON form
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    # get record and set fields 
    record = request.get_json(silent=True)
    if record is None:
        return jsonify({"error": "Malformed JSON record"}), 400
    
    # ensure it is properly formatted
    if not check_format(record):
        return jsonify({"error": "Record improperly formatted"}), 400
    
    device_id = record["device_id"].strip()
    timestamp = record["timestamp"]
    data_payload = record["data_payload"]
    gene_count = data_payload.get("gene_count", None)
    sample_quality = data_payload.get("sample_quality", None)

    # type checks before insertion
    try: 
        gene_count = int(gene_count)
    except(TypeError, ValueError):
        return jsonify({"error": "'gene_count' must be an integer"}), 400
    try: 
        sample_quality = float(sample_quality)
    except(TypeError, ValueError):
        return jsonify({"error": "'sample_quality' must be a number"}), 400
    
    # ensure absence of SQL injection
    # this is largely covered by parametrization and typechecking
    # keep the function just in case we want to set it up later 
    if not check_safe_sql(record):
        return jsonify({"error": "Translation to SQL spotted potentially malicious code"}), 400

    # add record to SQL database
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO recordings(device_id, timestamp, gene_count, sample_quality) VALUES (?, ?, ?, ?)", 
            (device_id, timestamp, gene_count, sample_quality),
        )
    return jsonify({"status": "ok"}), 201

@app.get("/records")
def list_records():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * from recordings ORDER BY id").fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/")
def home():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
