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
import urllib
from commoncore import kodi

ADDON_ID = 'service.fanart.proxy'
TMDB_KEY = kodi.get_setting('tmdb_api_key', ADDON_ID)
TVDB_KEY =  kodi.get_setting('tvdb_api_key', ADDON_ID)
FANART_KEY =  kodi.get_setting('fanart_api_key', ADDON_ID)
IMDB_KEY =  kodi.get_setting('imdb_api_key', ADDON_ID)
OIMDB_KEY =  kodi.get_setting('oimdb_api_key', ADDON_ID)

class FanartException(Exception):
	pass

def set_art(results, media, url):
	if not results[media]:
		results[media] = url
	return results

def set_complete(result):
	for k,v in result.iteritems():
		if not v: return False
	return True

DB_TYPE = 'MySQL' if kodi.get_setting('database_type') == '1' else 'SQLite'
if DB_TYPE == 'MySQL':
	from commoncore.baseapi import MYSQL_CACHABLE_API, EXPIRE_TIMES
	class BASE_FANART_API(MYSQL_CACHABLE_API):
		default_return_type = 'json'
		headers = {"User-Agent": 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1', "Content-Type": "application/json"}
		custom_tables = [
		"""CREATE TABLE IF NOT EXISTS `id_table` (
				`id` int(11) NOT NULL AUTO_INCREMENT,
				`media` VARCHAR(15),
				`primary_id` VARCHAR(15),
				`id_type` VARCHAR(15),
				`ids` LONGBLOB,
				`ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
				PRIMARY KEY(`id`),
				UNIQUE KEY `media_UNIQUE` (`media`,`primary_id`));
			"""
		]
		
		def __init__(self):
			self.dsn = {
				"database":  kodi.get_setting('database_mysql_name'),
				"host": kodi.get_setting('database_mysql_host'),
				"port": int(kodi.get_setting('database_mysql_port')),
				"user": kodi.get_setting('database_mysql_user'),
				"password": kodi.get_setting('database_mysql_pass'),
				"buffered": True
			}
			self.connect()
		
		def enabled(self):
			return False
		
		def handel_error(self, error, response, request_args, request_kwargs):
			pass
		
else:
	from commoncore.baseapi import DB_CACHABLE_API, EXPIRE_TIMES
	class BASE_FANART_API(DB_CACHABLE_API):
		default_return_type = 'json'
		headers = {"User-Agent": 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1', "Content-Type": "application/json"}
		custom_tables = [
		"""CREATE TABLE IF NOT EXISTS "id_table" (
				"id" INTEGER PRIMARY KEY AUTOINCREMENT,
				"media" TEXT,
				"primary_id" TEXT,
				"id_type" TEXT,
				"ids" TEXT,
				"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				UNIQUE (media, primary_id));
			"""
		]
		
		def enabled(self):
			return False
		
		def handel_error(self, error, response, request_args, request_kwargs):
			pass

class TMDB_API(BASE_FANART_API):
	base_url = "http://api.themoviedb.org/3"
	
	def enabled(self):
		return kodi.get_setting('enable_tmdb', ADDON_ID) == 'true'
	
	def build_url(self, uri, query, append_base):
		if append_base:
			url = self.base_url + uri
		url += '?' + urllib.urlencode({"api_key": TMDB_KEY})
		if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(url)
		return url

	def get_show_art(self, tmdb_id, tvdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		uri = "/tv/%s/images" % tmdb_id
		try:
			response = self.request(uri, cache_limit=EXPIRE_TIMES.WEEK)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
		except:
			return result
		try:
			result['fanart'] = "http://image.tmdb.org/t/p/w1280%s" % response['backdrops'][0]['file_path']
		except: pass
		try:
			result['poster'] = "http://image.tmdb.org/t/p/w1280%s" % response['posters'][0]['file_path']
		except: pass
		return result
	
	def get_movie_art(self, tmdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		uri = "/movie/%s/images" % tmdb_id
		try:
			response = self.request(uri, cache_limit=EXPIRE_TIMES.WEEK)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
		except:
			return result
		try:
			result['fanart'] = "http://image.tmdb.org/t/p/w1280%s" % response['backdrops'][0]['file_path']
		except: pass
		try:
			result['poster'] = "http://image.tmdb.org/t/p/w1280%s" % response['posters'][0]['file_path']
		except: pass
		return result

	def get_episode_art(self, tmdb_id, tvdb_id, imdb_id, season, episode):
		try:
			uri = "/tv/%s/season/%s/episode/%s/images" % (tmdb_id, season, episode)
			response = self.request(uri, cache_limit=EXPIRE_TIMES.DAY)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			if response and 'stills' in response and response['stills']:
				return "http://image.tmdb.org/t/p/w500%s" % response['stills'][0]['file_path']
		except: return False

	def get_person_art(self, tmdb_id):
		try:
			uri = "/person/%s" % tmdb_id
			response = self.request(uri)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			if 'profile_path' in response and response['profile_path'] is not None:
				return "http://image.tmdb.org/t/p/w500%s" % response['profile_path']
		except: return False

class IMDB_API(BASE_FANART_API):
	base_url = 'https://www.imdb.com/'
	default_return_type = 'xml'
	reg_fullsize = re.compile("@+\.([^jpg]+)jpg")
	
	def enabled(self):
		return kodi.get_setting('enable_imdb', ADDON_ID) == 'true'
	
	def get_show_art(self, tmdb_id, tvdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		uri = '/title/%s/mediaindex' % imdb_id
		try:
			xml = self.request(uri, cache_limit=EXPIRE_TIMES.WEEK)
		except:
			return result
		try:
			url = xml.find('img', {"class": "poster"})['src']
			result['poster'] = url.split('._')[0]
		except: pass
		try:
			result['fanart'] = self.reg_fullsize.sub("@",xml.find('img', {"width": "100", "height":"100"})['src'])
		except:
			pass
		return result
	
	def get_movie_art(self, tmdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		uri = '/title/%s/mediaindex' % imdb_id
		try:
			xml = self.request(uri, cache_limit=EXPIRE_TIMES.WEEK)
		except:
			return result
		try:
			result['poster'] = self.reg_fullsize.sub("@@", xml.find('img', {"class": "poster"})['src'])
		except: pass
		try:
			result['fanart'] = self.reg_fullsize.sub("@",xml.find('img', {"width": "100", "height":"100"})['src'])
		except:
			pass
		return result

class OIMDB_API(BASE_FANART_API):
	base_url = 'http://www.omdbapi.com'
	
	def enabled(self):
		return kodi.get_setting('enable_oimdb', ADDON_ID) == 'true'
	
	def get_show_art(self, tmdb_id, tvdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		try:
			response = self.request('/', query={"i": imdb_id, "apikey": OIMDB_KEY})
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			result['poster'] = response['Poster'].split('._')[0]
		except:
			pass
		return result
	
	def get_movie_art(self, tmdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		try:
			response = self.request('/', query={"i": imdb_id, "apikey": OIMDB_KEY})
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			result['poster'] = response['Poster'].split('._')[0]
		except:
			pass
		return result

class IMDBAPI_API(BASE_FANART_API):
	base_url = 'http://imdbapi.net'
	
	def enabled(self):
		return kodi.get_setting('enable_imdbapi', ADDON_ID) == 'true'
	
	def get_show_art(self, tmdb_id, tvdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		try:
			response = self.request('/api', data={"id": imdb_id, "key": IMDB_KEY})
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			result['poster'] = response['poster'].split('._')[0]
		except:
			pass
		return result
	
	def get_movie_art(self, tmdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		try:
			response = self.request('/api', data={"id": imdb_id, "key": IMDB_KEY})
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			result['poster'] = response['poster'].split('._')[0]
		except:
			pass
		return result	

class FANART_API(BASE_FANART_API):
	base_url = "http://webservice.fanart.tv/v3"
	
	def enabled(self):
		return kodi.get_setting('enable_fanart', ADDON_ID) == 'true'
	
	def get_movie_art(self, tmdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		uri = '/movies/%s' % tmdb_id
		try:
			response = self.request(uri, cache_limit=EXPIRE_TIMES.WEEK)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
		except:
			return result
		try:
			result['fanart'] = response['moviebackground'][0]['url']
		except: pass
		try:
			result['poster'] = response['movieposter'][0]['url']
		except: pass
		return result

	def get_show_art(self, tmdb_id, tvdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		uri = '/tv/%s' % tvdb_id
		try:
			response = self.request(uri, cache_limit=EXPIRE_TIMES.WEEK)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
		except:
			return result
		try:
			result['fanart'] = response['showbackground'][0]['url']
		except: pass
		try:
			result['poster'] = response['tvposter'][0]['url']
		except: pass
		return result
		
	def get_season_art(self, tvdb_id):
		result = {}
		uri = '/tv/%s' % tvdb_id
		try:
			response = self.request(uri, cache_limit=EXPIRE_TIMES.WEEK)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
		except:
			return result
		try:
			for poster in response['seasonposter']:
				if poster['lang'] != 'en' or int(poster['season']) in result: continue
				result[int(poster['season'])] = poster['url']
		except:
			pass
		return result
		
class TVDB_API(BASE_FANART_API):
	base_url = "https://api.thetvdb.com"
	def enabled(self):
		return kodi.get_setting('enable_tvdb', ADDON_ID) == 'true'
	
	def authorize(self):
		token = kodi.get_property("TVDB_API_token")
		if not token:
			response = self.request('/login', data={"apikey": TVDB_KEY})
			if 'token' in response:
				token = response['token']
				kodi.set_property("TVDB_API_token", token)
			else:
				response.raise_for_status()
				
		self.headers["Authorization"] = "Bearer %s" % token
	
	def get_show_art(self, tmdb_id, tvdb_id, imdb_id):
		result = {"fanart": "", "poster": ""}
		def sort_art(record):
			return record['ratingsInfo']['average']
		
		uri = "/series/%s/images/query" % tvdb_id
		try:
			response = self.request(uri, query={"keyType": "fanart"}, auth=True, cache_limit=EXPIRE_TIMES.WEEK)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			data = sorted(response['data'], reverse=True, key=lambda k: sort_art(k))
			result["fanart"] = "http://thetvdb.com/banners/" + data[0]['fileName']
		except: pass
		try:
			response = self.request(uri, query={"keyType": "poster"}, auth=True, cache_limit=EXPIRE_TIMES.WEEK)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			data = sorted(response['data'], reverse=True, key=lambda k: sort_art(k))
			result["poster"] = "http://thetvdb.com/banners/" + data[0]['fileName']
		except: pass
		return result

	def get_season_art(self, tvdb_id):
		result = {}
		def sort_art(record):
			return record['ratingsInfo']['average']
		try:
			uri = "/series/%s/images/query" % tvdb_id
			response = self.request(uri, query={"keyType": "season"}, auth=True, cache_limit=EXPIRE_TIMES.WEEK)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			data = sorted(response['data'], reverse=True, key=lambda k: sort_art(k))
			for d in data:
				s = int(d["subKey"])
				if s == 0: continue
				img = "http://thetvdb.com/banners/" + d["fileName"]
				result[s] = img
		except: pass
		return result

	def get_episode_art(self, tmdb_id, tvdb_id, imdb_id, season, episode):
		try:
			uri = '/episodes/%s' % tvdb_id
			response = self.request(uri, auth=True, cache_limit=EXPIRE_TIMES.DAY)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			if response and 'data' in response and response['data']['filename']:
				return 'http://thetvdb.com/banners/_cache/' + response['data']['filename']
		except: return False

class TVMAZE_API(BASE_FANART_API):
	base_url = "http://api.tvmaze.com"
	
	def enabled(self):
		return kodi.get_setting('enable_tvmaze', ADDON_ID) == 'true'
	
	def lookup_id(self, imdb_id):
		uri = '/lookup/shows'
		try:
			r = self.request(uri, query={"imdb": imdb_id}, cache_limit=EXPIRE_TIMES.WEEK)
			return r['id']
		except:
			return False
	
	def get_episode_art(self, tmdb_id, tvdb_id, imdb_id, season, episode):
		try:
			tvmaze_id = self.lookup_id(imdb_id)
			if not tvmaze_id: return False
			uri = "/shows/%s/episodes" % tvmaze_id
			response = self.request(uri, query={"specials": 0}, cache_limit=EXPIRE_TIMES.DAY)
			if kodi.get_setting('enable_fanart_debug')=="true": kodi.log(response)
			season = int(season)
			episode = int(season)
			for e in response:
				if e['season'] == season and e['number'] == episode:
					if e['image'] is not None:
						return e['image']['original']
		except: return False

def get_movie_art(tmdb_id, imdb_id):
	result = {"fanart": "", "poster": ""}
	for klass in [TMDB_API(), FANART_API(), IMDB_API(), OIMDB_API(), IMDBAPI_API()]:
		if 'get_movie_art' in dir(klass) and klass.enabled():
			response = klass.get_movie_art(tmdb_id, imdb_id)
			for k,v in response.iteritems():
				if not result[k] and response[k]:
					result[k] = v
			if set_complete(result):
				break
	return result
	
def get_show_art(tmdb_id, tvdb_id, imdb_id):
	result = {"fanart": "", "poster": ""}
	for klass in [TMDB_API(), TVDB_API(), FANART_API(), IMDB_API(), OIMDB_API(), IMDBAPI_API()]:
		if 'get_show_art' in dir(klass) and klass.enabled():
			response = klass.get_show_art(tmdb_id, tvdb_id, imdb_id)
			for k,v in response.iteritems():
				if not result[k] and response[k]:
					result[k] = v
			if set_complete(result):
				break
	return result

def get_season_art(tvdb_id, season=None):
	result = {}
	for klass in [TVDB_API(), FANART_API()]:
		if 'get_season_art' in dir(klass) and klass.enabled():
			response = klass.get_season_art(tvdb_id)
			for k,v in response.iteritems():
				if k not in result:
					result[k] = v

	if season is not None and season in result:
		return result[season]
	return result

def get_episode_art(tmdb_id, tvdb_id, imdb_id, season, episode):
	screenshot = ''
	for klass in [TMDB_API(), TVDB_API(), TVMAZE_API()]:
		if 'get_episode_art' in dir(klass) and klass.enabled():
			screenshot = klass.get_episode_art(tmdb_id, tvdb_id, imdb_id, season, episode)
			if screenshot: break
	return screenshot

def get_person_art(tmdb_id):
	person = ''
	for klass in [TMDB_API()]:
		if 'get_person_art' in dir(klass) and klass.enabled():
			person = klass.get_person_art(tmdb_id)
			if person: break
	return person

def get_art(media, id, id_type='trakt_id', season=None, episode=None):
	k = id_type.replace("_id", "")
	import json
	from commoncore import trakt
	from commoncore.dispatcher import dispatcher
	DB = BASE_FANART_API()
	try:

		@dispatcher.register('show')
		def show():
			ids = DB.query("SELECT ids FROM id_table WHERE primary_id=? AND media=?", [id, media])
			if ids:
				ids = json.loads(ids[0][0])
			else:
				response = trakt.get_show_info(id)
				ids = response['items']['ids']
				DB.execute("INSERT INTO id_table(media, primary_id, id_type, ids) VALUES(?,?,?,?)", [media, ids[k], id_type, json.dumps(ids)])
				DB.commit()
			return get_show_art(ids['tmdb'], ids['tvdb'], ids['imdb'])
		
		@dispatcher.register('movie')
		def movie():
			ids = DB.query("SELECT ids FROM id_table WHERE primary_id=? AND media=?", [id, media])
			if ids:
				ids = json.loads(ids[0][0])
			else:
				response = trakt.get_movie_info(id)
				ids = response['items']['ids']
				DB.execute("INSERT INTO id_table(media, primary_id, id_type, ids) VALUES(?,?,?,?)", [media, ids[k], id_type, json.dumps(ids)])
				DB.commit()
			return get_movie_art(ids['tmdb'], ids['imdb'])
		
		@dispatcher.register('season')
		def f_season():
			ids = DB.query("SELECT ids FROM id_table WHERE primary_id=? AND media=?", [id, media])
			if ids:
				ids = json.loads(ids[0][0])
			else:
				response = trakt.get_show_info(id)
				ids = response['items']['ids']
				ids['season'] = season
				DB.execute("INSERT INTO id_table(media, primary_id, id_type, ids) VALUES(?,?,?,?)", [media, ids[k], id_type, json.dumps(ids)])
				DB.commit()
			return get_season_art(ids['tvdb'], ids['season'])
		
		@dispatcher.register('episode')
		def f_episode():
			ids = DB.query("SELECT ids FROM id_table WHERE primary_id=? AND media=?", [id, media])
			if ids:
				ids = json.loads(ids[0][0])
			else:
				response = trakt.get_show_info(id)
				ids = response['items']['ids']
				ids['season'] = season
				ids['episode'] = episode
				DB.execute("INSERT INTO id_table(media, primary_id, id_type, ids) VALUES(?,?,?,?)", [media, ids[k], id_type, json.dumps(ids)])
				DB.commit()
			return get_episode_art(ids['tmdb'], ids['tvdb'], ids['imdb'], ids['season'], ids['episode'])
			
		return dispatcher.run(media)

	except:
		raise FanartException
		
	

