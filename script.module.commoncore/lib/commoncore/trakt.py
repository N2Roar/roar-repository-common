# -*- coding: utf-8 -*-

'''*
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
*'''

import re
import json
import urllib
import traceback
from datetime import datetime
from commoncore import kodi

ERROR_CODES = {
	400:	"Bad Request - request couldn't be parsed",
	401:	"Unauthorized - OAuth must be provided",
	403:	"Forbidden - invalid API key or unapproved app",
	404:	"Not Found - method exists, but no record found",
	405:	"Method Not Found - method doesn't exist",
	409:	"Conflict - resource already created",
	412:	"Precondition Failed - use application/json content type",
	422:	"Unprocessible Entity - validation errorsS",
	429:	"Rate Limit Exceeded",
	500:	"Server Error",
	501:	"Server Error",
	502:	"Server Error",
	503:	"Service Unavailable - server overloaded (try again in 30s)",
	504:	"Service Unavailable - server overloaded (try again in 30s)",
	520:	"Service Unavailable - Cloudflare error",
	521:	"Service Unavailable - Cloudflare error",
	522:	"Service Unavailable - Cloudflare error",
}

PERIOD_OPTIONS = ["weekly" , "monthly" , "yearly" , "all"]
MEDIA_TYPES = ["movie" , "show" , "episode" , "person" , "list"]
ID_TYPES = ["trakt" , "imdb" , "tmdb" , "tvdb" , "tvrage"]
COMMON_FILTERS = ["query", "years", "genres", "languages", "countries", "runtimes", "ratings"]
MOVIE_FILTERS = COMMON_FILTERS + ["certifications"]
SHOW_FILTERS = COMMON_FILTERS + ["certifications", "networks", "status"]
SHOW_STATUS = ["returning series", "in production", "planned", "canceled", "ended"]
DAYS_TO_GET = 21
SHOW_GENRES = [(u'Action', u'action'), (u'Adventure', u'adventure'), (u'Animation', u'animation'), (u'Anime', u'anime'), (u'Biography', u'biography'), (u'Children', u'children'), (u'Comedy', u'comedy'), (u'Crime', u'crime'), (u'Disaster', u'disaster'), (u'Documentary', u'documentary'), (u'Drama', u'drama'), (u'Eastern', u'eastern'), (u'Family', u'family'), (u'Fantasy', u'fantasy'), (u'Game Show', u'game-show'), (u'History', u'history'), (u'Holiday', u'holiday'), (u'Home And Garden', u'home-and-garden'), (u'Horror', u'horror'), (u'Mini Series', u'mini-series'), (u'Music', u'music'), (u'Musical', u'musical'), (u'Mystery', u'mystery'), (u'News', u'news'),(u'Reality', u'reality'), (u'Romance', u'romance'), (u'Science Fiction', u'science-fiction'), (u'Short', u'short'), (u'Soap', u'soap'), (u'Sports', u'sports'), (u'Superhero', u'superhero'), (u'Suspense', u'suspense'), (u'Talk Show', u'talk-show'), (u'Thriller', u'thriller'), (u'War', u'war'), (u'Western', u'western')]
MOVIE_GENRES = [(u'Action', u'action'), (u'Adventure', u'adventure'), (u'Animation', u'animation'), (u'Anime', u'anime'), (u'Comedy', u'comedy'), (u'Crime', u'crime'), (u'Disaster', u'disaster'), (u'Documentary', u'documentary'), (u'Drama', u'drama'), (u'Eastern', u'eastern'), (u'Family', u'family'), (u'Fan Film', u'fan-film'), (u'Fantasy', u'fantasy'), (u'Film Noir', u'film-noir'), (u'History', u'history'), (u'Holiday', u'holiday'), (u'Horror', u'horror'), (u'Indie', u'indie'), (u'Music', u'music'), (u'Musical', u'musical'), (u'Mystery', u'mystery'), (u'Road', u'road'), (u'Romance', u'romance'), (u'Science Fiction', u'science-fiction'), (u'Short', u'short'), (u'Sports', u'sports'), (u'Superhero', u'superhero'), (u'Suspense', u'suspense'), (u'Thriller', u'thriller'), (u'Tv Movie', u'tv-movie'), (u'War', u'war'), (u'Western', u'western')]
class TraktException(Exception):
	pass
