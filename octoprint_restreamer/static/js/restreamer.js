const sleep = ms => new Promise(r => setTimeout(r, ms));
$(function () {
	function restreamerViewModel(parameters) {
		var self = this;
		
		self.settingsViewModel = parameters[0];

		self.host = ko.observable();
		self.port = ko.observable();
	    self.user = ko.observable();
		self.secret = ko.observable();
		
		self.referenceID = ko.observable();
		self.pod = ko.observable();	
		self.streaming = ko.observable();
		self.status = ko.observable();
		
		self.processing = ko.observable(false);

		self.view_url = ko.observable();
		self.icon = ko.pureComputed(function() {
										var icons = [];
										if (self.streaming() && !self.processing()) {
											icons.push('icon-stop');
										} 
										
										if (!self.streaming() && !self.processing()){
											icons.push('icon-play');
										}
										
										if (self.processing()) {
											icons.push('icon-spin icon-spinner');
										} 
										
										return icons.join(' ');
									});
		self.btnclass = ko.pureComputed(function() {
										return self.streaming() ? 'btn-primary' : 'btn-danger';
									});
									

		// This will get called before the restreamerViewModel gets bound to the DOM, but after its depedencies have
		// already been initialized. It is especially guaranteed that this method gets called _after_ the settings
		// have been retrieved from the OctoPrint backend and thus the SettingsViewModel been properly populated.
		self.onBeforeBinding = function () {
			self.host(self.settingsViewModel.settings.plugins.restreamer.host());
			self.port(self.settingsViewModel.settings.plugins.restreamer.port());
		};

		self.onEventSettingsUpdated = function (payload) {            
			self.host(self.settingsViewModel.settings.plugins.restreamer.host());
			self.port(self.settingsViewModel.settings.plugins.restreamer.port());
			self.user(self.settingsViewModel.settings.plugins.restreamer.user());
			self.secret(self.settingsViewModel.settings.plugins.restreamer.secret());
			//self.referenceID(self.settingsViewModel.settings.plugins.restreamer.referenceID());

			console.log("oof: " + self.referenceID());

			if(self.streaming()){
				streamURL = 'http://' + self.settingsViewModel.settings.plugins.restreamer.host() + ':' + self.settingsViewModel.settings.plugins.restreamer.port() + '/'+self.referenceID()+'.html'
				self.view_url(streamURL);
			}else{
				self.view_url('./plugin/restreamer/static/htm/setup.htm');
			}			
        };
		
		self.onAfterBinding = function() {
			$.ajax({
					url: API_BASEURL + "plugin/restreamer",
					type: "POST",
					dataType: "json",
					data: JSON.stringify({
						command: "checkStream"
					}),
					contentType: "application/json; charset=UTF-8"
				})
		}
		
		self.onTabChange = function(next, current) {
			console.log("rID: " + self.referenceID()); 
			if(next == '#tab_plugin_restreamer'){
				if(self.settingsViewModel.settings.webcam.streamRatio() == '4:3'){
					$('#restreamer_wrapper').css('padding-bottom','75%');
				} 

				if(self.settingsViewModel.settings.plugins.restreamer.host().length > 0 ){
					if(self.streaming()){
						self.view_url('http://' + self.settingsViewModel.settings.plugins.restreamer.host() + ':' + self.settingsViewModel.settings.plugins.restreamer.port() + '/' + self.referenceID() + '.html');
					}else{
						self.view_url('./plugin/restreamer/static/htm/setup.htm');
					}
					
				} else {
					self.view_url('./plugin/restreamer/static/htm/setup.htm');
				}
			} else {
				self.view_url('./plugin/restreamer/static/htm/setup.htm');
			}
		}


	self.onDataUpdaterPluginMessage = function(plugin, data) {
		if (plugin != "restreamer") {
			return;
		}
		
		if(data.error) {
			new PNotify({
						title: 'Restreamer Error',
						text: data.error,
						type: 'error',
						hide: false,
						buttons: {
							closer: true,
							sticker: false
						}
						});
		}
		
		if(data.status) {
			
			if(data.streaming == true) {
				self.streaming(true);
				sleep(5); 
				self.view_url('http://' + self.settingsViewModel.settings.plugins.restreamer.host() + ':' + self.settingsViewModel.settings.plugins.restreamer.port() + '/'+self.referenceID()+'.html');
			} else {
				self.streaming(false);
				self.view_url('./plugin/restreamer/static/htm/setup.htm');
				self.processing(false);
			}
			
		}

		if(data.referenceID) {
			self.referenceID(data.referenceID); 
		}
		
		self.processing(false);
	};
	
			self.toggleStream = function() {
				self.processing(true);
				if (self.streaming()) {
					$.ajax({
						url: API_BASEURL + "plugin/restreamer",
						type: "POST",
						dataType: "json",
						data: JSON.stringify({
							command: "stopStream"
						}),
						contentType: "application/json; charset=UTF-8"
					})
					sleep(5);
					//self.view_url('./plugin/restreamer/static/htm/setup.htm');
					$.ajax({
						url: API_BASEURL + "plugin/restreamer",
						type: "POST",
						dataType: "json",
						data: JSON.stringify({
							command: "checkStream"
						}),
						contentType: "application/json; charset=UTF-8"
					})
				} else {
					$.ajax({
						url: API_BASEURL + "plugin/restreamer",
						type: "POST",
						dataType: "json",
						data: JSON.stringify({
							command: "startStream"
						}),
						contentType: "application/json; charset=UTF-8"
					})
					sleep(5);
					//self.view_url('http://' + self.settingsViewModel.settings.plugins.restreamer.host() + ':' + self.settingsViewModel.settings.plugins.restreamer.port() + '/' + self.referenceID() + '.html');
					$.ajax({
						url: API_BASEURL + "plugin/restreamer",
						type: "POST",
						dataType: "json",
						data: JSON.stringify({
							command: "checkStream"
						}),
						contentType: "application/json; charset=UTF-8"
					})
				}
			}
	}
	// This is how our plugin registers itself with the application, by adding some configuration information to
	// the global variable ADDITIONAL_VIEWMODELS
	ADDITIONAL_VIEWMODELS.push([
			// This is the constructor to call for instantiating the plugin
			restreamerViewModel,

			// This is a list of dependencies to inject into the plugin, the order which you request here is the order
			// in which the dependencies will be injected into your view model upon instantiation via the parameters
			// argument
			["settingsViewModel"],

			// Finally, this is the list of all elements we want this view model to be bound to.
			[("#tab_plugin_restreamer")]
		]);
});