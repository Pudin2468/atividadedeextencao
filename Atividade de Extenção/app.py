import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal, InvalidOperation

app = Flask(__name__)
# Use absolute path for the SQLite file to avoid issues with cwd, accents or permissions.
# Ensure database directory exists and is writable. Create folder if missing.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(BASE_DIR, 'database')
try:
    os.makedirs(db_dir, exist_ok=True)
    # Try to set permissive mode; on Windows this is a no-op for ACLs but won't crash.
    try:
        os.chmod(db_dir, 0o700)
    except Exception:
        pass
except Exception:
    # If creation fails, we'll continue and let SQLAlchemy raise a clear error later.
    pass

db_path = os.path.join(db_dir, 'app.db')
db_path = db_path.replace('\\', '/')
default_db = f"sqlite:///{db_path}"
# Allow overriding DB via env var for testing (e.g., sqlite:///:memory:)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TEST_DB', default_db)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # New: store the user's name to associate records
    name = db.Column(db.String(120), nullable=True)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    water_l = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    imc = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'name': self.name,
            'id': self.id,
            'height_cm': self.height_cm,
            'weight_kg': self.weight_kg,
            'water_l': self.water_l,
            'imc': self.imc,
            'created_at': self.created_at.isoformat()
        }

try:
    # Tentativa de criar as tabelas ao importar o módulo. Em alguns ambientes
    # a execução em decorator pode falhar; esta chamada garante que o DB
    # será criado quando a aplicação iniciar.
    with app.app_context():
        db.create_all()
        # Migration fallback: ensure 'imc' column exists for older DBs
        try:
            import sqlite3
            uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if uri.startswith('sqlite:///') and uri != 'sqlite:///:memory:':
                db_file = uri.replace('sqlite:///', '')
                if os.path.exists(db_file):
                    conn = sqlite3.connect(db_file)
                    cur = conn.cursor()
                    cur.execute("PRAGMA table_info('record')")
                    cols = [r[1] for r in cur.fetchall()]
                    # Ensure both 'imc' and 'name' exist; add individually if missing
                    if 'imc' not in cols:
                        try:
                            cur.execute('ALTER TABLE record ADD COLUMN imc REAL')
                            conn.commit()
                        except Exception:
                            pass
                    if 'name' not in cols:
                        try:
                            cur.execute("ALTER TABLE record ADD COLUMN name TEXT")
                            conn.commit()
                        except Exception:
                            pass
                    cur.close()
                    conn.close()
        except Exception:
            pass
except Exception:
    # Se falhar na importação (ambiente de teste), deixamos para serem criadas
    # pelo runtime normal ao iniciar o servidor.
    pass

@app.route('/')
def index():
    latest = Record.query.order_by(Record.created_at.desc()).first()
    last_weight = latest.weight_kg if latest else None
    last_name = latest.name if latest and latest.name else None
    avg_water = None
    if Record.query.count() > 0:
        avg_water = db.session.query(db.func.avg(Record.water_l)).scalar()
        avg_water = round(avg_water, 2) if avg_water is not None else None
    return render_template('index.html', last_weight=last_weight, avg_water=avg_water, last_name=last_name)

@app.route('/add', methods=['POST'])
def add_record():
    try:
        name = request.form.get('name', '').strip()
        height = float(request.form.get('height_cm', '').strip())
        weight = float(request.form.get('weight_kg', '').strip())
        water = float(request.form.get('water_l', '').strip())
    except (ValueError, TypeError):
        return redirect(url_for('index'))

    if not (30 <= height <= 300 and 2 <= weight <= 500 and 0 <= water <= 20):
        return redirect(url_for('index'))

    # Calculate BMI (IMC): weight (kg) / (height_m)^2; height given in cm
    try:
        height_m = height / 100.0
        imc_val = round(float(weight) / (height_m * height_m), 2) if height_m > 0 else None
    except Exception:
        imc_val = None

    rec = Record(height_cm=height, weight_kg=weight, water_l=water, imc=imc_val)
    # Save name if provided and reasonable length
    if name:
        rec.name = name[:120]
    db.session.add(rec)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/api/records', methods=['GET'])
def api_records():
    records = Record.query.order_by(Record.created_at.asc()).all()
    return jsonify([r.to_dict() for r in records])


@app.route('/export', methods=['GET'])
def export_csv():
    records = Record.query.order_by(Record.created_at.asc()).all()
    def generate():
        yield 'id,created_at,name,height_cm,weight_kg,water_l,imc\n'
        for r in records:
            name_val = r.name.replace(',', ' ') if r.name else ''
            line = f"{r.id},{r.created_at.isoformat()},{name_val},{r.height_cm},{r.weight_kg},{r.water_l},{r.imc if r.imc is not None else ''}\n"
            yield line
    return Response(generate(), mimetype='text/csv', headers={
        'Content-Disposition':'attachment; filename=records.csv'
    })

# ICMS removed — replaced by IMC (BMI) calculation stored per record

if __name__ == '__main__':
    app.run(debug=True)