CLIENT_ID = "d4161a7a106424551add171e5470112e4afdaf2438e6ef2fe0548edc75924868"
try:
	AUTH_TOKEN = json.loads(kodi.get_setting('authorization', 'script.trakt'))['access_token']
except:
	AUTH_TOKEN = '' #raise TraktException("Addon: script.trakt required.")


def to_slug(username):
	username = username.strip()
	username = username.lower()
	username = re.sub('[^a-z0-9_]', '-', username)
	username = re.sub('--+', '-', username)
	return username

DB_TYPE = 'MySQL' if kodi.get_setting('database_type') == '1' else 'SQLite'

if DB_TYPE == 'MySQL':
	from commoncore.baseapi import MYSQL_CACHABLE_API, EXPIRE_TIMES
	class BASE_TraktAPI(MYSQL_CACHABLE_API):
		custom_tables = [
			"""CREATE TABLE IF NOT EXISTS `trakt_activities` (
				`id` int(11) NOT NULL AUTO_INCREMENT,
				`activity` VARCHAR(1024) NOT NULL UNIQUE,
				`ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
				PRIMARY KEY(`id`));
			""",
			"""CREATE TABLE IF NOT EXISTS `trakt_activity_cache` (
				`id` int(11) NOT NULL AUTO_INCREMENT,
				`activity` VARCHAR(1024) NOT NULL UNIQUE,
				`cache` LONGBLOB,
				PRIMARY KEY(`id`));
			""",
			"""CREATE TABLE IF NOT EXISTS `search_history` (
				`search_id` int(11) NOT NULL AUTO_INCREMENT,
				`media` varchar(15) DEFAULT "show",
				`query` VARCHAR(255) NOT NULL,
				`ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
				PRIMARY KEY (`search_id`),
				UNIQUE KEY `media_UNIQUE` (`media`,`query`));
			""",
			"""CREATE TABLE IF NOT EXISTS `playback_states` (
				`watched_id` int(11) NOT NULL AUTO_INCREMENT,
				`media` varchar(15) DEFAULT "show",
				`trakt_id` INT(11),
				`current` VARCHAR(15) DEFAULT NULL,
				`total` VARCHAR(15) DEFAULT NULL,
				`watched` TINYINT(1) DEFAULT 0,
				`ids` LONGBLOB,
				`metadata` LONGBLOB,
				`ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
				PRIMARY KEY(`watched_id`),
				UNIQUE KEY `media_UNIQUE` (`media`,`trakt_id`));
			""",
			"""CREATE OR REPLACE VIEW `activity_timestamps` AS 
				SELECT trakt_activities.activity, unix_timestamp(ts) AS ts FROM trakt_activities;
			"""
		]

else:
	from commoncore.baseapi import DB_CACHABLE_API, EXPIRE_TIMES
	class BASE_TraktAPI(DB_CACHABLE_API):
		custom_tables = [
			"""CREATE TABLE IF NOT EXISTS "trakt_activities" (
				"id" INTEGER PRIMARY KEY AUTOINCREMENT,
				"activity" TEXT UNIQUE,
				"ts" TIMESTAMP);
			""",
			"""
			CREATE TABLE IF NOT EXISTS "trakt_activity_cache" (
				"id" INTEGER PRIMARY KEY AUTOINCREMENT,
				"activity" TEXT UNIQUE,
				"cache" TEXT
			);
			""",
			"""
			CREATE TABLE IF NOT EXISTS "search_history" (
				"search_id" INTEGER PRIMARY KEY AUTOINCREMENT,
				"media" TEXT DEFAULT "show",
				"query" TEXT,
				"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				UNIQUE (media, query));
			""",
			"""
			CREATE TABLE IF NOT EXISTS "playback_states" (
				"watched_id" INTEGER PRIMARY KEY AUTOINCREMENT,
				"media" TEXT,
				"trakt_id" TEXT,
				"current" varchar(45) DEFAULT NULL,
				"total" varchar(45) DEFAULT NULL,
				"watched" INTEGER DEFAULT 0,
				"ids" TEXT,
				"metadata" TEXT,
				"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				UNIQUE (media, trakt_id));
			""",
			"""CREATE VIEW "activity_timestamps" AS 
				SELECT trakt_activities.activity,  strftime('%s', ts) AS ts FROM trakt_activities;
			"""
		]
		

