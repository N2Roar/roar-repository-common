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

import os
import sys
import xbmc
import json
import random
import xbmcgui
import xbmcaddon
import xbmcplugin
import zlib
import urllib
import urlparse
import vfs
import traceback
from logging import log

try:
	import cPickle as _pickle
except:
	import pickle  as _pickle

pickle = _pickle.dumps
mode='main'
args = {}
__dispatcher = {}
__args = {}
__kwargs = {}

addon = xbmcaddon.Addon()
__get_setting = addon.getSetting
__set_setting = addon.setSetting
show_settings = addon.openSettings
sleep = xbmc.sleep
get_condition_visiblity = xbmc.getCondVisibility

PLATFORM = sys.platform
ARTWORK = vfs.join(addon.getAddonInfo('path').decode('utf-8'), 'resources/artwork')
def unpickle(pickled):
	try:
		return _pickle.loads(pickled)
	except TypeError:
		return _pickle.loads(str(pickled))

def save_data(file, data, format='pickle', compress=False):
	if format == 'pickle':
		if compress:
			data =  zlib.compress(pickle(data))
		else:
			data = pickle(data)
		vfs.write_file(file, data, mode='b')
	else:
		data = json.dumps(data)
		if compress:
			data = zlib.compress(data)
		vfs.write_file(file, data)
	
	 
def load_data(file, format='pickle', compress=False):
	if format == 'pickle':
		try:
			data = vfs.read_file(file, mode='b')
			if compress:
				data = zlib.decompress(data)
			return unpickle(data)
		except Exception, e:
			return None
	else:
		try:
			data = vfs.read_file(file)
			if compress:
				data = zlib.decompress(data)
			return json.loads()
		except Exception, e:
			return None


try:
	HANDLE_ID = int(sys.argv[1])
	ADDON_URL = sys.argv[0]
	PLUGIN_URL = sys.argv[0] + sys.argv[2]
except:
	HANDLE_ID = -1
	ADDON_URL = 'plugin://%s' % addon.getAddonInfo('name')
	PLUGIN_URL = 'plugin://%s' % addon.getAddonInfo('name')

def get_kodi_version():
	full_version_info = xbmc.getInfoLabel('System.BuildVersion')
	return int(full_version_info.split(".")[0])

def exit():
	sys.exit()

def get_addon(addon_id):
	return xbmcaddon.Addon(addon_id)

def has_addon(addon_id):
	return get_condition_visiblity("System.HasAddon(%s)" % addon_id)==1

def get_window(id=10000):
	return xbmcgui.Window(id)

def open_settings(addon_id=None):
	if not addon_id or addon_id is None:
		show_settings()
	else:
		get_addon(addon_id).openSettings()

def get_setting(k, addon_id=None):
	if addon_id is None:
		return __get_setting(k)
	else:
		return xbmcaddon.Addon(addon_id).getSetting(k)

def set_setting(k, v, addon_id=None):
	if not isinstance(v, basestring): v = str(v)
	if addon_id is None:
		return __set_setting(k, v)
	else:
		return xbmcaddon.Addon(addon_id).setSetting(k, v)

def get_property(k, id=None):
	if id is None: id = get_id()
	p = get_window().getProperty('%s.%s' % (id, k))
	if p.lower() == 'false': return False
	if p.lower() == 'true': return True
	return p
	
def set_property(k, v, id=None):
	if id is None: id = get_id()
	get_window().setProperty('%s.%s' % (id, k), str(v))

def clear_property(k, id=None):
	if id is None: id = get_id()
	get_window().clearProperty('%s.%s' % (id, k) + k)

def set_trakt_ids(ids):
	trakt_ids = {}
	for k in ['tmdb', 'tvdb', 'imdb', 'slug', 'trakt']:
		if k in ids:
			trakt_ids[k] = ids[k]
		elif k + '_id' in ids:
			trakt_ids[k] = ids[k + '_id']	
	get_window().setProperty('script.trakt.ids', json.dumps(trakt_ids))
	
