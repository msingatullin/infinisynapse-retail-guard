import os
import io
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from app.infinisynapse_agent import InfiniSynapseAgent

app = Flask(__name__)
agent = InfiniSynapseAgent()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_CSV = os.path.join(DATA_DIR, "sample_inventory.csv")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/load-sample")
def load_sample():
    if os.path.exists(DEFAULT_CSV):
        df = pd.read_csv(DEFAULT_CSV)
        analysis = agent.analyze_inventory(df)
        plan = agent.generate_executive_action_plan(analysis)
        return jsonify(plan)
    return jsonify({"error": "Sample data file not found"}), 404

@app.route("/api/upload-csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
        
    try:
        df = pd.read_csv(file)
        analysis = agent.analyze_inventory(df)
        plan = agent.generate_executive_action_plan(analysis)
        return jsonify(plan)
    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 400

@app.route("/api/export-po-csv", methods=["POST"])
def export_po_csv():
    data = request.json or {}
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "No items to export"}), 400
        
    df = pd.DataFrame(items)
    cols = ["sku_id", "product_name", "supplier", "suggested_reorder_qty", "unit_cost", "estimated_po_cost", "recommended_action"]
    valid_cols = [c for c in cols if c in df.columns]
    out = io.StringIO()
    df[valid_cols].to_csv(out, index=False)
    out.seek(0)
    
    return send_file(
        io.BytesIO(out.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="purchase_order_dispatch.csv"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
