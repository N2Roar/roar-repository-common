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

import sys
import re
import json
import kodi
import time
from constants import BASE_FANART_URL

def execute_api(namespace, api):
	try:
		if 'args' not in api or api['args'] is None: args = ()
		else: args = list(api['args'])
		if 'kwargs' not in api or api['kwargs'] is None: kwargs = {}
		else: kwargs = api['kwargs']
		if api['name'] == 'premiumize':
			from commoncore import premiumize
			namespace = locals()
		elif api['name'] == 'trakt':
			from commoncore import trakt
			namespace = locals()
		return getattr(namespace[api['name']], api['method'])(*args, **kwargs)
	except Exception, e:
		import traceback
		traceback.print_exc()
		kodi.handel_error("API Error", "Invalid API or Method")
		raise e("Invalid API or Method")

def utf8(string):
	try: 
		string = u'' + string
	except UnicodeEncodeError:
		string = u'' + string.encode('utf-8')
	except UnicodeDecodeError:
		string = u'' + string.decode('utf-8')
	return string

def format_size(num, suffix='B', split=False):
	num = float(num)
	for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
		if abs(num) < 1024.0:
			if split: return num, unit, suffix
			return "%3.1f %s%s" % (num, unit, suffix)
		num /= 1024.0
	if split: return num, unit, suffix
	return "%.1f %s%s" % (num, 'Y', suffix)

def size_to_bytes(num, unit='B'):
	unit = unit.upper()
	if unit.endswith('B'): unit = unit[:-1]
	units = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']
	try: mult = pow(1024, units.index(unit))
	except: mult = sys.maxint
	return int(float(num) * mult)

def format_time(seconds):
	seconds = int(seconds)
	minutes, seconds = divmod(seconds, 60)
	if minutes > 60:
		hours, minutes = divmod(minutes, 60)
		return "%02d:%02d:%02d" % (hours, minutes, seconds)
	else:
		return "%02d:%02d" % (minutes, seconds)

re_color = re.compile("(\[COLOR\s+[a-zA-Z]+\]|\[\/COLOR\])")
def format_color(string, color):
	string = re_color.sub('', string)
	return "[COLOR %s]%s[/COLOR]" % (color, string)

def highlight(string, subject, color):
	formated = "[COLOR %s]%s[/COLOR]" % (color, subject)
	return re.sub(subject, formated, string, re.IGNORECASE)

def format_trailer(trailer_url):
	if not trailer_url: return trailer_url
	match = re.search('\?v=(.*)', trailer_url)
	if match:
		return 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % (match.group(1))	

def make_people(item):
	people={}
	if 'people' in item: people['cast']=[actor['name'] for actor in item['people']['actors'] if actor['name']]
	if 'people' in item: people['castandrole']=['%s as %s' % (actor['name'],actor['character']) for actor in item['people']['actors'] if actor['name'] and actor['character']]
	if 'people' in item and 'directors' in item['people']: people['director']=', '.join([director['name'] for director in item['people']['directors']])
	if 'people' in item and 'writers' in item['people']: people['writer']=', '.join([writer['name'] for writer in item['people']['writers']])
	return people

def make_season_infolabel(item, ids, watched=False):
	if type(ids) is str: ids = json.loads(ids)
	if item['number'] == 0: return False
	info = {}
	if 'ids' in item:
		if 'imdb' in item['ids']: info['code']=info['imdbnumber']=info['imdb_id']=item['ids']['imdb']
		if 'tmdb' in item['ids']: info['tmdb_id']=item['ids']['tmdb']
		if 'tvdb' in item['ids']: info['tvdb_id']=item['ids']['tvdb']
		if 'tvrage' in item['ids']: info['tvrage_id']=item['ids']['tvrage']
		if 'trakt' in item['ids']: info['trakt_id']=item['ids']['trakt']
		if 'slug' in item['ids']: info['slug']=item['ids']['slug']
	info['title']=item['title']
	if 'title' in item: info['title'] = item['title']
	if 'number' in item: info['season'] = item['number']
	if 'rating' in item: info['rating']=item['rating']
	if 'votes' in item: info['votes']=item['votes']
	if 'aired_episodes' in item: info['AiredEpisodes']=item['aired_episodes']
	if 'episode_count' in item: info['TotalEpisodes']=item['episode_count']
	if 'aired_episodes' in item and 'episode_count' in item:
		info['UnAiredEpisodes'] = int(info['TotalEpisodes']) - int(info['TotalEpisodes'])
	if 'first_aired' in item:
		try:
			aired = time.strptime(item['first_aired'], "%Y-%m-%dT%H:%M:%S.000Z")
			info['aired']=info['premiered']=time.strftime('%Y-%m-%d', aired)
		except:
			info['aired']=info['premiered'] = ''
	if watched:
		info['overlay'] = 7
		info['playcount'] = 1
	else:
		info['overlay'] = 6
		info['playcount'] = 0
	if BASE_FANART_URL:
		info['poster'] = BASE_FANART_URL + '/season?season=%s&tvdb_id=%s' % (info['season'], ids['tvdb'])
		info['fanart'] = BASE_FANART_URL + '/show?image=fanart&tvdb_id=%s&tmdb_id=%s&imdb_id=%s' % (ids['tvdb'], ids['tmdb'], ids['imdb'])
	else:
		info['poster'] = ''
		info['fanart'] = ''
	return info
		
