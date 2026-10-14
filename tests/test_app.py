import hashlib
import json
import pytest
from werkzeug.security import generate_password_hash
from techarmor import SCHEMA, create_app, db
from techarmor.risk import assess

@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path/'test.sqlite'), 'SECRET_KEY': 'test-only', 'DEVICE_TOKEN': 'test-device'})
    with app.app_context():
        from flask import g
        g.app_db = app.config['DATABASE']
        db().executescript(SCHEMA)
        db().execute('INSERT INTO users VALUES(1,?,?,?)', ('admin',generate_password_hash('a-long-test-password'),'admin'))
        db().execute('INSERT INTO users VALUES(2,?,?,?)', ('operator',generate_password_hash('operator-password'),'operator'))
        db().execute("INSERT INTO cameras(name,location) VALUES('Gate','Campus')")
        db().commit()
    return app

@pytest.fixture
def client(app):
    c = app.test_client()
    with c.session_transaction() as s:
        s.update(uid=1,username='admin',role='admin',csrf='test-csrf')
    return c

H = {'X-CSRF-Token': 'test-csrf'}

def test_policy():
    assert assess({})['level']=='low'
    assert assess({'scream':.9})['level']=='moderate'
    assert assess({'gesture':.8,'scream':.8})['level']=='high'
    assert assess({'manual_sos':True})['score']==100
    for value in [float('nan'),float('inf'),-1,2,'0.5',True]:
        with pytest.raises(ValueError): assess({'scream':value})

def test_auth_and_csrf(app,client):
    assert app.test_client().get('/api/state').status_code==401
    assert client.post('/api/simulate',json={'camera_id':1}).status_code==403
    assert app.test_client().post('/api/observations',json={'camera_id':1}).status_code==401

def test_lifecycle_export(client):
    event=client.post('/api/simulate',json={'camera_id':1,'manual_sos':True},headers=H).json
    iid=event['incident_id']
    assert event['level']=='high'
    assert client.patch(f'/api/incidents/{iid}',json={'status':'resolved','note':'Reviewed'},headers=H).status_code==409
    for status in ['acknowledged','resolved']:
        assert client.patch(f'/api/incidents/{iid}',json={'status':status,'note':'Reviewed context'},headers=H).status_code==200
    data=client.get(f'/api/incidents/{iid}/export').json
    assert hashlib.sha256(json.dumps(data['record'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==data['sha256']
    assert data['record']['source']=='simulation'
    assert client.get('/api/state').json['counts']=={}

def test_dedup_and_device(client):
    payload={'camera_id':1,'gesture':.9,'scream':.9}
    a=client.post('/api/simulate',json=payload,headers=H).json
    b=client.post('/api/simulate',json=payload,headers=H).json
    assert a['incident_id']==b['incident_id']
    r=client.post('/api/observations',json={'camera_id':1,'people':2},headers={'Authorization':'Bearer test-device'})
    assert r.status_code==200 and r.json['incident_id'] is None
    assert client.get('/api/state').json['cameras'][0]['status']=='online'

def test_validation_and_disabled(client):
    for data in [None,[],{'camera_id':1,'people':-1},{'camera_id':1,'manual_sos':'true'},{'camera_id':1,'gesture':'bad'}]:
        assert client.post('/api/simulate',json=data,headers=H).status_code==400
    assert client.patch('/api/cameras/1',json={'enabled':False},headers=H).status_code==200
    assert client.post('/api/simulate',json={'camera_id':1},headers=H).status_code==409

def test_role(client):
    with client.session_transaction() as s: s['uid']=2
    assert client.post('/api/cameras',json={'name':'X','location':'Y'},headers=H).status_code==403

def test_login(app):
    c=app.test_client(); c.get('/login')
    with c.session_transaction() as s: csrf=s['csrf']
    assert c.post('/login',data={'csrf':csrf,'username':'admin','password':'a-long-test-password'}).status_code==302
    assert c.get('/api/state').status_code==200

def test_lockout(app):
    c=app.test_client();c.get('/login')
    with c.session_transaction() as s: csrf=s['csrf']
    for _ in range(5): c.post('/login',data={'csrf':csrf,'username':'admin','password':'wrong'})
    r=c.post('/login',data={'csrf':csrf,'username':'admin','password':'a-long-test-password'})
    assert b'Too many attempts' in r.data
    assert c.get('/api/state').status_code==401

def test_headers(client):
    r=client.get('/')
    assert "frame-ancestors 'none'" in r.headers['Content-Security-Policy']
    assert r.headers['Cache-Control']=='no-store'
