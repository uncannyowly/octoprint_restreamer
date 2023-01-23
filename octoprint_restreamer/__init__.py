# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.server import user_permission
import docker
import requests
import pyjq 
import time 
import json 
from requests.structures import CaseInsensitiveDict

class restreamer(octoprint.plugin.StartupPlugin,
				octoprint.plugin.TemplatePlugin,
				octoprint.plugin.AssetPlugin,
				octoprint.plugin.SettingsPlugin,
				octoprint.plugin.SimpleApiPlugin,
				octoprint.plugin.EventHandlerPlugin):

	def get_token(self):
		global token
		self.user = self._settings.get(["user"])
		self.password = self._settings.get(["secret"])
		
		url = 'http://'+self.host+':'+self.port+'/api/login'
		headers = CaseInsensitiveDict()
		headers["Accept"] = "application/json"
		headers["Content-Type"] = "application/json"
		body = '{ "password": "'+self.password+'", "username": "'+self.user+'" }'
		token = requests.post(url, headers=headers,data=body)
		token = json.loads(token.text)
		token = token["access_token"]		
		return token

	def check_stream(self):
		self.host = self._settings.get(["host"])	
		self.port = self._settings.get(["port"])
		self.user = self._settings.get(["user"])
		self.password = self._settings.get(["secret"])
		self.service = self._settings.get(["service"])

		try:
			self.container = self.client.containers.get('Restreamer')
			if self.container:
				if len(self.host) > 0: 
					if self.container.status == 'exited':
						self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False))
						self._logger.info("{ 'Restreamer' : 'OFFLINE' , 'Stream' : 'OFFLINE' }")
					else:
						#Get Process for YT: 
						self.token = self.get_token() 
						url = 'http://'+self.host+':'+self.port+'/api/v3/process'
						headers = CaseInsensitiveDict()
						headers["Accept"] = "application/json"
						headers["Content-Type"] = "application/json"
						headers["Authorization"] = "Bearer " + self.token
					
						streamID_req = requests.get(url,headers=headers)
						streamID_json = json.loads(streamID_req.text)
						streamID = pyjq.all('.[].id',streamID_json)

						for i in streamID:
							if("restreamer-ui:egress:"+self.service in i):
								streamID = i
								url = 'http://' + self.host + ':' + self.port + '/api/v3/process/' + streamID
								headers = CaseInsensitiveDict()
								headers["Accept"] = "application/json"
								headers["Content-Type"] = "application/json"
								headers["Authorization"] = "Bearer " + self.token
								stStatus_req = requests.get(url,headers=headers)
								stStatus_json = json.loads(stStatus_req.text)
								refID = pyjq.one('.reference', stStatus_json)	
								stStatus = pyjq.all('.state.exec', stStatus_json)
							
								for i in stStatus:
									if("running" in i): 
										stStatus = i 
										self._plugin_manager.send_plugin_message(self._identifier, dict(status=True,streaming=True,referenceID=refID,streamID=streamID))
										#self._logger.info('Restreamer URL: ' + url)
										#self._logger.info('Restreamer sID: ' + streamID)
										#self._logger.info('Restreamer rID: ' + refID)
										self._plugin_manager.send_plugin_message(self._identifier, dict(status=True,streaming=True))
										self._logger.info("{ 'Restreamer' : 'ONLINE' , 'Stream' : 'ONLINE' }")
										self.streamID = streamID
										self.refID = refID
										return 2
										#break 
									else:
										self._plugin_manager.send_plugin_message(self._identifier, dict(status=True,streaming=False))
										self._logger.info("{ 'Restreamer' : 'ONLINE' , 'Stream' : 'OFFLINE' }")
										return 1
									self._logger.info('Restreamer StreamStatus: ' + stStatus )
				else:
					self._logger.info("[!] Error: Restreamer container not configured. ")
					return 0 
			else:
				self._logger.info("[!] Error: Restreamer container doesn't exist. ")
				self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False))
				return 0
		except Exception as e:
			self._logger.error(str(e))
			self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False))
			return 0


	def __init__(self):
		self.client = docker.from_env()
		self.container = None


	##~~ StartupPlugin

	def on_after_startup(self):
		self.bootcheck = self.check_stream()
		return 
	
	##~~ TemplatePlugin
	
	def get_template_configs(self):
		return [dict(type="settings",custom_bindings=False)]
		
	##~~ AssetPlugin
	
	def get_assets(self):
		return dict(
			js=["js/restreamer.js"],
			css=["css/restreamer.css"]
		)
		
	##~~ SettingsPlugin
	
	def get_settings_defaults(self):
		return dict(host="",port="",user="",secret="",service="",referenceID="",streaming=False,automatic_start=False,automatic_stop=False)
		
	##~~ SimpleApiPlugin
	
	def get_api_commands(self):
		return dict(startStream=[],stopStream=[],checkStream=[])
		
	def on_api_command(self, command, data):
		if not user_permission.can():
			from flask import make_response
			return make_response("Insufficient rights", 403)
		
		if command == 'startStream':
			self._logger.info("{ command : startStream }")
			if self.container.status == 'exited':
				self.startContainer()
			else:
				self.startStream()

		if command == 'stopStream':
			self._logger.info("{ command : stopStream }")
			self.stopStream()
			time.sleep(5)
			if self._settings.get(["auto_stop_pod"]):
				self.stopContainer()		
		
		if command == 'stopContainer':
			self._logger.info("{ command : stopContainer }")
			self.stopContainer()

		if command == 'startContainer':
			self._logger.info("{ command : startContainer }")
			self.startContainer()


		if command == 'checkStream':
			self._logger.info("{ command : status }")
			#self._logger.info("SC: "+self.container)
			self.container = self.client.containers.get('Restreamer')
			if self.container:
				if len(self.host) > 0: 
					if self.container.status == 'exited':
						self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False))
						self._logger.info("{ 'Restreamer' : 'OFFLINE' , 'Stream' : 'OFFLINE' }")
					else:
						self.check_stream()
				else:
					self._logger.info("[!] Restreamer pod not configured properly. ")
			else:
				self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False))
				self._logger.info("{ 'Restreamer' : 'OFFLINE' , 'Stream' : 'OFFLINE' }")
				self._logger.info("[!] CheckStream error")
				
	##-- EventHandlerPlugin
	def on_event(self, event, payload):
		if event == "PrintStarted" and self._settings.get(["auto_start_stream"]):
			if self.container.status == 'exited':
				self.startContainer()
			else:
				self.startStream()
			
		if event in ["PrintDone","PrintCancelled"] and self._settings.get(["auto_stop_stream"]):
			self.stopStream()
			time.sleep(5)
			if self._settings.get(["auto_stop_pod"]):
				self.stopContainer()
			
	##-- Utility Functions
	
	def startStream(self):	
		self.host = self._settings.get(["host"])	
		self.port = self._settings.get(["port"])
		self.user = self._settings.get(["user"])
		self.password = self._settings.get(["secret"])
		self.service = self._settings.get(["service"])
		self.token = self.get_token() 
		#Stop
		url = 'http://'+self.host+':'+self.port+'/api/v3/process/'+ self.streamID  +'/command'
		headers = CaseInsensitiveDict()
		headers["Accept"] = "application/json"
		headers["Content-Type"] = "application/json"
		headers["Authorization"] = "Bearer "+self.token
		body = '{ "command":"start" }'
		resp = requests.put(url, headers=headers,data=body)    
		time.sleep(5)
		self.check_stream()

	def stopStream(self):
		self.host = self._settings.get(["host"])	
		self.port = self._settings.get(["port"])
		self.user = self._settings.get(["user"])
		self.password = self._settings.get(["secret"])
		self.service = self._settings.get(["service"])
		self.token = self.get_token() 
		#Stop
		url = 'http://'+self.host+':'+self.port+'/api/v3/process/'+ self.streamID  +'/command'
		self._logger.info(url) 
		self._logger.info(self.refID)
		self._logger.info(self.token)
		headers = CaseInsensitiveDict()
		headers["Accept"] = "application/json"
		headers["Content-Type"] = "application/json"
		headers["Authorization"] = "Bearer "+self.token
		body = '{ "command":"stop" }'
		resp = requests.put(url, headers=headers,data=body)    
		time.sleep(5)
		self.check_stream()

	def startContainer(self):	
		self.container = self.client.containers.get('Restreamer')
		if self.container:

			try:
				if self.container.status == 'exited':
					self.status=False
					self.container.start() 
					time.sleep(5)
					self.container = self.client.containers.get('Restreamer')
					if self.container.status == 'exited': 
						self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False)) 
						#self._logger.info("Restreamer [ OFFLINE ]; Stream [ OFFLINE ]")
						#self.streaming=False
					else:
						#self._logger.info("Restreamer [ ONLINE ]; Stream [ ONLINE ]")
						self._plugin_manager.send_plugin_message(self._identifier, dict(status=True))
						#self.streaming=True
						self.check_stream() 
				else:
					self._plugin_manager.send_plugin_message(self._identifier, dict(status=True))
					self.check_stream()
			except Exception as e:
				self._plugin_manager.send_plugin_message(self._identifier, dict(error=str(e),status=False,streaming=False))
		else:
			self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False))
		return 

	def stopContainer(self):
		self.container = self.client.containers.get('Restreamer')
		if self.container:
			try:
				self.container.stop()
				self.container = None
				self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False))
				#self.streaming = "False"
			except Exception as e:
				self._plugin_manager.send_plugin_message(self._identifier, dict(error=str(e),status=True,streaming=False))
		else:
			self._plugin_manager.send_plugin_message(self._identifier, dict(status=False,streaming=False))

	##~~ Softwareupdate hook
	def get_update_information(self):
		return dict(
			restreamer=dict(
				displayName="Restreamer",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="uncannyowly",
				repo="octoprint-restreamer",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/uncannyowly/octoprint-restreamer/archive/{target_version}.zip"
			)
		)


__plugin_name__ = "Restreamer"
__plugin_pythoncompat__ = ">=3,<4"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = restreamer()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}