class TraktAPI(BASE_TraktAPI):
	default_return_type = 'json'
	timeout = kodi.get_setting('trakt_timeout', addon_id='script.module.commoncore') if kodi.get_setting('trakt_timeout', addon_id='script.module.commoncore') else 5
	base_url = '%s://%s' % (kodi.get_setting('trakt_protocol', addon_id='script.module.commoncore'), kodi.get_setting('trakt_base_url', addon_id='script.module.commoncore'))
	headers = {'Content-Type': 'application/json', 'trakt-api-key': CLIENT_ID, 'trakt-api-version': '2'}
	def authorize(self):
		self.headers.update({'Authorization': 'Bearer %s' % (AUTH_TOKEN)})
		
	def build_url(self, uri, query, append_base):
		if append_base:
			url = self.base_url + uri	
		if query is None:
			query = {}
		query['limit'] = 100
		if 'page' in kodi.args:
			query['page'] = kodi.args['page']
		url += '?' + urllib.urlencode(query)
		return url
	
	def handel_error(self, error, response, request_args, request_kwargs):
		traceback.print_stack()
		if response is None:
			kodi.notify("Trakt Error", "See log file")
			raise error
		elif response.status_code > 499:
			kodi.notify("Temporary Trakt Error", "%s: %s" % (response.status_code, ERROR_CODES[response.status_code]))
			raise TraktException("Temporary Trakt Error <<%s>>: %s" % (response.status_code, ERROR_CODES[response.status_code]))
		else:
			kodi.notify("Trakt Error", "%s: %s" % (response.status_code, ERROR_CODES[response.status_code]))
			raise TraktException("Trakt Error <<%s>>: %s" % (response.status_code, ERROR_CODES[response.status_code]))
	
	def process_response(self, url, response, cache_limit,request_args, request_kwargs):
		total_pages = int(response.headers['X-Pagination-Page-Count']) if 'X-Pagination-Page-Count' in response.headers else 1
		current_page = int(response.headers['X-Pagination-Page']) if 'X-Pagination-Page' in response.headers else 1
		response = {"total_pages": total_pages, "current_page": current_page, "items": response.json()}
		self.cache_response(url, json.dumps(response), cache_limit)
		return response
if DB_TYPE == 'MySQL':
	trakt = TraktAPI(kodi.get_setting('database_mysql_host'), kodi.get_setting('database_mysql_name'), kodi.get_setting('database_mysql_user'), kodi.get_setting('database_mysql_pass'), kodi.get_setting('database_mysql_port'))
else:
	trakt = TraktAPI()

""" Core Functions """

def is_authorized():
	try:
		auth = AUTH_TOKEN != ''
	except:
		auth = False
	return auth

def call(uri, query=None, data=None, append_base=True, headers=None, auth=None, method=None, timeout=5, cache_limit=0):
	return trakt.request(uri, query=query, data=data, append_base=append_base, headers=headers, auth=auth, method=method, timeout=timeout, cache_limit=cache_limit)

def get_genres(media='shows'):
	uri = "/genres/%s" % media
	return trakt.request(uri, cache_limit=EXPIRE_TIMES.WEEK)

