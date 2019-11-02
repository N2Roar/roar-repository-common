# -*- coding: utf-8 -*-

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

from openscrapers.modules import cache
from openscrapers.modules import cleantitle
from openscrapers.modules import client
from openscrapers.modules import debrid
from openscrapers.modules import source_utils
from openscrapers.modules import workers


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en', 'de', 'fr', 'ko', 'pl', 'pt', 'ru']
        self.domains = ['kickasshydra.net', 'kickasstrusty.com', 'kickassindia.com',
            'kickassmovies.net', 'torrentskickass.org', 'kickasstorrents.li', 'kkat.net',
            'kickassdb.com', 'kickassaustralia.com', 'kickasspk.com', 'kkickass.com',
            'kathydra.com', 'kickasst.org', 'kickasstorrents.id', 'kickasst.net', 'thekat.cc',
            'thekat.ch', 'kickasstorrents.bz', 'kickass-kat.com', 'kickass-usa.com'
        ]
        self._base_link = None
        self.search = '/usearch/{0}%20category:movies'
        self.search2 = '/usearch/{0}%20category:tv'


    @property
    def base_link(self):
        if not self._base_link:
            self._base_link = cache.get(self.__get_base_url, 120, 'https://%s' % self.domains[0])
        return self._base_link


    def movie(self, imdb, title, localtitle, aliases, year):
        if debrid.status(True) is False:
            return

        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except Exception:
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        if debrid.status(True) is False:
            return

        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except Exception:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        if debrid.status(True) is False:
            return

        try:
            if url == None:
                return

            url = urlparse.parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urllib.urlencode(url)
            return url
        except Exception:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            self._sources = []
            self.items = []
            if url == None:
                return self._sources

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

            self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']

            self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']

            query = '%s S%02dE%02d' % (
                data['tvshowtitle'],
                int(data['season']),
                int(data['episode'])) if 'tvshowtitle' in data else '%s %s' % (
                data['title'],
                data['year'])
            query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)
            url = self.search2.format(urllib.quote(query)) if 'tvshowtitle' in data else self.search.format(urllib.quote(query))
            url = urlparse.urljoin(self.base_link, url)

            self._get_items(url)
            self.hostDict = hostDict + hostprDict
            threads = []
            for i in self.items:
                threads.append(workers.Thread(self._get_sources, i))
            [i.start() for i in threads]
            [i.join() for i in threads]
            return self._sources
        except Exception:
            return self._sources


    def _get_items(self, url):
        try:
            headers = {'User-Agent': client.agent()}
            r = client.request(url, headers=headers)
            posts = client.parseDOM(r, 'tr', attrs={'id': 'torrent_latest_torrents'})
            for post in posts:
                data = client.parseDOM(post, 'a', attrs={'title': 'Torrent magnet link'}, ret='href')[0]
                link = urllib.unquote(data).decode('utf8').replace('https://mylink.me.uk/?url=', '').replace('https://mylink.cx/?url=', '')
                name = urllib.unquote_plus(re.search('dn=([^&]+)', link).groups()[0])

                t = name.split(self.hdlr)[0]
                if not cleantitle.get(re.sub('(|)', '', t)) == cleantitle.get(self.title):
                    continue

                # try:
                    # y = re.findall('[\.|\(|\[|\s|\_|\-](S\d+E\d+|S\d+)[\.|\)|\]|\s|\_|\-]', name, re.I)[-1].upper()
                # except:
                    # y = re.findall('[\.|\(|\[|\s\_|\-](\d{4})[\.|\)|\]|\s\_|\-]', name, re.I)[-1].upper()
                # if not y == self.hdlr:
                    # continue

                if self.hdlr not in name:
                    raise Exception()

                try:
                    size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GiB|MiB|GB|MB))', post)[0]
                    div = 1 if size.endswith('GB') else 1024
                    size = float(re.sub('[^0-9|/.|/,]', '', size.replace(',', '.'))) / div
                    size = '%.2f GB' % size
                except:
                    size = '0'
                self.items.append((name, link, size))
            return self.items
        except:
            return self.items


    def _get_sources(self, item):
        try:
            name = item[0]
            url = item[1]
            quality, info = source_utils.get_release_quality(url, name)
            info.append(item[2])
            info = ' | '.join(info)
            self._sources.append({'source': 'Torrent', 'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True})
        except:
            pass


    def resolve(self, url):
        return url


    def __get_base_url(self, fallback):
        try:
            for domain in self.domains:
                try:
                    url = 'https://%s' % domain
                    result = client.request(url, limit=1, timeout='5')
                    result = re.findall('<title>(.+?)</title>', result, re.DOTALL)[0]
                    if result and 'Kickass' in result:
                        return url
                except:
                    pass
        except:
            pass
        return fallback