def unset_trakt_ids():
	get_window().clearProperty('script.trakt.ids')


def parse_query(query, q={'mode': 'main'}):
	if query.startswith('?'): query = query[1:]
	queries = urlparse.parse_qs(query)
	for key in queries:
		if len(queries[key]) == 1:
			q[key] = queries[key][0]
		else:
			q[key] = queries[key]
	return q
try:
	args = parse_query(sys.argv[2])
	mode = args['mode']
except:
	args = {"mode": "main"}

def arg(k, default=None, decode=None):
	return_val = default
	if k in args:
		v = args[k]
		if v == '': return default
		if v == 'None': return default
	else:
		return default
	if decode == 'json':
		return json.loads(v)
	return v
	
def get_arg(k, default=None):
	return arg(k, default)

def get_current_url():
	return str(sys.argv[0]) + str(sys.argv[2])

def get_path():
	return addon.getAddonInfo('path').decode('utf-8')

def get_profile():
	return addon.getAddonInfo('profile').decode('utf-8')

def translate_path(path):
	return xbmc.translatePath(path).decode('utf-8')

def get_version():
	return addon.getAddonInfo('version')

def get_id():
	return addon.getAddonInfo('id')

def get_name():
	return addon.getAddonInfo('name')

def get_plugin_url(queries, addon_id=None):
	for k,v in queries.iteritems():
		if type(v) is dict:
			queries[k] = json.dumps(v)
		
	try:
		query = urllib.urlencode(queries)
	except UnicodeEncodeError:
		for k in queries:
			if isinstance(queries[k], unicode):
				queries[k] = queries[k].encode('utf-8')
		query = urllib.urlencode(queries)
	addon_id = sys.argv[0] if addon_id is None else addon_id
	return addon_id + '?' + query

def refresh(plugin_url=None):
	query = get_property('search.query')
	if query:
		set_property('search.query.refesh', query)
		clear_property('search.query')
		
	if plugin_url is None:
		xbmc.executebuiltin("Container.Refresh")
	else:
		xbmc.executebuiltin("Container.Refresh(%s)" % plugin_url)
		
def exit():
	exit = xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
	return exit

def kodi_json_request(method, params, id=1):
	if type(params) is not dict:
		from ast import literal_eval
		params = literal_eval(params)
	jsonrpc =  json.dumps({ "jsonrpc": "2.0", "method": method, "params": params, "id": id })
	response = json.loads(xbmc.executeJSONRPC(jsonrpc))
	return response

def run_command(cmd):
	return xbmc.executebuiltin(cmd)

def build_plugin_url(queries, addon_id=None):
	return get_plugin_url(queries, addon_id)

def execute_url(plugin_url):
	cmd = 'XBMC.RunPlugin(%s)' % (plugin_url) 
	run_command(cmd)

def execute_script(script):
	cmd = 'XBMC.RunScript(%s)' % (script)
	run_command(cmd)

def execute_addon(addon_id):
	cmd = 'XBMC.RunAddon(%s)' % addon_id
	run_command(cmd) 

def navigate_to(query):
	plugin_url = build_plugin_url(query)
	go_to_url(plugin_url)

def go_to_url(plugin_url):
	cmd = "XBMC.Container.Update(%s)" % plugin_url
	xbmc.executebuiltin(cmd)

def install_addon(addon_id):
	cmd = "RunPlugin(plugin://%s)" % addon_id
	run_command(cmd)

def play_url(plugin_url, isFolder=False):
	if isFolder:
		cmd = 'XBMC.PlayMedia(%s,True)' % (plugin_url)
	else:
		cmd = 'XBMC.PlayMedia(%s)' % (plugin_url)
	run_command(cmd)


def dialog_ok(title="", m1="", m2="", m3=""):
	dialog = xbmcgui.Dialog()
	dialog.ok(title, m1, m2, m3)

def open_busy_dialog():
	xbmc.executebuiltin( "ActivateWindow(busydialog)" )

