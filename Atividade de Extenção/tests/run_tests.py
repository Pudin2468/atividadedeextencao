from app import app, db, Record
import json

with app.app_context():
    db.drop_all()
    db.create_all()

client = app.test_client()

resp = client.post('/add', data={'height_cm':'170','weight_kg':'70','water_l':'2.5'}, follow_redirects=True)
print('POST /add status:', resp.status_code)

resp2 = client.get('/api/records')
records = resp2.get_json()
print('GET /api/records ->', records)
print('Saved IMC:', records[0].get('imc'))

resp3 = client.post('/api/icms', data=json.dumps({'value':100,'rate':18}), content_type='application/json')
print('POST /api/icms ->', resp3.get_json())

ok = (resp.status_code==200) and isinstance(records, list) and len(records)>=1 and records[0].get('imc') is not None
print('TESTS OK?' , ok)
