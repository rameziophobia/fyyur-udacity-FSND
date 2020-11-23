#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
from datetime import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from itertools import groupby
from operator import attrgetter
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    artist_image_link = db.Column(db.String(512))
    start_time = db.Column(db.Date)

    def __repr__(self):
      return f'<show#{self.id}, aritst #{self.artist_id}, venue #{self.venue_id}>'

    def display_dict(self):
      return {
        "venue_id": self.venue_id,
        "venue_name": self.venue.name,
        "artist_id": self.id,
        "artist_name": self.artist.name,
        "artist_image_link": self.artist_image_link,
        "start_time": format_datetime(str(self.start_time))
      }
      


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column("genres", db.ARRAY(db.String()))
    shows = db.relationship(
      'Show',
      backref='venue',
      lazy=True,
      collection_class=list,
      cascade='save-update'
    )

    def __repr__(self):
      return f'<venue#{self.id}, name: {self.name}>'

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column("genres", db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship(
      'Show',
      backref='artist',
      lazy=True,
      collection_class=list,
      cascade='save-update'
    )

    def __repr__(self):
      return f'<artist#{self.id}, name: {self.name}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.order_by(Venue.city).all()
  
  print(venues)
  venues_by_city = [list(g) for k, g in groupby(venues, attrgetter('city'))]
  print(venues_by_city)

  data = [{
    "city": venue_by_city[0].city,
    "state": venue_by_city[0].state,
    "venues": [{
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": 0,
    } for venue in venue_by_city]}
    for venue_by_city in venues_by_city]
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_query = request.form.get('search_term', '')
  result = Venue.query.filter(Venue.name.ilike(f'%{search_query}%'))
  response={
    "count": result.count(),
    "data": result
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_query)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)

  now = datetime.now().date()
  past_shows, upcoming_shows = [], []
  for show in Show.query.join(Venue, Venue.id==Show.venue_id):
    if show.start_time < now:
      past_shows.append(show)
    else:
      upcoming_shows.append(show)
  print(venue.shows)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": ''.join(venue.genres).lstrip('{').rstrip('}').split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "image_link": venue.image_link,
    "past_shows": [show.display_dict() for show in past_shows],
    "upcoming_shows": [show.display_dict() for show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  try:
    form = VenueForm()
    new_venue = Venue(name=form.name.data, 
                  city=form.city.data, 
                  state=form.state.data, 
                  address=form.address.data,
                  phone=form.phone.data, 
                  image_link=form.image_link.data,
                  genres=form.genres.data, 
                  facebook_link=form.facebook_link.data,
                  seeking_talent=form.seeking_venue.data=='Yes', 
                  seeking_description=form.seeking_description.data,
                  website = form.website.data)

    db.session.add(new_venue)
    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    db.session.rollback()
    print(e)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    db.session.rollback()
    print(e)
  finally:
    db.session.close()
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = [{
      "id":artist.id,
      "name":artist.name
    } for artist in artists]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_query = request.form.get('search_term', '')
  result = Artist.query.filter(Artist.name.ilike(f'%{search_query}%'))
  response={
    "count": result.count(),
    "data": result
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)

  past_shows = []
  upcoming_shows = []
  now = datetime.now().date()

  for show in Show.query.join(Artist, Artist.id==Show.artist_id):
    if show.start_time < now:
      past_shows.append(show)
    else:
      upcoming_shows.append(show)

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": ''.join(artist.genres).lstrip('{').rstrip('}').split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "facebook_link": artist.facebook_link,
    "image_link": artist.image_link,
    "past_shows": [show.display_dict() for show in past_shows],
    "upcoming_shows": [show.display_dict() for show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "website": artist.website
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  artist_data = {
    "id": artist.id,
    "name": artist.name,
    "genres": ''.join(artist.genres).lstrip('{').rstrip('}').split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "facebook_link": artist.facebook_link,
    "image_link": artist.image_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "website": artist.website
    }

  return render_template('forms/edit_artist.html', form=form, artist=artist_data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    artist.name = form.name.data
    artist.phone = form.phone.data
    artist.state = form.state.data
    artist.city = form.city.data
    artist.genres = form.genres.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    seeking_venue = form.seeking_venue.data == 'Yes'
    seeking_description = form.seeking_description.data
    website = form.website.data
    db.session.commit()
  except Exception as e:
    db.session.rolback()
    print(e)
  finally:
    db.session.close()

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  venue = Venue.query.get(venue_id)
  venue_data={
    "id": venue.id,
    "name": venue.name,
    "genres": ''.join(venue.genres).lstrip('{').rstrip('}').split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "website": artist.website,
    "image_link": venue.image_link,
  }
  
  return render_template('forms/edit_venue.html', form=form, venue=venue_data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    name = form.name.data

    venue.name = name
    venue.genres = form.genres.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.facebook_link = form.facebook_link.data
    venue.website = form.website.data
    venue.image_link = form.image_link.data
    seeking_talent = form.seeking_talent.data == 'Yes'
    seeking_description = form.seeking_description.data
    website = form.website.data
    db.session.commit()
  except Exception as e:
    db.session.rolback()
    print(e)
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    [print (request.form[k] + " key " + k) for k in request.form]
    form = ArtistForm()

    new_artist = Artist(name=form.name.data, 
                    city=form.city.data, 
                    state=form.city.data,
                    phone=form.phone.data, 
                    genres=form.genres.data, 
                    image_link=form.image_link.data, 
                    facebook_link=form.facebook_link.data,
                    seeking_venue=form.seeking_venue.data=='Yes', 
                    seeking_description=form.seeking_description.data,
                    website = form.website.data)

    db.session.add(new_artist)
    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    db.session.rollback()
    print(e)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  return render_template('pages/shows.html', shows=[show.display_dict() for show in Show.query.all()])

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    [print (request.form[k] + " key " + k) for k in request.form]
    form = ShowForm()

    new_show = Show(artist_id=request.form['artist_id'] , 
                  venue_id=request.form['venue_id'] , 
                  start_time=request.form['start_time'])

    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e:
    db.session.rollback()
    print(e)
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