def get_certifications(media='shows'):
	uri = "/certifications/%s" % media
	return trakt.request(uri, cache_limit=EXPIRE_TIMES.WEEK)

def get_networks():
	uri = "/networks"
	return trakt.request(uri, cache_limit=EXPIRE_TIMES.WEEK)

def search(query, media):
	if media not in MEDIA_TYPES: raise TraktException("Invalid Media Type")
	uri = '/search/%s' % media
	trakt.execute("REPLACE INTO search_history(media, query) VALUES(?,?)", [media, query])
	trakt.commit()
	return trakt.request(uri, query={'extended': 'full', 'query': query}, auth=True, cache_limit=EXPIRE_TIMES.DAY)

def get_search_history(media):
	return trakt.query("SELECT query FROM search_history WHERE media=? ORDER BY ts DESC LIMIT 15", [media])
	
def lookup(id, id_type, media):
	if id_type not in ID_TYPES: raise TraktException("Invalid ID Type")
	if media not in MEDIA_TYPES: raise TraktException("Invalid Media Type")
	uri ="/search/%s/%s" % (id_type, id)
	return trakt.request(uri, query={'extended': 'full', 'type': media}, auth=True, cache_limit=72)

def _check_activities():
	results = {}
	uri = '/sync/last_activities'
	response = trakt.request(uri, auth=True)
	response=response['items']

	for media in ['movies', 'shows', 'seasons', 'episodes', 'lists']:
		results[media] = {}
		for activity in ['watched_at', 'watchlisted_at', 'updated_at', 'collected_at']:
			if not response: return results
			if activity in response[media]:
				ts = response[media][activity]
				SQL = "SELECT activity FROM activity_timestamps WHERE activity=? AND ts >= ?"
				test = trakt.query(SQL, [activity, ts])
	
				if test:
					results[media][activity] = [True, ts]
				else:
					results[media][activity] = [False, ts]
	return results
	
def _check_activity(media, activity):
	activities = _check_activities()
	if media in activities:
		if activity in activities[media]:
			return activities[media]
	return False

def get_activity(fresh, activity, uri, data=None, params=None, auth=False):
	if fresh[0]:
		results = trakt.query("SELECT cache FROM trakt_activity_cache WHERE activity=?", [activity])
		if results:
			kodi.log('return cached activity: %s' % activity)
			return json.loads(results[0][0])
	kodi.log('request remote activity: %s, %s' % (activity, uri))
	results = trakt.request(uri, query=params, data=data, auth=auth)
	results=results['items']
	if results:
		SQL = "REPLACE INTO trakt_activity_cache(activity, cache) VALUES (?,?)"
		trakt.execute(SQL, [activity, json.dumps(results)])
	if activity.endswith('_at') is False:
		activity = re.sub('_[a-zA-Z0-9]+$', '', activity)
	if DB_TYPE == 'MySQL':
		ts = fresh[1][0:len(fresh[1])-5].replace("T", " ")
		SQL = "REPLACE INTO trakt_activities(activity, ts) VALUES (?, ?)"
		trakt.execute(SQL, [activity, ts])
	else:
		SQL = "REPLACE INTO trakt_activities(activity, ts) VALUES (?, strftime('%s',?))"
		trakt.execute(SQL, [activity, fresh[1]])
	trakt.commit()
	return results

""" History Functions """

def get_watched_history(media):
		uri = '/sync/watched/%s' % media
		a = _check_activities()
		if media == 'shows':
			results = {}
			response = get_activity(a['episodes']['watched_at'], 'watched_at_%s' % media , uri, auth=True)
			if not response: return False
			for r in response:
				trakt_id =  r['show']['ids']['trakt']
				results[trakt_id] = {}
				seasons = r['seasons']
				for season in seasons:
					results[trakt_id][season['number']] = []
					for episode in season['episodes']: results[trakt_id][season['number']].append(episode['number'])
			return results
		else:
			results = []
			response = get_activity(a['movies']['watched_at'], 'watched_at_%s' % media , uri, auth=True)
			if not response: return False
			for r in response:
				results.append(r['movie']['ids']['trakt'])
			return results