def close_busy_dialog():
	xbmc.executebuiltin( "Dialog.Close(busydialog)" )

def notify(title, message, timeout=1500, image=vfs.join(get_path(), 'icon.png')):
	cmd = "XBMC.Notification(%s, %s, %s, %s)" % (title.encode('utf-8'), message.encode('utf-8'), timeout, image)
	xbmc.executebuiltin(cmd)

def handel_error(title, message, timeout=3000):
	image=vfs.join(ARTWORK, 'error.png')
	cmd = "XBMC.Notification(%s, %s, %s, %s)" % (title.encode('utf-8'), message.encode('utf-8'), timeout, image)
	xbmc.executebuiltin(cmd)
	sys.exit()

def dialog_file_browser(title, mask='', path='/'):
	dialog = xbmcgui.Dialog()
	return dialog.browseSingle(1, title, 'files', mask, False, False, path)
	

def dialog_input(title, default=''):
	kb = xbmc.Keyboard(default, title, False)
	kb.doModal()
	if (kb.isConfirmed()):
		text = kb.getText()
		if text != '':
			return text
	return None	

def dialog_textbox(heading, content):
		TextBox().show(heading, content)

def dialog_context(options):
	dialog = xbmcgui.Dialog()
	index = dialog.contextmenu(options)
	if index >= 0:
		return index
	else: 
		return False

def dialog_select(heading, options):
	dialog = xbmcgui.Dialog()
	index = dialog.select(heading, options)
	if index >= 0:
		return index
	else: 
		return False

def multi_select(heading, options, selected=[]):
	from commoncore.basewindow import BaseWindow
	from commoncore.enum import enum
	CONTROLS = enum(CLOSE=82000, LIST=85001, TITLE=85005, CANCEL=85011, OK=85012)
	skin_path = vfs.join("special://home/addons", "script.module.commoncore/")
	class MultiSelect(BaseWindow):
		def __init__(self, *args, **kwargs):
			BaseWindow.__init__(self)
			self.return_val = []
	
		def onInit(self):
			for c in options:
				if type(c) is tuple:
					t,v = c
					liz = xbmcgui.ListItem(t, iconImage='')
					liz.setProperty("value", v)
				elif type(c) is list:
					t = c[0]
					v = c[1]
				else:
					t = c
					v = options.index(c)
				liz = xbmcgui.ListItem(t, iconImage='')
				liz.setProperty("value", str(v))
				if options.index(c) in selected:
					liz.setProperty("selected", "checked.png")
				self.getControl(CONTROLS.LIST).addItem(liz)
			self.getControl(CONTROLS.TITLE).setLabel(heading)
			self.setFocus(self.getControl(CONTROLS.LIST))
		
		def onClick(self, controlID):
			if controlID==CONTROLS.LIST:
				index = self.getControl(CONTROLS.LIST).getSelectedPosition()
				s = self.getControl(CONTROLS.LIST).getListItem(index).getProperty("selected") != ""
				if s:
					self.getControl(CONTROLS.LIST). getListItem(index).setProperty("selected", "")
				else:
					self.getControl(CONTROLS.LIST). getListItem(index).setProperty("selected", "checked.png")
	
			elif controlID in [ CONTROLS.CLOSE, CONTROLS.CANCEL]:
				self.close()
			elif controlID == CONTROLS.OK:
				for index in xrange(self.getControl(CONTROLS.LIST).size()):
					if self.getControl(CONTROLS.LIST).getListItem(index).getProperty("selected") != "":
						self.return_val.append(self.getControl(CONTROLS.LIST).getListItem(index).getProperty("value"))
				self.close()

	s = MultiSelect("multi_select.xml", skin_path)
	return s.show()
	
def dialog_confirm(title, m1='', m2='', m3='', yes='', no=''):
	dialog = xbmcgui.Dialog()
	return dialog.yesno(title, m1, m2, m3, no, yes)

def raise_error(self, title, m1='', m2=''):
	dialog = xbmcgui.Dialog()
	dialog.ok("%s ERROR!" % get_name(), str(title), str(m1), str(m2))

