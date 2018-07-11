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
import traceback
import requests
from commoncore import kodi
from commoncore.baseapi import DB_CACHABLE_API as BASE_API, EXPIRE_TIMES
from commoncore.enum import enum
from commoncore.basewindow import BaseWindow

CLIENT_ID = 'X245A4XAIBGVM'
class RealDebrid_API(BASE_API):
	base_url = 'https://api.real-debrid.com/rest/1.0'
	default_return_type = 'json'
	headers = {}
	attemp = 0
	timeout = 5
	def authorize(self):
		self.headers = {"Authorization": "Bearer %s" % kodi.get_setting('realdebrid_token', addon_id='script.module.scrapecore')}

	def handel_error(self, error, response, request_args, request_kwargs):
		if response is None: raise error
		if response.status_code == 401 and request_kwargs['auth'] and self.attemp == 0:
			self.attempt = 1
			refresh_token()
			return self.request(*request_args, **request_kwargs)
		else:
			kodi.log(response.status_code)
			kodi.log(response.text)
			
	
RD = RealDebrid_API()
session = requests.Session()

### Authorization ###

def authorize():
	CONTROLS = enum(CLOSE=92000, CODE=91050, PROGRESS=91051)
	class Authorize(BaseWindow):
		_abort = False
		return_val = False
		
		def onInit(self):
			response = request_code()
			self.device_code = response['device_code']
			self.user_code = response['user_code']
			self.timeout = int(response['expires_in'])
			self.getControl(CONTROLS.CODE).setLabel(self.user_code)
			for tick in range(self.timeout, 0,-1):
				if tick == 0 or self._abort: break
				width = (float(tick) / self.timeout) * 596
				self.getControl(CONTROLS.PROGRESS).setWidth(int(width))
				if (tick % 5) == 0:
					r = poll_credentials(self.device_code)
					if r:
						client_id = r['client_id']
						client_secret = r['client_secret']
						token = request_token(client_id, client_secret, self.device_code)
						kodi.set_setting('realdebrid_client_id', client_id, addon_id='script.module.scrapecore')
						kodi.set_setting('realdebrid_client_secret', client_secret, addon_id='script.module.scrapecore')
						kodi.set_setting('realdebrid_token', token['access_token'], addon_id='script.module.scrapecore')
						kodi.set_setting('realdebrid_refresh_token', token['refresh_token'], addon_id='script.module.scrapecore')
						kodi.notify("RealDebrid Authorization", "Success!")
						self._close()
						return
				kodi.sleep(1000)
			self.close()

		def onClick(self, controlID):
			if controlID == CONTROLS.CLOSE: self._close()

		def _close(self):
			self._abort = True
			self.close()
		
	A = Authorize("auth_realdebrid.xml", kodi.get_addon('script.module.scrapecore').getAddonInfo('path').decode('utf-8'))
	A.show()

def poll_credentials(device_code):
	try:	
		r = request_credentials(device_code)
		client_id = r['client_id']
	except: return False	
	return r

def request_code():
	url = 'https://api.real-debrid.com/oauth/v2/device/code'
	query = {"client_id": CLIENT_ID, "new_credentials": "yes"}
	response = session.get(url, params=query)
	return response.json()

def request_credentials(device_code):
	url = 'https://api.real-debrid.com/oauth/v2/device/credentials'
	query = {"client_id": CLIENT_ID, "code": device_code}
	response = session.get(url, params=query)
	return response.json()

def request_token(client_id, client_secret, code):
	url = 'https://api.real-debrid.com/oauth/v2/token'
	data = {'client_id': client_id, 'client_secret': client_secret, 'code': code, 'grant_type': 'http://oauth.net/grant_type/device/1.0'}
	response = session.post(url, data=data)
	return response.json()

def refresh_token():
	url = 'https://api.real-debrid.com/oauth/v2/token'
	data = {'client_id': kodi.get_setting('realdebrid_client_id', addon_id='script.module.scrapecore'), 'client_secret': kodi.get_setting('realdebrid_client_secret', addon_id='script.module.scrapecore'), 'code': kodi.get_setting('realdebrid_refresh_token', addon_id='script.module.scrapecore'), 'grant_type': 'http://oauth.net/grant_type/device/1.0'}
	response = session.post(url, data=data)
	response.json()
	if 'access_token' in response:
		kodi.set_setting('realdebrid_token', response['access_token'], addon_id='script.module.scrapecore')
	return response		