def _get_watched_episodes(id):
	a = _check_activities()
	uri = '/sync/history/seasons/%s' % id
	return get_activity(a['episodes']['watched_at'], 'episodes_watched_at_%s' % id , uri, auth=True)

def get_watched_episodes(id, season=None):
	watched = _get_watched_episodes(id)
	temp = {}
	for w in watched:
		season = w['episode']['season']
		if season not in temp: temp[season] = []
		temp[season].append(w['episode']["number"])
	if season is not None and season in temp:
		return temp[season]
	return temp

def get_watched_season(trakt_id, season, season_id):
	watched = []
	for test in _get_watched_episodes(season_id):
		if test['episode']['number'] not in watched: watched.append(test['episode']['number'])
	watched = len(watched)
	episodes = 0
	for test in get_season_info(trakt_id, season)['items']:
		if test['number'] == 0: break
		if test['first_aired'] is None: break
		episodes += 1

	return watched == episodes if episodes > 0 else None

def get_season_watched(id):
	uri = '/sync/history/shows/%s' % id
	response = trakt.request(uri, auth=True)
	watched = {}
	for r in response['items']:
		if r['episode']['season'] not in watched: watched[r['episode']['season']] = []
		watched[r['episode']['season']].append(r['episode']['number'])
	return watched


def is_inprogress(media, trakt_id):
	if trakt.query("SELECT 1 FROM playback_states WHERE media=? AND watched=0 AND trakt_id=?", [media, trakt_id]):
		return True
	else:
		return False

""" Calendars """

def get_my_calendar():
	from datetime import date, timedelta
	d = date.today() - timedelta(days=(DAYS_TO_GET - 1)) 
	today = d.strftime("%Y-%m-%d")
	uri = '/calendars/my/shows/%s/%s' % (today, DAYS_TO_GET)
	return trakt.request(uri, query={'extended': 'full'}, auth=True, cache_limit=EXPIRE_TIMES.TWELVEHOURS)

def get_my_new_shows():
	from datetime import date, timedelta
	d = date.today() - timedelta(days=(DAYS_TO_GET - 1)) 
	today = d.strftime("%Y-%m-%d")
	uri = '/calendars/my/shows/new/%s/%s' % (today, DAYS_TO_GET)
	return trakt.request(uri, query={'extended': 'full'}, auth=True, cache_limit=EXPIRE_TIMES.TWELVEHOURS)

def get_my_season_premieres():
	from datetime import date, timedelta
	d = date.today() - timedelta(days=(DAYS_TO_GET - 1)) 
	today = d.strftime("%Y-%m-%d")
	uri = '/calendars/my/shows/premieres/%s/%s' % (today, DAYS_TO_GET)
	return trakt.request(uri, query={'extended': 'full'}, auth=True, cache_limit=EXPIRE_TIMES.TWELVEHOURS)

""" TV Show Functions"""
def get_show_info(id):
	uri = '/shows/%s' % id
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.THREEDAYS)

def get_show_progress(id):
	uri = '/shows/%s/progress/watched' % id
	return trakt.request(uri, auth=True)

def get_my_watchlist_shows():
	uri = '/sync/watchlist/shows'
	return trakt.request(uri, query={'extended': 'full'}, auth=True)

def get_my_collection_shows():
	uri = '/sync/collection/shows'
	return trakt.request(uri, query={'extended': 'full'}, auth=True)

def get_recommended_shows():
	uri = '/recommendations/shows'
	return trakt.request(uri, query={'extended': 'full'}, auth=True, cache_limit=EXPIRE_TIMES.DAY)

def get_trending_shows(filter=None, filter_value=None):
	query = {'extended': 'full'}
	if filter is not None:
		query[filter] = filter_value
	uri = '/shows/trending'
	return trakt.request(uri, query=query, cache_limit=EXPIRE_TIMES.DAY)