def make_infolabel(media, item, show=[], watched=[], ids=None):
	if ids is not None:
		if type(ids) is str: ids = json.loads(ids)
	else:
		ids = {}
	if media in item: item = item[media]
	if 'items' in show: show = show['items']
	info={}
	if 'ids' in item:
		if 'imdb' in item['ids']: info['code']=info['imdbnumber']=info['imdb_id']=item['ids']['imdb']
		if 'tmdb' in item['ids']: info['tmdb']=info['tmdb_id']=item['ids']['tmdb']
		if 'tvdb' in item['ids']: info['tvdb']=info['tvdb_id']=item['ids']['tvdb']
		if 'tvrage' in item['ids']: info['tvrage_id']=item['ids']['tvrage']
		if 'trakt' in item['ids']: info['trakt_id']=item['ids']['trakt']
		if 'slug' in item['ids']: info['slug']=item['ids']['slug']
	info['title']=item['title']
	
	if 'overview' in item: info['plot']=info['plotoutline']=item['overview']
	if 'runtime' in item: info['duration']=item['runtime']
	if 'certification' in item: info['mpaa']=item['certification']
	if 'year' in item: info['year']=item['year']
	if 'season' in item: info['season']=item['season']
	if 'episode' in item: info['episode']=item['episode']
	if 'number' in item: info['episode']=item['number']
	if 'genres' in item: info['genre']=', '.join(item['genres'])
	if 'network' in item: info['studio']=item['network']
	if 'status' in item: info['status']=item['status']
	if 'tagline' in item: info['tagline']=item['tagline']
	if 'watched' in item and item['watched']: info['playcount']=1
	if 'plays' in item and item['plays']: info['playcount']=item['plays']
	if 'rating' in item: info['rating']=item['rating']
	if 'votes' in item: info['votes']=item['votes']
	info['overlay'] = 6
	info['playcount'] = 0
	info['poster'] = ''
	info['fanart'] = ''
	
	if media == 'show':
		item['DBTYPE'] = 'show'
		if 'first_aired' in item:
			try:
				aired = time.strptime(item['first_aired'], "%Y-%m-%dT%H:%M:%S.000Z")
				info['air_date']=info['premiered']=time.strftime('%Y-%m-%d', aired)
			except:
				info['air_date'] = ''
		if BASE_FANART_URL:
			info['poster'] = BASE_FANART_URL + '/show?image=poster&tvdb_id=%s&tmdb_id=%s&imdb_id=%s' % (info['tvdb_id'], info['tmdb_id'], info['imdb_id'])
			info['fanart'] = BASE_FANART_URL + '/show?image=fanart&tvdb_id=%s&tmdb_id=%s&imdb_id=%s' % (info['tvdb_id'], info['tmdb_id'], info['imdb_id'])
	elif media == 'movie':
		item['DBTYPE'] = 'movie'
		if info['trakt_id'] in watched:
			info['overlay'] = 7
			info['playcount'] = 1
		if 'released' in item: info['premiered'] = item['released']
		if BASE_FANART_URL:
			info['poster'] = BASE_FANART_URL + '/movie?image=poster&imdb_id=%s&tmdb_id=%s' % (info['imdb_id'], info['tmdb_id'])
			info['fanart'] = BASE_FANART_URL + '/movie?image=fanart&imdb_id=%s&tmdb_id=%s' % (info['imdb_id'], info['tmdb_id'])
	elif media == 'episode':
		item['DBTYPE'] = 'episode'
		if 'title' in show: info['tvshowtitle']=info['TVShowTitle']=info['showtitle'] = show['title']
		if 'year' in show: info['year'] = show['year']
		if 'number' in item and item['number'] == 0: return False
		if 'first_aired' in item:
			try:
				aired = time.strptime(item['first_aired'], "%Y-%m-%dT%H:%M:%S.000Z")
				info['air_date']=info['premiered']=time.strftime('%Y-%m-%d', aired)
				info['aired'] = 1 if time.mktime(aired) < time.time() else 0
			except:
				info['air_date'] = ''
				info['aired'] = 0
				
		try:
			if info['episode'] in watched[ids['trakt']][info['season']]:
				info['overlay'] = 7
				info['playcount'] = 1
		except: pass
		if BASE_FANART_URL:
			info['poster'] = BASE_FANART_URL + '/episode?tvdb_id=%s&tmdb_id=%s&imdb_id=%s&season=%s&episode=%s' % (info['tvdb_id'], ids['tmdb'], ids['imdb'], info['season'], info['episode'])
			info['fanart'] = BASE_FANART_URL + '/show?image=fanart&tvdb_id=%s&tmdb_id=%s' % (ids['tvdb'], ids['tmdb'])
		
	if 'trailer' in item: info['trailer'] = format_trailer(item['trailer'])
	info.update(make_people(item))

	return info
