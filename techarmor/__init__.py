"""Her TechArmor operator console."""
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

import click
from flask import Flask, abort, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cameras(id INTEGER PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, last_seen TEXT, people INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS incidents(id INTEGER PRIMARY KEY, camera_id INTEGER NOT NULL REFERENCES cameras(id), level TEXT NOT NULL, score INTEGER NOT NULL, source TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', signals TEXT NOT NULL, reasons TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, note TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS login_limits(username TEXT PRIMARY KEY, failures INTEGER NOT NULL, blocked_until REAL NOT NULL);
'''


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def db():
    if 'db' not in g:
        g.db = sqlite3.connect(g.app_db, timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def audit(action, detail):
    db().execute('INSERT INTO audit(actor,action,detail,created_at) VALUES(?,?,?,?)',
                 (session.get('username', 'device'), action, str(detail), now()))


def protected(admin=False):
    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'uid' not in session:
                abort(401)
            user = db().execute('SELECT * FROM users WHERE id=?', (session['uid'],)).fetchone()
            if not user or (admin and user['role'] != 'admin'):
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorate


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    secret_path = Path(app.instance_path) / 'session.key'
    if not secret_path.exists():
        try:
            with secret_path.open('x') as f:
                f.write(secrets.token_hex(32))
            secret_path.chmod(0o600)
        except FileExistsError:
            pass
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secret_path.read_text(),
                      DATABASE=str(Path(app.instance_path) / 'techarmor.sqlite'),
                      DEVICE_TOKEN=os.getenv('DEVICE_TOKEN', ''),
                      MAX_CONTENT_LENGTH=64 * 1024,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                      SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE') == '1',
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
    if config:
        app.config.update(config)

    @app.before_request
    def before():
        g.app_db = app.config['DATABASE']
        if request.path.startswith('/api/') and request.method in ('POST', 'PATCH'):
            if not isinstance(request.get_json(silent=True), dict):
                abort(400, 'A JSON object is required')
        if request.method in ('POST', 'PATCH', 'DELETE') and request.endpoint != 'ingest':
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
            if not token or not hmac.compare_digest(str(token), session.get('csrf', '')):
                abort(403, 'Invalid CSRF token. Reload the page.')

    @app.teardown_appcontext
    def close(error=None):
        connection = g.pop('db', None)
        if connection:
            connection.close()

    @app.after_request
    def headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    def error(e):
        if request.path.startswith('/api/'):
            return jsonify(error=e.description), e.code
        return render_template('error.html', message=e.description, code=e.code), e.code

    @app.get('/health')
    def health():
        return jsonify(status='ok', mode='prototype')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        session.setdefault('csrf', secrets.token_hex(24))
        message = None
        if request.method == 'POST':
            username = request.form.get('username', '').strip()[:80]
            limit = db().execute('SELECT * FROM login_limits WHERE username=?', (username,)).fetchone()
            if limit and limit['blocked_until'] > time.time():
                message = 'Too many attempts. Try again in 5 minutes.'
            else:
                user = db().execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
                if user and check_password_hash(user['password'], request.form.get('password', '')):
                    session.clear()
                    session.update(uid=user['id'], username=user['username'], role=user['role'], csrf=secrets.token_hex(24))
                    session.permanent = True
                    db().execute('DELETE FROM login_limits WHERE username=?', (username,))
                    audit('login', 'Operator signed in')
                    db().commit()
                    return redirect(url_for('index'))
                failures = (limit['failures'] if limit else 0) + 1
                db().execute('INSERT OR REPLACE INTO login_limits VALUES(?,?,?)', (username, failures, time.time() + 300 if failures >= 5 else 0))
                db().commit()
                message = 'Username or password is incorrect.'
        return render_template('login.html', message=message)

    @app.post('/logout')
    @protected()
    def logout():
        audit('logout', 'Operator signed out')
        db().commit()
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    def index():
        if 'uid' not in session:
            return redirect(url_for('login'))
        return render_template('index.html')

    @app.get('/api/state')
    @protected()
    def state():
        cameras = [dict(r) for r in db().execute('SELECT * FROM cameras ORDER BY id')]
        for c in cameras:
            c['status'] = 'disabled' if not c['enabled'] else 'online' if c['last_seen'] and (datetime.now(timezone.utc) - datetime.fromisoformat(c['last_seen'])).total_seconds() < 30 else 'offline'
        incidents = [dict(r) for r in db().execute('SELECT * FROM incidents ORDER BY id DESC LIMIT 200')]
        for i in incidents:
            i['signals'] = json.loads(i['signals'])
            i['reasons'] = json.loads(i['reasons'])
        counts = {r['level']: r['n'] for r in db().execute("SELECT level,COUNT(*) n FROM incidents WHERE status != 'resolved' GROUP BY level")}
        return jsonify(cameras=cameras, incidents=incidents, counts=counts,
                       audit=[dict(r) for r in db().execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100')], mode='prototype')

    @app.post('/api/cameras')
    @protected(admin=True)
    def add_camera():
        d = request.get_json(silent=True) or {}
        name, location = d.get('name'), d.get('location')
        if not isinstance(name, str) or not isinstance(location, str) or not name.strip() or not location.strip() or len(name) > 80 or len(location) > 160:
            abort(400, 'Name and location are required (80 / 160 characters maximum).')
        cur = db().execute('INSERT INTO cameras(name,location) VALUES(?,?)', (name.strip(), location.strip()))
        audit('camera.create', cur.lastrowid)
        db().commit()
        return jsonify(id=cur.lastrowid), 201

    @app.patch('/api/cameras/<int:cid>')
    @protected(admin=True)
    def camera_status(cid):
        d = request.get_json(silent=True) or {}
        if not isinstance(d.get('enabled'), bool):
            abort(400, 'enabled must be boolean')
        cur = db().execute('UPDATE cameras SET enabled=? WHERE id=?', (d['enabled'], cid))
        if not cur.rowcount:
            abort(404)
        audit('camera.toggle', cid)
        db().commit()
        return jsonify(ok=True)

    def observe(d, source):
        from .risk import assess
        if not isinstance(d, dict):
            abort(400, 'A JSON object is required')
        cid = d.get('camera_id')
        people = d.get('people', 0)
        if type(cid) is not int or type(people) is not int or not 0 <= people <= 10000:
            abort(400, 'camera_id and people must be valid integers')
        c = db().execute('SELECT * FROM cameras WHERE id=?', (cid,)).fetchone()
        if not c:
            abort(404, 'Unknown camera')
        if not c['enabled']:
            abort(409, 'Camera is disabled')
        try:
            result = assess(d)
        except ValueError as e:
            abort(400, str(e))
        timestamp = now()
        db().execute('UPDATE cameras SET last_seen=?, people=? WHERE id=?', (timestamp, people, cid))
        iid = None
        if result['level'] != 'low':
            signals = {k: d.get(k, False if k == 'manual_sos' else 0) for k in ('gesture', 'scream', 'aggression', 'manual_sos')}
            # Coalesce repeated detector alerts for 60 seconds; each manual SOS creates a new event.
            recent = db().execute("SELECT id FROM incidents WHERE camera_id=? AND level=? AND source=? AND status='open' AND created_at>? ORDER BY id DESC LIMIT 1", (cid, result['level'], source, (datetime.now(timezone.utc)-timedelta(seconds=60)).isoformat())).fetchone()
            if recent and not signals['manual_sos']:
                iid = recent['id']
            else:
                cur = db().execute('INSERT INTO incidents(camera_id,level,score,source,signals,reasons,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)', (cid, result['level'], result['score'], source, json.dumps(signals), json.dumps(result['reasons']), timestamp, timestamp))
                iid = cur.lastrowid
                audit('incident.create', f'{iid}: {source}')
        db().commit()
        return jsonify(**result, incident_id=iid, source=source)

    @app.post('/api/simulate')
    @protected()
    def simulate():
        return observe(request.get_json(silent=True), 'simulation')

    @app.post('/api/observations')
    def ingest():
        expected = app.config['DEVICE_TOKEN']
        auth = request.headers.get('Authorization', '')
        if not expected or not hmac.compare_digest(auth, 'Bearer ' + expected):
            abort(401, 'Device token required')
        return observe(request.get_json(silent=True), 'device')

    @app.patch('/api/incidents/<int:iid>')
    @protected()
    def update(iid):
        d = request.get_json(silent=True) or {}
        status, note = d.get('status'), d.get('note', '')
        if status not in ('acknowledged', 'resolved') or not isinstance(note, str) or not 3 <= len(note.strip()) <= 1000:
            abort(400, 'Choose a status and provide a review note (3–1000 characters).')
        row = db().execute('SELECT * FROM incidents WHERE id=?', (iid,)).fetchone()
        if not row:
            abort(404)
        allowed = {'open': ('acknowledged',), 'acknowledged': ('resolved',), 'resolved': ()}
        if status not in allowed[row['status']]:
            abort(409, 'Acknowledge before resolving. Resolved events are closed.')
        db().execute('UPDATE incidents SET status=?, note=?, updated_at=? WHERE id=?', (status, note.strip(), now(), iid))
        audit('incident.' + status, f'{iid}: {note.strip()}')
        db().commit()
        return jsonify(ok=True)

    @app.get('/api/incidents/<int:iid>/export')
    @protected()
    def export(iid):
        row = db().execute('SELECT * FROM incidents WHERE id=?', (iid,)).fetchone()
        if not row:
            abort(404)
        record = dict(row)
        raw = json.dumps(record, sort_keys=True, separators=(',', ':')).encode()
        payload = {'record': record, 'sha256': hashlib.sha256(raw).hexdigest(), 'canonicalization': 'json.dumps(record, sort_keys=True, separators=(",", ":")) UTF-8', 'scope': 'Incident metadata only. No CCTV or audio included.'}
        audit('incident.export', iid)
        db().commit()
        response = jsonify(payload)
        response.headers['Content-Disposition'] = f'attachment; filename=incident-{iid}.json'
        return response

    @app.cli.command('init-db')
    def init_db():
        g.app_db = app.config['DATABASE']
        db().executescript(SCHEMA)
        db().commit()
        click.echo('Database initialized without deleting existing records.')

    @app.cli.command('create-user')
    @click.option('--username', prompt=True)
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option('--role', type=click.Choice(['admin', 'operator']), default='admin')
    def create_user(username, password, role):
        if len(password) < 12:
            raise click.ClickException('Use at least 12 characters.')
        g.app_db = app.config['DATABASE']
        try:
            db().execute('INSERT INTO users(username,password,role) VALUES(?,?,?)', (username, generate_password_hash(password), role))
            db().commit()
        except sqlite3.IntegrityError:
            raise click.ClickException('Username already exists.')
        click.echo('User created.')

    @app.cli.command('seed-demo')
    def seed():
        g.app_db = app.config['DATABASE']
        if db().execute('SELECT COUNT(*) FROM cameras').fetchone()[0] == 0:
            db().executemany('INSERT INTO cameras(name,location) VALUES(?,?)', [('North entrance', 'Campus · Gate A'), ('Transit walkway', 'Campus · East block'), ('Library courtyard', 'Campus · Central square')])
            db().commit()
        click.echo('Demo camera registry ready. No live feeds are connected.')
    return app
