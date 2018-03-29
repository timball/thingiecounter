import local_settings as conf
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, conf.DBFILE)
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
    """ tallybanana -- this just returns json of what's in the db no processing """
    all_the_things = ThingCounter.query.all()
    result = things_schema.dump(all_the_things)
    return jsonify(result.data)


@app.route("/tally", methods=["GET"])
def tally():
    """ tally -- returns a json that graph lib can deal with """
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
    """ inc_thing -- this incriments a thing's counter or sets it to 1 if thing doesn't exist """
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


@app.route("/<thing>", methods=["DELETE"])
def rm_thing(thing):
    """ rm_thing -- deletes a thing from the database """
    thing = ''.join([*filter(str.isalnum, thing)])
    auth = request.headers.get(conf.AUTH_HDR)

    if (auth is conf.AUTH_HDR):
        raise APIError('Say ‘friend’ and enter.', status_code=401)
    else:
        q = db.session.query(ThingCounter)
        r = q.filter(ThingCounter.name == thing)

        if r.count() == 1:
            id = r.all()[0].id
            thing = ThingCounter.query.get(id)
            db.session.delete(thing)
            db.session.commit()

        elif r.count() == 0:
            True
            # do nothing explicitly

        else:
            raise APIError('number of things name %s:%d is neither {0,1}' % (thing, r.count()), status_code=520)

    return jsonify("Gwaem")


@app.route("/<thing>", methods=["PURGE"])
def purge_thing(thing):
    """ purge_thing -- resets thing's counter to 0 """
    thing = ''.join([*filter(str.isalnum, thing)])
    auth = request.headers.get(conf.AUTH_HDR)

    if (auth is conf.AUTH_HDR):
        raise APIError('Say ‘friend’ and enter.', status_code=401)
    else:
        q = db.session.query(ThingCounter)
        r = q.filter(ThingCounter.name == thing)

        if r.count() == 1:
            id = r.all()[0].id
            thing = ThingCounter.query.get(id)
            thing.count = 0
            db.session.commit()

        elif r.count() == 0:
            True
            # do nothing explicitly

        else:
            raise APIError('number of things name %s:%d is neither {0,1}' % (thing, r.count()), status_code=520)
    return jsonify("Navaer")


@app.route("/new", methods=["POST"])
def new_thing():
    """ new_thing() -- mostly unneeded way to create a new thing to count """
    name = request.json['name']

    new_thing = ThingCounter(name)

    db.session.add(new_thing)
    db.session.commit()

    return thing_schema.jsonify(new_thing)


if __name__ == '__main__':
    app.run(debug=True)
