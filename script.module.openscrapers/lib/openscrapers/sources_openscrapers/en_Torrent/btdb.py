# -*- coding: utf-8 -*-
# modified by Venom for Openscrapers

#  ..#######.########.#######.##....#..######..######.########....###...########.#######.########..######.
#  .##.....#.##.....#.##......###...#.##....#.##....#.##.....#...##.##..##.....#.##......##.....#.##....##
#  .##.....#.##.....#.##......####..#.##......##......##.....#..##...##.##.....#.##......##.....#.##......
#  .##.....#.########.######..##.##.#..######.##......########.##.....#.########.######..########..######.
#  .##.....#.##.......##......##..###.......#.##......##...##..########.##.......##......##...##........##
#  .##.....#.##.......##......##...##.##....#.##....#.##....##.##.....#.##.......##......##....##.##....##
#  ..#######.##.......#######.##....#..######..######.##.....#.##.....#.##.......#######.##.....#..######.

'''
    OpenScrapers Project
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
'''

import re
import urllib
import urlparse

from openscrapers.modules import cleantitle
from openscrapers.modules import client
from openscrapers.modules import debrid
from openscrapers.modules import source_utils
from openscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['btdb.io', 'btdb.eu']
		# self.base_link = 'https://btdb.eu'
		# self.search_link = '/?s=%s' # still works but may become deprecated
		self.base_link = 'https://btdb.io'
		self.search_link = '/search/%s/?sort=popular'
		self.min_seeders = 1


	def movie(self, imdb, title, localtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url is None:
				return
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(url)
			return url
		except:
			return


	def sources(self, url, hostDict, hostprDict):
		self.sources = []
		try:
			if url is None:
				return self.sources

			if debrid.status() is False:
				return self.sources

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU')

			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
			self.year = data['year']

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)

			urls = []
			url = self.search_link % urllib.quote_plus(query)
			url = urlparse.urljoin(self.base_link, url)
			urls.append(url)
			urls.append(url + '&page=2')
			# log_utils.log('urls = %s' % urls, log_utils.LOGDEBUG)

			threads = []
			for url in urls:
				threads.append(workers.Thread(self._get_sources, url))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources

		except:
			source_utils.scraper_error('BTDB')
			return self.sources


	def _get_sources(self, url):
		try:
			r = client.request(url)
			posts = client.parseDOM(r, 'div', attrs={'class': 'media'})

			for post in posts:
				# file_name = client.parseDOM(post, 'span', attrs={'class': 'file-name'}) # file_name and &dn= differ 25% of the time.  May add check
				try:
					seeders = int(re.findall(r'Seeders\s+:\s+<strong class="text-success">(.*?)</strong>', post, re.DOTALL)[0].replace(',', ''))
					if self.min_seeders > seeders:
						return
				except:
					pass

				link = re.findall('<a href="(magnet:.+?)"', post, re.DOTALL)

				for url in link:
					url = url.replace('&amp;', '&').replace(' ', '.')
					url = url.split('&tr')[0]

					name = url.split('&dn=')[1]
					name = urllib.unquote_plus(name)
					if source_utils.remove_lang(name):
						continue

					if name.startswith('www'):
						try:
							name = re.sub(r'www(.*?)\W{2,10}', '', name)
						except:
							name = name.split('-.', 1)[1].lstrip()

					t = name.split(self.hdlr)[0].replace(self.year, '').replace('(', '').replace(')', '').replace('&', 'and').replace('.US.', '.').replace('.us.', '.')
					if cleantitle.get(t) != cleantitle.get(self.title):
						continue

					if self.hdlr not in name:
						continue

					quality, info = source_utils.get_release_quality(url)

					try:
						size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', post)[0]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
						pass

					info = ' | '.join(info)

					self.sources.append({'source': 'torrent', 'quality': quality, 'language': 'en', 'url': url,
													'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
		except:
			source_utils.scraper_error('BTDB')
			pass


	def resolve(self, url):
		return url