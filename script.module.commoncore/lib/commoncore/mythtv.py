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
import requests
from commoncore import kodi

vfs = kodi.vfs
try:
	myth_host = kodi.get_setting('host', 'pvr.mythtv')
	myth_port = kodi.get_setting('wsport', 'pvr.mythtv')
except:
	myth_host = ''
	myth_port = ''
	
_base_url = 'http://%s:%s' % (myth_host, myth_port)
session = requests.Session()

def process_response(response, return_type='xml'):
	if return_type == 'json':
		return json.loads(response)
	elif return_type == 'xml':
		import xml.etree.ElementTree as ET
		if type(response) == unicode:
			response = response.encode("utf-8", errors="ignore")
		return ET.fromstring(response)
	else:
		return response


def search_episodes(title, season, episode):
	uri = '/Dvr/GetRecordedList?Descending=true'
	xml = _call(uri)
	for p in xml.iter('Program'):
		showname = p.find('Title').text
		if showname != title: continue
		test_season = p.find('Season').text
		test_episode = p.find('Episode').text
		if test_season == season and test_episode == episode:
			filename = p.find('FileName').text
			storage = p.find('Recording').find('StorageGroup').text
			url = _base_url + '/Content/GetFile?StorageGroup=%s&FileName=%s' % (storage, filename)
			media = {
				"url": url,
				"size": p.find('FileSize').text,
				"extension": "mpg",
			}
			return media
	
	return False

def search_movies(title, year):
	uri = '/Dvr/GetRecordedList?Descending=true'
	xml = _call(uri)
	for p in xml.iter('Program'):
		if p.find('Title').text == title and p.find('Airdate').text[0:4] == year:
			filename = p.find('FileName').text
			storage = p.find('Recording').find('StorageGroup').text
			url = _base_url + '/Content/GetFile?StorageGroup=%s&FileName=%s' % (storage, filename)
			media = {
				"url": url,
				"size": p.find('FileSize').text,
				"extension": "mpg",
			}
			return media
	return False	


def _call(uri, params={}, data=None, append_base=True, retry=False, method=None):
	headers = {}
	if append_base:
		url = _base_url + uri
	else:
		url = uri

	if data is None:
		response = session.get(url, params=params, headers=headers, timeout=5)
	else:
		response = session.post(url, data, headers=headers, timeout=5)
	if response.status_code in [ requests.codes.ok, 201, 206]:
		return process_response(response.text)
	
	return None	