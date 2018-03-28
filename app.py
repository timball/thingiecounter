import local_settings as conf
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, confi.DBFILE)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)


class ThingCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    count = db.Column(db.Integer, default=0)

    def __init__(self, name):
        self.name = name
        self.count = 0


class ThingSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'count')

thing_schema = ThingSchema()
things_schema = ThingSchema(many=True)


class APIError(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(APIError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def hello():
    with open('index.html') as file:
        content = file.read()
    return content


@app.route("/tallymebanana", methods=["GET"])
def tallybanana():
    all_the_things = ThingCounter.query.all()
    result = things_schema.dump(all_the_things)
    return jsonify(result.data)


@app.route("/tally", methods=["GET"])
def tally():
    all_the_things = ThingCounter.query.all()
    result = things_schema.dump(all_the_things)
    names = list()
    counts = list()
    for res in result.data:
        names.append(res['name'])
        counts.append(res['count'])
    ans = {'data': [{'x': names, 'y': counts, 'type': 'bar'}]}

    return jsonify(ans)


@app.route("/<thing>", methods=["PUT"])
def inc_thing(thing):
    thing = ''.join([*filter(str.isalnum, thing)])
    q = db.session.query(ThingCounter)
    r = q.filter(ThingCounter.name == thing)

    if r.count() == 1:
        id = r.all()[0].id
        count = r.all()[0].count
        name = r.all()[0].name
        thing = ThingCounter.query.get(id)
        thing.name = name
        thing.count = count + 1

    elif r.count() == 0:
        thing = ThingCounter(thing)
        db.session.add(thing)
        thing.count += 1

    else:
        raise APIError('number of things name %s:%d is neither {0,1}' % (thing, r.count()), status_code=520)

    db.session.commit()
    return thing_schema.jsonify(thing)


@app.route("/new", methods=["POST"])
def new_thing():
    name = request.json['name']

    new_thing = ThingCounter(name)

    db.session.add(new_thing)
    db.session.commit()

    return thing_schema.jsonify(new_thing)


if __name__ == '__main__':
    app.run(debug=False)