def get_popular_shows():
	uri = '/shows/popular'
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_anticipated_shows():
	uri = '/shows/anticipated'
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_most_played_shows(period=None):
	uri = '/shows/played'
	if period.lower() in PERIOD_OPTIONS: uri += '/' + period.lower()
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_most_watched_shows(period=None):
	uri = '/shows/watched'
	if period.lower() in PERIOD_OPTIONS: uri += '/' + period.lower()
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_most_collected_shows(period=None):
	uri = '/shows/collected'
	if period.lower() in PERIOD_OPTIONS: uri += '/' + period.lower()
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_show_watched_progress(id):
	uri = '/shows/%s/progress/watched' % id
	return trakt.request(uri, query={'hidden': 'false', 'specials': 'false', })

def get_show_people(id):
	uri = '/shows/%s/people' % id
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_related_shows(id):
	uri = '/shows/%s/related' % id
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_next_epidode(id):
	uri = '/shows/%s/next_episode' % id
	return trakt.request(uri, query={'extended': 'full'})

def get_last_epidode(id):
	uri = '/shows/%s/next_episode' % id
	return trakt.request(uri, query={'extended': 'full'})

def get_inprogress_shows():
	return trakt.query("SELECT ids, metadata FROM playback_states WHERE media='episode' AND watched = 0 ORDER BY ts DESC")


""" Season Functions"""

def get_show_seasons(id):
	uri = '/shows/%s/seasons' % id
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.EIGHTHOURS)

def get_season_info(id, season):
	uri = '/shows/%s/seasons/%s' % (id, season)
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.EIGHTHOURS)

""" Episode Functions"""
def get_episode_info(id, season, episode):
	uri = '/shows/%s/seasons/%s/episodes/%s' % (id, season, episode)
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)



""" Movie Functions"""
def get_movie_info(id):
	uri = '/movies/%s' % id
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.THREEDAYS)

def get_my_watchlist_movies():
	uri = '/sync/watchlist/movies'
	return trakt.request(uri, query={'extended': 'full'}, auth=True)

def get_my_collection_movies():
	uri = '/sync/collection/movies'
	return trakt.request(uri, query={'extended': 'full'}, auth=True)

def get_trending_movies(filter=None, filter_value=None):
	query = {'extended': 'full'}
	if filter is not None:
		query[filter] = filter_value
	uri = '/movies/trending'
	return trakt.request(uri, query=query, cache_limit=EXPIRE_TIMES.DAY)

def get_popular_movies():
	uri = '/movies/popular'
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_most_played_movies(period=None):
	uri = '/movies/movies'
	if period.lower() in PERIOD_OPTIONS: uri += '/' + period.lower()
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_most_watched_movies(period=None):
	uri = '/movies/watched'
	if period.lower() in PERIOD_OPTIONS: uri += '/' + period.lower()
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_most_collected_movies(period=None):
	uri = '/movies/collected'
	if period.lower() in PERIOD_OPTIONS: uri += '/' + period.lower()
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_anticipated_movies():
	uri = '/movies/anticipated'
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_movie_people(id):
	uri = '/movies/%s/people' % id
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_related_movies(id):
	uri = '/movies/%s/related' % id
	return trakt.request(uri, query={'extended': 'full'}, cache_limit=EXPIRE_TIMES.DAY)

def get_recommended_movies():
	uri = '/recommendations/movies'
	return trakt.request(uri, query={'extended': 'full'}, auth=True, cache_limit=EXPIRE_TIMES.DAY)

def get_inprogress_movies():
	return trakt.query("SELECT ids, metadata FROM playback_states WHERE media='movie' AND watched = 0 ORDER BY ts DESC")


""" LIST Functions """

def get_liked_lists():
	uri = '/users/likes/lists'
	return trakt.request(uri, auth=True)

