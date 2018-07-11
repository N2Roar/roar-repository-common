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
import errno
import socket
from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
from logging import log

class Server(HTTPServer):
	def get_request(self):
		self.socket.settimeout(5.0)
		result = None
		while result is None:
			try:
				result = self.socket.accept()
			except socket.timeout:
				pass
		result[0].settimeout(1000)
		return result
	
	def run(self):
		try:
			self.serve_forever()
		except KeyboardInterrupt:
			pass
		finally:
			self.server_close()
	
	def _handle_request_noblock(self):
		"""Handle one request, without blocking.

		I assume that select.select has returned that the socket is
		readable before this function was called, so there should be
		no risk of blocking in get_request().
		"""
		try:
			request, client_address = self.get_request()
		except socket.error, e:
			if isinstance(e.args, tuple):
				log("errno is %d" % e[0])
				if e[0] == errno.EPIPE:
					log("Detected remote disconnect")
				else:
					log("Socket error: %s" % e)
			else:
				log("Socket error: %s" % e)
		if self.verify_request(request, client_address):
			try:
				self.process_request(request, client_address)
			except:
				self.handle_error(request, client_address)
				self.shutdown_request(request)

class HTTPSServer(HTTPServer):
	def get_request(self):
		self.socket.settimeout(5.0)
		result = None
		while result is None:
			try:
				result = self.socket.accept()
			except socket.timeout:
				pass
		result[0].settimeout(1000)
		return result
	
	def run(self):
		try:
			self.serve_forever()
		except KeyboardInterrupt:
			pass
		finally:
			self.server_close()
	
	def _handle_request_noblock(self):
		"""Handle one request, without blocking.

		I assume that select.select has returned that the socket is
		readable before this function was called, so there should be
		no risk of blocking in get_request().
		"""
		try:
			request, client_address = self.get_request()
		except socket.error, e:
			if isinstance(e.args, tuple):
				log("errno is %d" % e[0])
				if e[0] == errno.EPIPE:
					log("Detected remote disconnect")
				else:
					log("Socket error: %s" % e)
			else:
				log("Socket error: %s" % e)
		if self.verify_request(request, client_address):
			try:
				self.process_request(request, client_address)
			except:
				self.handle_error(request, client_address)
				self.shutdown_request(request)

class ThreadedHTTPServer(ThreadingMixIn, Server):
	"""Handle requests in a separate thread."""

class ThreadedHTTPSServer(ThreadingMixIn, HTTPSServer):
	"""Handle requests in a separate thread."""

def HttpServer(address, port, request_handler):
	return ThreadedHTTPServer((address, port), request_handler)

def HttpsServer(address, port, certfile, request_handler):
	import ssl
	httpd = ThreadedHTTPSServer((address, port), request_handler)
	httpd.socket = ssl.wrap_socket (httpd.socket, certfile=certfile, server_side=True)
	return httpd
	
