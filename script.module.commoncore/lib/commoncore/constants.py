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
import kodi
from enum import enum

try:
	if kodi.get_setting('fanart_proxy_remote') == 'true':
		client_host = kodi.get_setting('fanart_proxy_host')
		client_port = kodi.get_setting('fanart_proxy_port')
		client_protocol = kodi.get_setting('fanart_proxy_protocol')
	else:
		client_host = '127.0.0.1'
		client_port = kodi.get_setting('control_port', 'service.fanart.proxy')
		client_protocol = kodi.get_setting('control_protocol', 'service.fanart.proxy')
	BASE_FANART_URL = '%s://%s:%s/api/images' % (client_protocol, client_host, client_port) 
except:
	BASE_FANART_URL = ''
	
DEFAULT_VIEWS = enum(
	DEFAULT= 550, 
	LIST= int(kodi.get_setting('default_list_view')) if kodi.get_setting('default_list_view') else 550, 
	MOVIES= int(kodi.get_setting('default_movie_view')) if kodi.get_setting('default_movie_view') else 550, 
	SHOWS= int(kodi.get_setting('default_show_view')) if kodi.get_setting('default_show_view') else 550, 
	SEASONS= int(kodi.get_setting('default_season_view')) if kodi.get_setting('default_season_view') else 550, 
	EPISODES= int(kodi.get_setting('default_episode_view')) if kodi.get_setting('default_episode_view') else 550,
	STREAMS= int(kodi.get_setting('default_stream_view')) if kodi.get_setting('default_stream_view') else 550, 
)