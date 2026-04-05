# app.py

import os, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv('.env')

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
SYNC_SECRET  = os.environ.get('SYNC_SECRET', '')

def supabase_insert(row):
    url = f"{SUPABASE_URL}/rest/v1/triage_records"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    r = requests.post(url, json=row, headers=headers)
    result = r.json()
    if not isinstance(result, list) or len(result) == 0:
        raise ValueError(f"Supabase error: {result}")
    return result

def validate_secret(req):
    return req.headers.get('X-Sync-Secret') == SYNC_SECRET
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})
@app.route('/sync', methods=['POST'])
def sync_record():
    if not validate_secret(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    module = data.get('module', 'chest_pain')
    # Build the row — null-safe
    row = {
        'pid':        data.get('pid'),
        'module':     module,
        'facility':   data.get('facility'),
        'age':        data.get('age'),
        'sex':        data.get('sex'),
        'sbp':        data.get('sbp'),
        'pulse':      data.get('pulse'),
        'spo2':       data.get('spo2'),
        'pain_score': data.get('painScore'),
        'pain_char':  data.get('painChar'),
        'esi':        data.get('esi'),
        'category':   data.get('category'),
        'risk_scd':   data.get('riskScd', False),
        'risk_hiv':   data.get('riskHiv', False),
        'raw_json':   data,
    }
    try:
        result = supabase_insert(row)
    except ValueError as e:
        return jsonify({'error': str(e)}), 502
    return jsonify({'status': 'synced', 'id': result[0]['id']}), 201
@app.route('/sync/batch', methods=['POST'])
def sync_batch():
    """Sync multiple records in one request."""
    if not validate_secret(request):
        return jsonify({'error': 'Unauthorized'}), 401
    records = request.get_json()
    if not isinstance(records, list) or len(records) == 0:
        return jsonify({'error': 'Expected non-empty array'}), 400
    synced_ids = []
    for data in records:
        module = data.get('module', 'chest_pain')
        row = {
            'pid':        data.get('pid'),
            'module':     module,
            'facility':   data.get('facility'),
            'age':        data.get('age'),
            'sex':        data.get('sex'),
            'sbp':        data.get('sbp'),
            'pulse':      data.get('pulse'),
            'spo2':       data.get('spo2'),
            'pain_score': data.get('painScore'),
            'pain_char':  data.get('painChar'),
            'esi':        data.get('esi'),
            'category':   data.get('category'),
            'risk_scd':   data.get('riskScd', False),
            'risk_hiv':   data.get('riskHiv', False),
            'raw_json':   data,
        }
        try:
            result = supabase_insert(row)
        except ValueError as e:
            return jsonify({'error': str(e), 'synced_so_far': len(synced_ids)}), 502
        synced_ids.append(result[0]['id'])
    return jsonify({'status': 'synced', 'count': len(synced_ids)}), 201
if __name__ == '__main__':
    app.run(debug=True)