def _eod(cache_to_disc=True):
	xbmcplugin.endOfDirectory(HANDLE_ID, cacheToDisc=cache_to_disc)

def eod(view_id=None, content=None, clear_search=False):
	from constants import DEFAULT_VIEWS
	if view_id in [DEFAULT_VIEWS.SHOWS, DEFAULT_VIEWS.SEASONS, DEFAULT_VIEWS.EPISODES]:
		content = "tvshows"
	elif view_id == DEFAULT_VIEWS.MOVIES:
		content = 'movies'
	if view_id is not None:
		set_view(view_id, content)
	_eod()

def get_current_view():
	window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
	return window.getFocusId()

def set_default_view(view):
	set_setting('default_%s_view' % view, get_current_view())
	
def set_view(view_id, content=None):
	if content is not None:
		xbmcplugin.setContent(HANDLE_ID, content)

	xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)
	xbmcplugin.addSortMethod( handle=HANDLE_ID, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=HANDLE_ID, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
	xbmcplugin.addSortMethod( handle=HANDLE_ID, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
	xbmcplugin.addSortMethod( handle=HANDLE_ID, sortMethod=xbmcplugin.SORT_METHOD_DATE )
	xbmcplugin.addSortMethod( handle=HANDLE_ID, sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
	xbmcplugin.addSortMethod( handle=HANDLE_ID, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.addSortMethod( handle=HANDLE_ID, sortMethod=xbmcplugin.SORT_METHOD_GENRE )


MC_NATIVE = get_setting('use_native_master_control') == 'true'

def add_menu_item(query, infolabels, total_items=0, icon='', image='', fanart='', replace_menu=True, menu=None, visible=True, format=None, in_progress=False):
	if 'display' in infolabels: infolabels['title'] = infolabels['display']
	if hasattr(visible, '__call__'):
		if visible() is False: return
	else:
		if visible is False: return
	
	if not fanart and 'fanart' in infolabels and infolabels['fanart']:
		fanart = infolabels['fanart']
	elif not fanart:
		fanart = get_path() + '/fanart.jpg'
	if format is not None:
		text = format % infolabels['title']
	else:
		text = infolabels['title']
	
	if icon:
		image = vfs.join(ARTWORK, icon)
		
	listitem = xbmcgui.ListItem(text, iconImage=image, thumbnailImage=image)
	cast = infolabels.pop('cast', None)
	try:
		if cast is not None: listitem.setCast(cast)
	except: pass
	watched = False
	if 'playcount' in infolabels and int(infolabels['playcount']) > 0: watched = True 
	if not watched and in_progress:
		listitem.setProperty('totaltime', '999999')
		listitem.setProperty('resumetime', "1")
		infolabels['playcount'] = 0
	listitem.setInfo('video', infolabels)
	listitem.setProperty('IsPlayable', 'false')
	if MC_NATIVE:
		listitem.setProperty('Master.Control', 'native')
	listitem.setProperty('fanart_image', fanart)
	if menu is None:
		menu = ContextMenu()
	menu.add("Addon Settings", {"mode": "addon_settings"}, script=True)
	listitem.addContextMenuItems(menu.get(), replaceItems=replace_menu)
	plugin_url = get_plugin_url(query)
	xbmcplugin.addDirectoryItem(HANDLE_ID, plugin_url, listitem, isFolder=True, totalItems=total_items)



def add_video_item(query, infolabels, total_items=0, icon='', image='', fanart='', replace_menu=True, menu=None, format=None, random_url=True, in_progress=False):
	if 'display' in infolabels: infolabels['title'] = infolabels['display']
	if not fanart:
		fanart = get_path() + '/fanart.jpg'
	if format is not None:
		text = format % infolabels['title']
	else:
		text = infolabels['title']
	if icon:
		image = vfs.join(ARTWORK, icon)
	listitem = xbmcgui.ListItem(text, iconImage=image, thumbnailImage=image)
	cast = infolabels.pop('cast', None)
	try:
		if cast is not None: listitem.setCast(cast)
	except: pass
	#watched = False
	#if 'playcount' in infolabels and int(infolabels['playcount']) > 0: watched = True 
	#if not watched and in_progress:
	#	listitem.setProperty('totaltime', '999999')
	#	listitem.setProperty('resumetime', "1")
	#	infolabels['playcount'] = 0
	listitem.setInfo('video', infolabels)
	listitem.setProperty('IsPlayable', 'true')
	if MC_NATIVE:
		listitem.setProperty('Master.Control', 'native')
	listitem.setProperty('fanart_image', fanart)
	if random_url: query['rand'] = random.random()
	if menu is None:
		menu = ContextMenu()
	menu.add("Addon Settings", {"mode": "addon_settings"}, script=True)
	listitem.addContextMenuItems(menu.get(), replaceItems=replace_menu)
	plugin_url = get_plugin_url(query)
	xbmcplugin.addDirectoryItem(HANDLE_ID, plugin_url, listitem, isFolder=False, totalItems=total_items)
	
def play_stream(url, metadata={"poster": "", "title": "", "resume_point": ""}):
	set_property('core.playing', "true", 'service.core.playback')
	if url.startswith("playlist://"):
		li = eval(url[11:])
		plst = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
		plst.clear()
		xbmc.sleep(200)
		for l in li:
			index = li.index(l)
			liz = xbmcgui.ListItem(metadata['title'], path=l)
			plst.add(l, liz, index)
			if index == 0: xbmcplugin.setResolvedUrl(HANDLE_ID, True, liz)
		plst.unshuffle()
	else:
		listitem = xbmcgui.ListItem(metadata['title'], iconImage=metadata['poster'], thumbnailImage=metadata['poster'], path=url)
		listitem.setPath(url)
		listitem.setInfo("video", metadata)
		listitem.setProperty('IsPlayable', 'true')
		resume_point = check_resume_point()
		
		if resume_point:
			listitem.setProperty('totaltime', '999999')
			listitem.setProperty('resumetime', str(resume_point))
		if HANDLE_ID > -1:
			xbmcplugin.setResolvedUrl(HANDLE_ID, True, listitem)
		else:
			xbmc.Player().play(url, listitem)
	while get_property('core.playing', 'service.core.playback'):
		sleep(100)
	_on_playback_stop()

def set_playback_info(infoLabel):
	set_property('core.infolabel', json.dumps(infoLabel), "service.core.playback")

def get_playback_times():
	#try:
	percent = int(get_property('core.percent', 'service.core.playback'))
	current_time = get_property('core.current_time', 'service.core.playback')
	total_time = get_property('core.total_time', 'service.core.playback')
	return current_time, total_time, percent
	#except:
	#	return 0,0,0
	
def check_resume_point():
	if 'media' in args and 'trakt_id' in args:
		import coreplayback
		return coreplayback.check_resume_point(args['media'], args['trakt_id'])
	return False
		

def on_playback_stop():
	pass

def _on_playback_stop():
	on_playback_stop()
	hash = get_property('Playback.Hash')
	if hash:
		from scrapecore.scrapecore import delete_torrent
		resolver = get_property('Playback.Resolver')
		id = get_property('Playback.Id')
		delete_torrent(resolver, hash, id)
		set_property('Playback.Hash', '')
		set_property('Playback.Resolver', '')
		set_property('Playback.Id', '')
	
	if get_setting('refresh_onstop') == 'true': 
		go_to_url(get_property('last.plugin.url'))

def map_directory(items, args=(), kwargs={}):
	def decorator(func):
		map(func, items)
	return decorator
	
def _register(mode, target, args=(), kwargs={}):
	if isinstance(mode, list):
		for foo in mode:
			__dispatcher[foo] = target
			__args[foo] = args
			__kwargs[foo] = kwargs
	else:
		__dispatcher[mode] = target
		__args[mode] = args
		__kwargs[mode] = kwargs

def register(mode):
	def func_decorator(func):
		_register(mode, func)
	return func_decorator

def first_run():
	pass

def run():
	if args['mode'] == 'void': return
	if get_setting('setup_run') != 'true' and 'video' in get_id():
		first_run()
	if mode not in ['search_streams', 'play_stream', 'master_control', 'open_settings', 'auth_realdebrid']:
		set_property('last.plugin.url', sys.argv[0] + sys.argv[2])
	if True:#try:
		if args['mode'] == 'addon_settings': 
			open_settings()
			return
		elif args['mode'] is None or not args['mode']:
			__dispatcher[args['main']](*__args[args['main']], **__kwargs[args['main']])
		else:
			__dispatcher[args['mode']](*__args[args['mode']], **__kwargs[args['mode']])
		log("Executing with params: %s | args: %s | kwargs: %s" % (args, __args[args['mode']], __kwargs[args['mode']]))
	#except Exception, e:
	#	log(e)
	#	traceback.print_stack()
	#	handel_error("%s Error" % get_name(), 'Invalid Mode')

class TextBox:
	# constants
	WINDOW = 10147
	CONTROL_LABEL = 1
	CONTROL_TEXTBOX = 5

	def __init__( self, *args, **kwargs):
		# activate the text viewer window
		xbmc.executebuiltin( "ActivateWindow(%d)" % ( self.WINDOW, ) )
		# get window
		self.window = xbmcgui.Window( self.WINDOW )
		# give window time to initialize
		xbmc.sleep( 500 )


	def setControls( self ):
		#get header, text
		heading, text = self.message
		# set heading
		self.window.getControl( self.CONTROL_LABEL ).setLabel( "%s - %s v%s" % ( heading, get_name(), get_version()) )
		# set text
		self.window.getControl( self.CONTROL_TEXTBOX ).setText( text )

	def show(self, heading, text):
		# set controls

		self.message = heading, text
		self.setControls()

		
class ProgressBar(xbmcgui.DialogProgress):
	def __init__(self, *args, **kwargs):
		xbmcgui.DialogProgress.__init__(self, *args, **kwargs)
		self._silent = False
		self._index = 0
		self._total = 0
		self._percent = 0
		
	def new(self, heading, total):
		if not self._silent:
			self._index = 0
			self._total = total
			self._percent = 0
			self._heading = heading
			self.create(heading)
			self.update(0, heading, '')
			
	def update_subheading(self, subheading, subheading2="", percent=False):
		if percent: self._percent = percent
		self.update(self._percent, self._heading, subheading, subheading2)
		
	def next(self, subheading, subheading2=""):
		if not self._silent:
			self._index = self._index + 1
			self._percent = self._index * 100 / self._total
			self.update(self._percent, self._heading, subheading, subheading2)
	
	def is_canceled(self):
		return self.iscanceled()

class ContextMenu:
	def __init__(self):
		self.commands = []

	def add(self, text, arguments={}, script=False, visible=True, mode=False, priority=50):
		if hasattr(visible, '__call__'):
			if visible() is False: return
		else:
			if visible is False: return
		if mode: arguments['mode'] = mode	
		cmd = self._build_url(arguments, script)
		self.commands.append((text, cmd, '', priority))
	
	def _build_url(self, arguments, script):
		for k,v in arguments.iteritems():
			if type(v) is dict:
				arguments[k] = json.dumps(v)
		try:
			plugin_url =  "%s?%s" % (sys.argv[0], urllib.urlencode(arguments))
		except UnicodeEncodeError:
			for k in arguments:
				if isinstance(arguments[k], unicode):
					arguments[k] = arguments[k].encode('utf-8')
			plugin_url =  "%s?%s" % (sys.argv[0], urllib.urlencode(arguments))
			
		if script:
			cmd = 'XBMC.RunPlugin(%s)' % (plugin_url)
		else:
			cmd = "XBMC.Container.Update(%s)" % plugin_url
		return cmd

	def get(self):
		return sorted(self.commands, key=lambda k: k[3])	
		
