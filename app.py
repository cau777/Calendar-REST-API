import sys

from datetime import date
from flask import Flask, abort
from flask_restful import Api, Resource, reqparse, inputs
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'event': self.name,
            'date': str(self.date)
        }


db.create_all()


def event_by_id(event_id):
    return Event.query.filter_by(id=event_id).first()


class TodayEventsResource(Resource):
    def get(self):
        events: list[dict] = [event.to_dict() for event in Event.query.filter_by(date=date.today()).all()]
        if len(events) == 0:
            return {"data": "There are no events for today!"}
        else:
            return events


class EventsResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()

        parser.add_argument('start_time', type=inputs.date,
                            help='The start date of the events! The correct format is YYYY-MM-DD!',
                            required=False)
        parser.add_argument('end_time', type=inputs.date,
                            help='The end date of the events! The correct format is YYYY-MM-DD!',
                            required=False)

        events: list[Event] = Event.query.all()
        try:
            args = parser.parse_args()
            start_time: date = args['start_time'].date()
            end_time: date = args['end_time'].date()

            events = list(filter(lambda event: start_time <= event.date <= end_time, events))
        except AttributeError:
            pass

        return [event.to_dict() for event in events]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('event', type=str,
                            help='The event name is required!',
                            required=True)
        parser.add_argument('date', type=inputs.date,
                            help='The event date with the correct format is required! The correct format is YYYY-MM-DD!',
                            required=True)
        args = parser.parse_args()
        event_name: str = args['event']
        event_date: date = args['date']

        event = Event(id=len(Event.query.all()), name=event_name, date=event_date)
        db.session.add(event)
        db.session.commit()

        return {
            'message': 'The event has been added!',
            'event': event_name,
            'date': event_date.strftime('%Y-%m-%d')
        }


class EventByIdResource(Resource):
    def get(self, event_id):
        event = event_by_id(event_id)

        if event is None:
            abort(404, "The event doesn't exist!")
        return event.to_dict()

    def delete(self, event_id):
        event = event_by_id(event_id)

        if event is None:
            abort(404, "The event doesn't exist!")

        db.session.delete(event)
        db.session.commit()
        return {"message": "The event has been deleted!"}


api = Api(app)
api.add_resource(TodayEventsResource, '/event/today')
api.add_resource(EventsResource, '/event')
api.add_resource(EventByIdResource, '/event/<int:event_id>')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