### Hosts ###

def get_hosts(full=False):
	uri = '/hosts'
	results = RD.request(uri, cache_limit=EXPIRE_TIMES.EIGHTHOURS)
	if full: return results
	else: return [h for h in results][1:-1]
list_hosts = get_hosts

def get_domains():
	uri = '/hosts/domains'
	response = RD.request(uri, cache_limit=EXPIRE_TIMES.EIGHTHOURS)
	return response
list_domains = get_domains

def host_status():
	uri = '/hosts/status'
	response = RD.request(uri, auth=True, cache_limit=EXPIRE_TIMES.FOURHOURS)
	return response

def host_regex():
	uri = '/hosts/regex'
	response = RD.request(uri, auth=True, cache_limit=EXPIRE_TIMES.FOURHOURS)
	return response

### Traffic ###

def get_traffic_limits():
	uri = '/traffic'
	response = RD.request(uri, auth=True, cache_limit=EXPIRE_TIMES.FOURHOURS)
	return response

def get_usage():
	uri = '/traffic/info'
	response = RD.request(uri, auth=True, cache_limit=EXPIRE_TIMES.HOUR)
	return response

### Downloads ###

def list_downloads(page=1):
	uri = '/downloads'
	response = RD.request(uri, query={"page": page}, auth=True)
	return response

def delete_download(id):
	uri = '/downloads/delete/%s' % id
	RD.request(uri, auth=True, method='DELETE')

### Torrents ###

def list_torrents():
	uri = '/torrents'
	response = RD.request(uri, auth=True)
	return response

def check_hashes(hashes):
	uri = '/torrents/instantAvailability/' + '/'.join(hashes)
	response = RD.request(uri, auth=True)
	return response

def get_torrent_info(torrent_id):
	uri = '/torrents/info/' + torrent_id
	response = RD.request(uri, auth=True)
	return response

def add_torrent(source):
	if source[0:6] == 'magnet':
		return add_magnet_url(source)
	else:
		return add_torrent_url(source)
	
def add_magnet_url(magnet_url):
	uri = '/torrents/addMagnet'
	post_data = {'magnet': magnet_url, 'host': 'real-debrid.com'}
	return RD.request(uri, data=post_data, auth=True, encode_data=False)

def add_torrent_url(torrent_url):
	uri = '/torrents/addTorrent'
	response = requests.get(torrent_url, stream=True)
	if response.status_code == requests.codes.ok or response.status_code == 201:
		data = b''
		for block in response.iter_content(chunk_size=8096):
			if not block: break
			data += block
		RD.request(uri, query={'host': 'real-debrid.com'}, data=data, auth=True, method='PUT')

def delete_torrent(id):
	uri = '/torrents/delete/%s' % id
	RD.request(uri, auth=True, method='DELETE')

def get_stream_file(files):
	id = False
	files.sort(reverse=True, key=lambda k: k['bytes'])
	re_ext = re.compile("(flv)|(avi)|(mpg)|(mpeg)|(mp4)|(mkv)$")
	for f in files:
		if re_ext.search(f['path'], re.IGNORECASE):
			return f['id']
	return id

def select_torrent_files(torrent_id, file_ids):
	uri = '/torrents/selectFiles/' + torrent_id
	if type(file_ids) is list:
		files = ','.join(file_ids)
	else:
		files = file_ids
	RD.request(uri, data={"files": str(files)}, auth=True, encode_data=False)

### Unrestrict ###

def verify_link(link):
	uri = '/unrestrict/check'
	post_data= {'link': link}
	response = RD.request(uri, data=post_data, cache_limit=EXPIRE_TIMES.EIGHTHOURS)
	return response

def unrestrict_link(link):
	uri = '/unrestrict/link'
	post_data= {'link': link}
	response = RD.request(uri, data=post_data, auth=True, encode_data=False)
	return response

def resolve_url(link):
	resolved_url = ''
	response = unrestrict_link(link)
	if response and 'download' in response:
		return response['download']
	else: 
		return ''