def get_custom_lists(username='me'):
	if username == 'me':
		auth = True
	else:
		username = to_slug(username)
		auth = False
	uri = '/users/%s/lists' % username
	return trakt.request(uri, auth=auth)

def get_custom_list(id, media, username='me'):
	if 'show' in media: media = 'show'
	elif 'movie' in media: media = 'movie'
	if username == 'me':	
		uri = '/users/me/lists/%s/items' % id 
		auth = True
	else:
		uri = '/users/%s/lists/%s/items' % (to_slug(username), id)
		auth = False
	temp = trakt.request(uri, auth=auth, cache_limit=0)
	results = {"items": []}
	if not temp: return results
	for r in temp['items']:
		if r['type'] == media:
			results['items'].append(r)
	return results

def add_to_list(media, trakt_id):
	options = ['Watchlist', 'Collection']
	lists = get_custom_lists()
	for li in lists['items']:
		options.append(li['name'])
	c = kodi.dialog_select("Add to list", options)
	if c is False: return
	elif c == 0:
		add_to_watchlist(media,trakt_id)
	elif c == 1:
		add_to_collection(media,trakt_id)
	else:
		slug = lists['items'][c-2]['ids']['slug']
		add_to_custom_list(media, slug, trakt_id)

def add_to_watchlist(media, id, id_type='trakt'):
	if not media.endswith('s'): media += 's'
	uri = '/sync/watchlist'
	post_dict = {media: [{'ids': {id_type: id}}]}
	return trakt.request(uri, data=post_dict, auth=True)

def add_to_collection(media, id, id_type='trakt'):
	if not media.endswith('s'): media += 's'
	uri = '/sync/collection'
	post_dict = {media: [{'ids': {id_type: id}}]}
	return trakt.request(uri, data=post_dict, auth=True)

def delete_from_watchlist(media, id, id_type='trakt'):
	uri = '/sync/watchlist/remove'
	post_dict = {media:  [{'ids': {id_type: id}}]}
	return trakt.request(uri, data=post_dict, auth=True)

def add_to_custom_list(media, slug, id, user='me', id_type='trakt'):
	post_dict = {'shows': [{'ids': {id_type: id}}]}
	uri = '/users/%s/lists/%s/items' % (user, slug)
	return trakt.request(uri, data=post_dict, auth=True)

def remove_from_list(media, list_id, id, user='me', id_type='trakt'):
	if not media.endswith('s'): media += 's'
	post_dict = {'shows': [{'ids': {id_type: id}}]}
	uri = '/users/%s/lists/%s/items/remove' % (user, list_id)
	return trakt.request(uri, data=post_dict, auth=True)

def set_watched_state(media, id, watched, season=None, id_type='trakt'):
	uri = '/sync/history' if watched else '/sync/history/remove'
	if media == 'episode':
		post_dict = {'episodes': [{"ids": {"trakt": id}}]}
	elif media == 'movie':
		post_dict = {'movies': [{"ids": {id_type: id}}]}
	elif media == 'season':
		post_dict = {'shows': [{'seasons': [{'number': int(season)}], 'ids': {id_type: id}}]}
	return trakt.request(uri, data=post_dict, auth=True)

def create_custom_list(title, description=None, private=True, allow_comments=False):
	uri = '/users/me/lists'
	post_dict = {
		"name": title,
		"description": "Created by %s" % kodi.get_name() if description is None else description,
		"privacy": "private",
		"display_numbers": private,
		"allow_comments": allow_comments
	}
	return trakt.request(uri, data=post_dict, auth=True)

def delete_custom_list(id):
	uri = '/users/me/lists/%s' % id
	return trakt.request(uri, auth=True, method='DELETE')

def hide_media(media, section, id):
	uri = '/users/hidden/%s' % section
	post_dict = {"shows": [], "movies":[]}
	if media == 'show':
		post_dict['shows'].append({"ids":{"trakt": id}})
	else:
		post_dict['movies'].append({"ids":{"trakt": id}})
	return trakt.request(uri, data=post_dict, auth=True)



