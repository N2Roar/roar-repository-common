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

import urllib
import traceback
from commoncore import kodi
from commoncore.baseapi import DB_CACHABLE_API as BASE_API, EXPIRE_TIMES

try:
	_username = kodi.get_setting('premiumize_username', 'script.module.scrapecore')
	_password = kodi.get_setting('premiumize_password', 'script.module.scrapecore')
except:
	_username = ''
	_password = ''

class PremiumizeAPI_V1(BASE_API):
	'''
	errors to be expected: 
	* 400 (no valid link) 
	* 401 (login failed) 
	* 402 (payment required - the download would be possible, but the account is not premium) 
	* 403 (forbidden) * 404 (file not found - the file has been deleted by a 3rd party provider) 
	* 428 (hoster currently not available. ) 
	* 502 (unkonwn technical error (most likely from a 3rd party provieder - retry after some minutes, we recomend 3 minutes)) 
	* 503 (temporary technical error, maintenance - retry after some minutes, we recomend 3 minutes), 
	* 509 (fair use limit exhausted - retry after some minutes, we recommend 10 minutes)
	'''
	
	base_url = "https://api.premiumize.me"
	default_return_type = 'json'
	headers = {'Content-Type': 'application/json'}

	def prepair_query(self, query):
		if type(query) is dict:
			query['params[login]'] = _username
			query['params[pass]'] = _password
		else:
			query = {"params[login]": _username, 'params[pass]': _password}
		return query
	
PremiumizeV1 = PremiumizeAPI_V1()
	
class PremiumizeAPI_V2(BASE_API):
	base_url = "https://premiumize.me"
	default_return_type = 'json'
	headers = {'Content-Type': 'application/json'}
	timeout = 5
	def prepair_query(self, query):
		if type(query) is dict:
			query['customer_id'] = _username
			query['pin'] = _password
		else:
			query = {"customer_id": _username, "pin": _password}
		return query
	
	def build_url(self, uri, query, append_base):
		if append_base:
			url = self.base_url + uri
		if query is not None:
			tail = ""
			temp = {}
			for k,v in query.iteritems():
				if type(v) is list:
					key = "&%s[]=" % k
					tail += key + key.join(v)
				else:
					temp[k] = v
			url += '?' + urllib.urlencode(temp)
			url += tail
		return url

PremiumizeV2 = PremiumizeAPI_V2()

def get_hosts(full=False):
	uri = '/pm-api/v1.php'
	try:
		response = PremiumizeV1.request(uri, query={'method': 'hosterlist'}, cache_limit=EXPIRE_TIMES.EIGHTHOURS)
		if full: return response
		else: return [h for h in response['result']['hosters']]
	except:
		return []


def get_account():
	uri = '/pm-api/v1.php'
	response = PremiumizeV1.request(uri, query= {'method': 'accountstatus'})
	return response

def get_download(link):
	uri = '/pm-api/v1.php'
	query = {'method': 'directdownloadlink', "params[link]": link}
	response = PremiumizeV1.request(uri, query=query)
	return response

def check_hashes(hashes):
	uri = '/api/torrent/checkhashes'
	return PremiumizeV2.request(uri, query={"hashes": hashes})

def check_items(items):
	uri = '/api/cache/check'
	return PremiumizeV2.request(uri, query={"items": items})
	
def list_folder(id=''):
	uri = '/api/folder/list'
	return PremiumizeV2.request(uri, query={"id": id, "includebreadcrumbs": "false"})

def get_folder_stream(results):
	content = results['content']
	temp = []
	for c in content:
		if 'type' in c and c['type'] == 'folder': continue
		temp.append(c)
	temp.sort(reverse=True, key=lambda k: k['size'])
	return temp[0]['link']

def create_folder(name, parent=None):
	uri = '/api/folder/create'
	data = {"name": name}
	if parent is not None:
		data['parent'] = parent
	return PremiumizeV2.request(uri, data=data)

def rename_folder(id, name):
	uri = '/api/folder/rename'
	return PremiumizeV2.request(uri, data={"id": id, "name": name})

def delete_folder(id):
	uri = '/api/folder/delete'
	return PremiumizeV2.request(uri, query={"id": id})

def folder_info(id):
	uri = '/api/folder/upload_info'
	return PremiumizeV2.request(uri, data={"id": id})

def upload():
	pass

def item_details(id):
	uri = '/api/item/details'
	return PremiumizeV2.request(uri, query={"id": id})

def delete_item(id):
	uri = '/api/item/delete'
	return PremiumizeV2.request(uri, query={"id": id})

def rename_item(id, name):
	uri = '/api/item/rename'
	return PremiumizeV2.request(uri, data={"id": id, "name": name})
	
def list_transfers():
	uri = '/api/transfer/list'
	return PremiumizeV2.request(uri)

def create_transfer(url, status=False):
	uri = "/api/transfer/create"
	response = PremiumizeV2.request(uri, {"src": url})
	if status:
		return response['status']
	else:
		return response
	
def clear_transfers():
	uri = "/api/transfer/clearfinished"
	return PremiumizeV2.request(uri)





