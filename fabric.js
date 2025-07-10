
/*! Fabric.js Copyright 2008-2015, Printio (Juriy Zaytsev, Maxim Chernyak) */

var fabric = fabric || { version: '5.2.1' };
if (typeof exports !== 'undefined') {
  exports.fabric = fabric;
}
/* _AMD_START_ */
else if (typeof define === 'function' && define.amd) {
  define([], function() { return fabric; });
}
/* _AMD_END_ */
if (typeof document !== 'undefined' && typeof window !== 'undefined') {
  if (document instanceof (typeof HTMLDocument !== 'undefined' ? HTMLDocument : Document)) {
    fabric.document = document;
  }
  else {
    fabric.document = document.implementation.createHTMLDocument('');
  }
  fabric.window = window;
}
else {
  // assume we're running under node.js when document/window are not present
  var jsdom = require('jsdom');
  var virtualWindow = new jsdom.JSDOM(
    decodeURIComponent('%3C!DOCTYPE%20html%3E%3Chtml%3E%3Chead%3E%3C%2Fhead%3E%3Cbody%3E%3C%2Fbody%3E%3C%2Fhtml%3E'),
    {
      features: {
        FetchExternalResources: ['img']
      },
      resources: 'usable'
    }).window;
  fabric.document = virtualWindow.document;
  fabric.jsdomImplForWrapper = require('jsdom/lib/jsdom/living/generated/utils').implForWrapper;
  fabric.nodeCanvas = require('jsdom/lib/jsdom/utils').Canvas;
  fabric.window = virtualWindow;
  DOMParser = fabric.window.DOMParser;
}

/**
 * True when in environment that supports touch events
 * @type boolean
 */
fabric.isTouchSupported = 'ontouchstart' in fabric.window || 'ontouchstart' in fabric.document ||
  (fabric.window && fabric.window.navigator && fabric.window.navigator.maxTouchPoints > 0);

/**
 * True when in environment that's probably Node.js
 * @type boolean
 */
fabric.isLikelyNode = typeof Buffer !== 'undefined' &&
                      typeof window === 'undefined';

/* _FROM_SVG_START_ */
/**
 * Attributes parsed from all SVG elements
 * @type array
 */
fabric.SHARED_ATTRIBUTES = [
  'display',
  'transform',
  'fill', 'fill-opacity', 'fill-rule',
  'opacity',
  'stroke', 'stroke-dasharray', 'stroke-linecap', 'stroke-dashoffset',
  'stroke-linejoin', 'stroke-miterlimit',
  'stroke-opacity', 'stroke-width',
  'id', 'paint-order', 'vector-effect',
  'instantiated_by_use', 'clip-path',
];
/* _FROM_SVG_END_ */

/**
 * Pixel per Inch as a default value set to 96. Can be changed for more realistic conversion.
 */
fabric.DPI = 96;
fabric.reNum = '(?:[-+]?(?:\\d+|\\d*\\.\\d+)(?:[eE][-+]?\\d+)?)';
fabric.commaWsp = '(?:\\s+,?\\s*|,\\s*)';
fabric.rePathCommand = /([-+]?((\d+\.\d+)|((\d+)|(\.\d+)))(?:[eE][-+]?\d+)?)/ig;
fabric.reNonWord = /[ \n\.,;!\?\-]/;
fabric.fontPaths = { };
fabric.iMatrix = [1, 0, 0, 1, 0, 0];
fabric.svgNS = 'http://www.w3.org/2000/svg';

/**
 * Pixel limit for cache canvases. 1Mpx , 4Mpx should be fine.
 * @since 1.7.14
 * @type Number
 * @default
 */
fabric.perfLimitSizeTotal = 2097152;

/**
 * Pixel limit for cache canvases width or height. IE fixes the maximum at 5000
 * @since 1.7.14
 * @type Number
 * @default
 */
fabric.maxCacheSideLimit = 4096;

/**
 * Lowest pixel limit for cache canvases, set at 256PX
 * @since 1.7.14
 * @type Number
 * @default
 */
fabric.minCacheSideLimit = 256;

/**
 * Cache Object for widths of chars in text rendering.
 */
fabric.charWidthsCache = { };

/**
 * if webgl is enabled and available, textureSize will determine the size
 * of the canvas backend
 * @since 2.0.0
 * @type Number
 * @default
 */
fabric.textureSize = 2048;

/**
 * When 'true', style information is not retained when copy/pasting text, making
 * pasted text use destination style.
 * Defaults to 'false'.
 * @type Boolean
 * @default
 */
fabric.disableStyleCopyPaste = false;

/**
 * Enable webgl for filtering picture is available
 * A filtering backend will be initialized, this will both take memory and
 * time since a default 2048x2048 canvas will be created for the gl context
 * @since 2.0.0
 * @type Boolean
 * @default
 */
fabric.enableGLFiltering = true;

/**
 * Device Pixel Ratio
 * @see https://developer.apple.com/library/safari/documentation/AudioVideo/Conceptual/HTML-canvas-guide/SettingUptheCanvas/SettingUptheCanvas.html
 */
fabric.devicePixelRatio = fabric.window.devicePixelRatio ||
                          fabric.window.webkitDevicePixelRatio ||
                          fabric.window.mozDevicePixelRatio ||
                          1;
/**
 * Browser-specific constant to adjust CanvasRenderingContext2D.shadowBlur value,
 * which is unitless and not rendered equally across browsers.
 *
 * Values that work quite well (as of October 2017) are:
 * - Chrome: 1.5
 * - Edge: 1.75
 * - Firefox: 0.9
 * - Safari: 0.95
 *
 * @since 2.0.0
 * @type Number
 * @default 1
 */
fabric.browserShadowBlurConstant = 1;

/**
 * This object contains the result of arc to bezier conversion for faster retrieving if the same arc needs to be converted again.
 * It was an internal variable, is accessible since version 2.3.4
 */
fabric.arcToSegmentsCache = { };

/**
 * This object keeps the results of the boundsOfCurve calculation mapped by the joined arguments necessary to calculate it.
 * It does speed up calculation, if you parse and add always the same paths, but in case of heavy usage of freedrawing
 * you do not get any speed benefit and you get a big object in memory.
 * The object was a private variable before, while now is appended to the lib so that you have access to it and you
 * can eventually clear it.
 * It was an internal variable, is accessible since version 2.3.4
 */
fabric.boundsOfCurveCache = { };

/**
 * If disabled boundsOfCurveCache is not used. For apps that make heavy usage of pencil drawing probably disabling it is better
 * @default true
 */
fabric.cachesBoundsOfCurve = true;

/**
 * Skip performance testing of setupGLContext and force the use of putImageData that seems to be the one that works best on
 * Chrome + old hardware. if your users are experiencing empty images after filtering you may try to force this to true
 * this has to be set before instantiating the filtering backend ( before filtering the first image )
 * @type Boolean
 * @default false
 */
fabric.forceGLPutImageData = false;

fabric.initFilterBackend = function() {
  if (fabric.enableGLFiltering && fabric.isWebglSupported && fabric.isWebglSupported(fabric.textureSize)) {
    console.log('max texture size: ' + fabric.maxTextureSize);
    return (new fabric.WebglFilterBackend({ tileSize: fabric.textureSize }));
  }
  else if (fabric.Canvas2dFilterBackend) {
    return (new fabric.Canvas2dFilterBackend());
  }
};
/*:
	----------------------------------------------------
	event.js : 1.1.5 : 2014/02/12 : MIT License
	----------------------------------------------------
	https://github.com/mudcube/Event.js
	----------------------------------------------------
	1  : click, dblclick, dbltap
	1+ : tap, longpress, drag, swipe
	2+ : pinch, rotate
	   : mousewheel, devicemotion, shake
	----------------------------------------------------
	Ideas for the future
	----------------------------------------------------
	* GamePad, and other input abstractions.
	* Event batching - i.e. for every x fingers down a new gesture is created.
	----------------------------------------------------
	http://www.w3.org/TR/2011/WD-touch-events-20110505/
	----------------------------------------------------
*/

if (typeof(eventjs) === "undefined") var eventjs = {};

(function(root) { "use strict";

// Add custom *EventListener commands to HTMLElements (set false to prevent funkiness).
root.modifyEventListener = false;

// Add bulk *EventListener commands on NodeLists from querySelectorAll and others  (set false to prevent funkiness).
root.modifySelectors = false;

root.configure = function(conf) {
	if (isFinite(conf.modifyEventListener)) root.modifyEventListener = conf.modifyEventListener;
	if (isFinite(conf.modifySelectors)) root.modifySelectors = conf.modifySelectors;
	/// Augment event listeners
	if (eventListenersAgumented === false && root.modifyEventListener) {
		augmentEventListeners();
	}
	if (selectorsAugmented === false && root.modifySelectors) {
		augmentSelectors();
	}
};

// Event maintenance.
root.add = function(target, type, listener, configure) {
	return eventManager(target, type, listener, configure, "add");
};

root.remove = function(target, type, listener, configure) {
	return eventManager(target, type, listener, configure, "remove");
};

root.returnFalse = function(event) {
	return false;
};

root.stop = function(event) {
	if (!event) return;
	if (event.stopPropagation) event.stopPropagation();
	event.cancelBubble = true; // <= IE8
	event.cancelBubbleCount = 0;
};

root.prevent = function(event) {
	if (!event) return;
	if (event.preventDefault) {
		event.preventDefault();
	} else if (event.preventManipulation) {
		event.preventManipulation(); // MS
	} else {
		event.returnValue = false; // <= IE8
	}
};

root.cancel = function(event) {
	root.stop(event);
	root.prevent(event);
};

root.blur = function() { // Blurs the focused element. Useful when using eventjs.cancel as canceling will prevent focused elements from being blurred.
	var node = document.activeElement;
	if (!node) return;
	var nodeName = document.activeElement.nodeName;
	if (nodeName === "INPUT" || nodeName === "TEXTAREA" || node.contentEditable === "true") {
		if (node.blur) node.blur();
	}
};

// Check whether event is natively supported (via @kangax)
root.getEventSupport = function (target, type) {
	if (typeof(target) === "string") {
		type = target;
		target = window;
	}
	type = "on" + type;
	if (type in target) return true;
	if (!target.setAttribute) target = document.createElement("div");
	if (target.setAttribute && target.removeAttribute) {
		target.setAttribute(type, "");
		var isSupported = typeof target[type] === "function";
		if (typeof target[type] !== "undefined") target[type] = null;
		target.removeAttribute(type);
		return isSupported;
	}
};

var clone = function (obj) {
	if (!obj || typeof (obj) !== 'object') return obj;
	var temp = new obj.constructor();
	for (var key in obj) {
		if (!obj[key] || typeof (obj[key]) !== 'object') {
			temp[key] = obj[key];
		} else { // clone sub-object
			temp[key] = clone(obj[key]);
		}
	}
	return temp;
};

/// Handle custom *EventListener commands.
var eventManager = function(target, type, listener, configure, trigger, fromOverwrite) {
	configure = configure || {};
	// Check whether target is a configuration variable;
	if (String(target) === "[object Object]") {
		var data = target;
		target = data.target; delete data.target;
		///
		if (data.type && data.listener) {
			type = data.type; delete data.type;
			listener = data.listener; delete data.listener;
			for (var key in data) {
				configure[key] = data[key];
			}
		} else { // specialness
			for (var param in data) {
				var value = data[param];
				if (typeof(value) === "function") continue;
				configure[param] = value;
			}
			///
			var ret = {};
			for (var key in data) {
				var param = key.split(",");
				var o = data[key];
				var conf = {};
				for (var k in configure) { // clone base configuration
					conf[k] = configure[k];
				}
				///
				if (typeof(o) === "function") { // without configuration
					var listener = o;
				} else if (typeof(o.listener) === "function") { // with configuration
					var listener = o.listener;
					for (var k in o) { // merge configure into base configuration
						if (typeof(o[k]) === "function") continue;
						conf[k] = o[k];
					}
				} else { // not a listener
					continue;
				}
				///
				for (var n = 0; n < param.length; n ++) {
					ret[key] = eventjs.add(target, param[n], listener, conf, trigger);
				}
			}
			return ret;
		}
	}
	///
	if (!target || !type || !listener) return;
	// Check for element to load on interval (before onload).
	if (typeof(target) === "string" && type === "ready") {
		if (window.eventjs_stallOnReady) { /// force stall for scripts to load
			type = "load";
			target = window;
		} else { //
			var time = (new Date()).getTime();
			var timeout = configure.timeout;
			var ms = configure.interval || 1000 / 60;
			var interval = window.setInterval(function() {
				if ((new Date()).getTime() - time > timeout) {
					window.clearInterval(interval);
				}
				if (document.querySelector(target)) {
					window.clearInterval(interval);
					setTimeout(listener, 1);
				}
			}, ms);
			return;
		}
	}
	// Get DOM element from Query Selector.
	if (typeof(target) === "string") {
		target = document.querySelectorAll(target);
		if (target.length === 0) return createError("Missing target on listener!", arguments); // No results.
		if (target.length === 1) { // Single target.
			target = target[0];
		}
	}

	/// Handle multiple targets.
	var event;
	var events = {};
	if (target.length > 0 && target !== window) {
		for (var n0 = 0, length0 = target.length; n0 < length0; n0 ++) {
			event = eventManager(target[n0], type, listener, clone(configure), trigger);
			if (event) events[n0] = event;
		}
		return createBatchCommands(events);
	}

	/// Check for multiple events in one string.
	if (typeof(type) === "string") {
		type = type.toLowerCase();
		if (type.indexOf(" ") !== -1) {
			type = type.split(" ");
		} else if (type.indexOf(",") !== -1) {
			type = type.split(",");
		}
	}

	/// Attach or remove multiple events associated with a target.
	if (typeof(type) !== "string") { // Has multiple events.
		if (typeof(type.length) === "number") { // Handle multiple listeners glued together.
			for (var n1 = 0, length1 = type.length; n1 < length1; n1 ++) { // Array [type]
				event = eventManager(target, type[n1], listener, clone(configure), trigger);
				if (event) events[type[n1]] = event;
			}
		} else { // Handle multiple listeners.
			for (var key in type) { // Object {type}
				if (typeof(type[key]) === "function") { // without configuration.
					event = eventManager(target, key, type[key], clone(configure), trigger);
				} else { // with configuration.
					event = eventManager(target, key, type[key].listener, clone(type[key]), trigger);
				}
				if (event) events[key] = event;
			}
		}
		return createBatchCommands(events);
	} else if (type.indexOf("on") === 0) { // to support things like "onclick" instead of "click"
		type = type.slice(2);
	}

	// Ensure listener is a function.
	if (typeof(target) !== "object") return createError("Target is not defined!", arguments);
	if (typeof(listener) !== "function") return createError("Listener is not a function!", arguments);

	// Generate a unique wrapper identifier.
	var useCapture = configure.useCapture || false;
	var id = getID(target) + "." + getID(listener) + "." + (useCapture ? 1 : 0);
	// Handle the event.
	if (root.Gesture && root.Gesture._gestureHandlers[type]) { // Fire custom event.
		id = type + id;
		if (trigger === "remove") { // Remove event listener.
			if (!wrappers[id]) return; // Already removed.
			wrappers[id].remove();
			delete wrappers[id];
		} else if (trigger === "add") { // Attach event listener.
			if (wrappers[id]) {
				wrappers[id].add();
				return wrappers[id]; // Already attached.
			}
			// Retains "this" orientation.
			if (configure.useCall && !root.modifyEventListener) {
				var tmp = listener;
				listener = function(event, self) {
					for (var key in self) event[key] = self[key];
					return tmp.call(target, event);
				};
			}
			// Create listener proxy.
			configure.gesture = type;
			configure.target = target;
			configure.listener = listener;
			configure.fromOverwrite = fromOverwrite;
			// Record wrapper.
			wrappers[id] = root.proxy[type](configure);
		}
		return wrappers[id];
	} else { // Fire native event.
		var eventList = getEventList(type);
		for (var n = 0, eventId; n < eventList.length; n ++) {
			type = eventList[n];
			eventId = type + "." + id;
			if (trigger === "remove") { // Remove event listener.
				if (!wrappers[eventId]) continue; // Already removed.
				target[remove](type, listener, useCapture);
				delete wrappers[eventId];
			} else if (trigger === "add") { // Attach event listener.
				if (wrappers[eventId]) return wrappers[eventId]; // Already attached.
				target[add](type, listener, useCapture);
				// Record wrapper.
				wrappers[eventId] = {
					id: eventId,
					type: type,
					target: target,
					listener: listener,
					remove: function() {
						for (var n = 0; n < eventList.length; n ++) {
							root.remove(target, eventList[n], listener, configure);
						}
					}
				};
			}
		}
		return wrappers[eventId];
	}
};

/// Perform batch actions on multiple events.
var createBatchCommands = function(events) {
	return {
		remove: function() { // Remove multiple events.
			for (var key in events) {
				events[key].remove();
			}
		},
		add: function() { // Add multiple events.
			for (var key in events) {
				events[key].add();
			}
		}
	};
};

/// Display error message in console.
var createError = function(message, data) {
	if (typeof(console) === "undefined") return;
	if (typeof(console.error) === "undefined") return;
	console.error(message, data);
};

/// Handle naming discrepancies between platforms.
var pointerDefs = {
	"msPointer": [ "MSPointerDown", "MSPointerMove", "MSPointerUp" ],
	"touch": [ "touchstart", "touchmove", "touchend" ],
	"mouse": [ "mousedown", "mousemove", "mouseup" ]
};

var pointerDetect = {
	// MSPointer
	"MSPointerDown": 0,
	"MSPointerMove": 1,
	"MSPointerUp": 2,
	// Touch
	"touchstart": 0,
	"touchmove": 1,
	"touchend": 2,
	// Mouse
	"mousedown": 0,
	"mousemove": 1,
	"mouseup": 2
};

var getEventSupport = (function() {
	root.supports = {};
	if (window.navigator.msPointerEnabled) {
		root.supports.msPointer = true;
	}
	if (root.getEventSupport("touchstart")) {
		root.supports.touch = true;
	}
	if (root.getEventSupport("mousedown")) {
		root.supports.mouse = true;
	}
})();

var getEventList = (function() {
	return function(type) {
		var prefix = document.addEventListener ? "" : "on"; // IE
		var idx = pointerDetect[type];
		if (isFinite(idx)) {
			var types = [];
			for (var key in root.supports) {
				types.push(prefix + pointerDefs[key][idx]);
			}
			return types;
		} else {
			return [ prefix + type ];
		}
	};
})();

/// Event wrappers to keep track of all events placed in the window.
var wrappers = {};
var counter = 0;
var getID = function(object) {
	if (object === window) return "#window";
	if (object === document) return "#document";
	if (!object.uniqueID) object.uniqueID = "e" + counter ++;
	return object.uniqueID;
};

/// Detect platforms native *EventListener command.
var add = document.addEventListener ? "addEventListener" : "attachEvent";
var remove = document.removeEventListener ? "removeEventListener" : "detachEvent";

/*
	Pointer.js
	----------------------------------------
	Modified from; https://github.com/borismus/pointer.js
*/

root.createPointerEvent = function (event, self, preventRecord) {
	var eventName = self.gesture;
	var target = self.target;
	var pts = event.changedTouches || root.proxy.getCoords(event);
	if (pts.length) {
		var pt = pts[0];
		self.pointers = preventRecord ? [] : pts;
		self.pageX = pt.pageX;
		self.pageY = pt.pageY;
		self.x = self.pageX;
		self.y = self.pageY;
	}
	///
	var newEvent = document.createEvent("Event");
	newEvent.initEvent(eventName, true, true);
	newEvent.originalEvent = event;
	for (var k in self) {
		if (k === "target") continue;
		newEvent[k] = self[k];
	}
	///
	var type = newEvent.type;
	if (root.Gesture && root.Gesture._gestureHandlers[type]) { // capture custom events.
//		target.dispatchEvent(newEvent);
		self.oldListener.call(target, newEvent, self, false);
	}
};

var eventListenersAgumented = false;
var augmentEventListeners = function() {
	/// Allows *EventListener to use custom event proxies.
	if (!window.HTMLElement) return;
	var augmentEventListener = function(proto) {
		var recall = function(trigger) { // overwrite native *EventListener's
			var handle = trigger + "EventListener";
			var handler = proto[handle];
			proto[handle] = function (type, listener, useCapture) {
				if (root.Gesture && root.Gesture._gestureHandlers[type]) { // capture custom events.
					var configure = useCapture;
					if (typeof(useCapture) === "object") {
						configure.useCall = true;
					} else { // convert to configuration object.
						configure = {
							useCall: true,
							useCapture: useCapture
						};
					}
					eventManager(this, type, listener, configure, trigger, true);
//					handler.call(this, type, listener, useCapture);
				} else { // use native function.
					var types = getEventList(type);
					for (var n = 0; n < types.length; n ++) {
						handler.call(this, types[n], listener, useCapture);
					}
				}
			};
		};
		recall("add");
		recall("remove");
	};
	// NOTE: overwriting HTMLElement doesn't do anything in Firefox.
	if (navigator.userAgent.match(/Firefox/)) {
		// TODO: fix Firefox for the general case.
		augmentEventListener(HTMLDivElement.prototype);
		augmentEventListener(HTMLCanvasElement.prototype);
	} else {
		augmentEventListener(HTMLElement.prototype);
	}
	augmentEventListener(document);
	augmentEventListener(window);
};

var selectorsAugmented = false;
var augmentSelectors = function() {
/// Allows querySelectorAll and other NodeLists to perform *EventListener commands in bulk.
	var proto = NodeList.prototype;
	proto.removeEventListener = function(type, listener, useCapture) {
		for (var n = 0, length = this.length; n < length; n ++) {
			this[n].removeEventListener(type, listener, useCapture);
		}
	};
	proto.addEventListener = function(type, listener, useCapture) {
		for (var n = 0, length = this.length; n < length; n ++) {
			this[n].addEventListener(type, listener, useCapture);
		}
	};
};

return root;

})(eventjs);

/*:
	----------------------------------------------------
	eventjs.proxy : 0.4.2 : 2013/07/17 : MIT License
	----------------------------------------------------
	https://github.com/mudcube/eventjs.js
	----------------------------------------------------
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

/*
	Create a new pointer gesture instance.
*/

root.pointerSetup = function(conf, self) {
	/// Configure.
	conf.target = conf.target || window;
	conf.doc = conf.target.ownerDocument || conf.target; // Associated document.
	conf.minFingers = conf.minFingers || conf.fingers || 1; // Minimum required fingers.
	conf.maxFingers = conf.maxFingers || conf.fingers || Infinity; // Maximum allowed fingers.
	conf.position = conf.position || "relative"; // Determines what coordinate system points are returned.
	delete conf.fingers; //-
	/// Convenience data.
	self = self || {};
	self.enabled = true;
	self.gesture = conf.gesture;
	self.target = conf.target;
	self.env = conf.env;
	///
	if (eventjs.modifyEventListener && conf.fromOverwrite) {
		conf.oldListener = conf.listener;
		conf.listener = eventjs.createPointerEvent;
	}
	/// Convenience commands.
	var fingers = 0;
	var type = self.gesture.indexOf("pointer") === 0 && eventjs.modifyEventListener ? "pointer" : "mouse";
	if (conf.oldListener) self.oldListener = conf.oldListener;
	///
	self.listener = conf.listener;
	self.proxy = function(listener) {
		self.defaultListener = conf.listener;
		conf.listener = listener;
		listener(conf.event, self);
	};
	self.add = function() {
		if (self.enabled === true) return;
		if (conf.onPointerDown) eventjs.add(conf.target, type + "down", conf.onPointerDown);
		if (conf.onPointerMove) eventjs.add(conf.doc, type + "move", conf.onPointerMove);
		if (conf.onPointerUp) eventjs.add(conf.doc, type + "up", conf.onPointerUp);
		self.enabled = true;
	};
	self.remove = function() {
		if (self.enabled === false) return;
		if (conf.onPointerDown) eventjs.remove(conf.target, type + "down", conf.onPointerDown);
		if (conf.onPointerMove) eventjs.remove(conf.doc, type + "move", conf.onPointerMove);
		if (conf.onPointerUp) eventjs.remove(conf.doc, type + "up", conf.onPointerUp);
		self.reset();
		self.enabled = false;
	};
	self.pause = function(opt) {
		if (conf.onPointerMove && (!opt || opt.move)) eventjs.remove(conf.doc, type + "move", conf.onPointerMove);
		if (conf.onPointerUp && (!opt || opt.up)) eventjs.remove(conf.doc, type + "up", conf.onPointerUp);
		fingers = conf.fingers;
		conf.fingers = 0;
	};
	self.resume = function(opt) {
		if (conf.onPointerMove && (!opt || opt.move)) eventjs.add(conf.doc, type + "move", conf.onPointerMove);
		if (conf.onPointerUp && (!opt || opt.up)) eventjs.add(conf.doc, type + "up", conf.onPointerUp);
		conf.fingers = fingers;
	};
	self.reset = function() {
		conf.tracker = {};
		conf.fingers = 0;
	};
	///
	return self;
};

/*
	Begin proxied pointer command.
*/

var sp = eventjs.supports; // Default pointerType
///
eventjs.isMouse = !!sp.mouse;
eventjs.isMSPointer = !!sp.touch;
eventjs.isTouch = !!sp.msPointer;
///
root.pointerStart = function(event, self, conf) {
	/// tracks multiple inputs
	var type = (event.type || "mousedown").toUpperCase();
	if (type.indexOf("MOUSE") === 0) {
		eventjs.isMouse = true;
		eventjs.isTouch = false;
		eventjs.isMSPointer = false;
	} else if (type.indexOf("TOUCH") === 0) {
		eventjs.isMouse = false;
		eventjs.isTouch = true;
		eventjs.isMSPointer = false;
	} else if (type.indexOf("MSPOINTER") === 0) {
		eventjs.isMouse = false;
		eventjs.isTouch = false;
		eventjs.isMSPointer = true;
	}
	///
	var addTouchStart = function(touch, sid) {
		var bbox = conf.bbox;
		var pt = track[sid] = {};
		///
		switch(conf.position) {
			case "absolute": // Absolute from within window.
				pt.offsetX = 0;
				pt.offsetY = 0;
				break;
			case "differenceFromLast": // Since last coordinate recorded.
				pt.offsetX = touch.pageX;
				pt.offsetY = touch.pageY;
				break;
			case "difference": // Relative from origin.
				pt.offsetX = touch.pageX;
				pt.offsetY = touch.pageY;
				break;
			case "move": // Move target element.
				pt.offsetX = touch.pageX - bbox.x1;
				pt.offsetY = touch.pageY - bbox.y1;
				break;
			default: // Relative from within target.
				pt.offsetX = bbox.x1 - bbox.scrollLeft;
				pt.offsetY = bbox.y1 - bbox.scrollTop;
				break;
		}
		///
		var x = touch.pageX - pt.offsetX;
		var y = touch.pageY - pt.offsetY;
		///
		pt.rotation = 0;
		pt.scale = 1;
		pt.startTime = pt.moveTime = (new Date()).getTime();
		pt.move = { x: x, y: y };
		pt.start = { x: x, y: y };
		///
		conf.fingers ++;
	};
	///
	conf.event = event;
	if (self.defaultListener) {
		conf.listener = self.defaultListener;
		delete self.defaultListener;
	}
	///
	var isTouchStart = !conf.fingers;
	var track = conf.tracker;
	var touches = event.changedTouches || root.getCoords(event);
	var length = touches.length;
	// Adding touch events to tracking.
	for (var i = 0; i < length; i ++) {
		var touch = touches[i];
		var sid = touch.identifier || Infinity; // Touch ID.
		// Track the current state of the touches.
		if (conf.fingers) {
			if (conf.fingers >= conf.maxFingers) {
				var ids = [];
				for (var sid in conf.tracker) ids.push(sid);
				self.identifier = ids.join(",");
				return isTouchStart;
			}
			var fingers = 0; // Finger ID.
			for (var rid in track) {
				// Replace removed finger.
				if (track[rid].up) {
					delete track[rid];
					addTouchStart(touch, sid);
					conf.cancel = true;
					break;
				}
				fingers ++;
			}
			// Add additional finger.
			if (track[sid]) continue;
			addTouchStart(touch, sid);
		} else { // Start tracking fingers.
			track = conf.tracker = {};
			self.bbox = conf.bbox = root.getBoundingBox(conf.target);
			conf.fingers = 0;
			conf.cancel = false;
			addTouchStart(touch, sid);
		}
	}
	///
	var ids = [];
	for (var sid in conf.tracker) ids.push(sid);
	self.identifier = ids.join(",");
	///
	return isTouchStart;
};

/*
	End proxied pointer command.
*/

root.pointerEnd = function(event, self, conf, onPointerUp) {
	// Record changed touches have ended (iOS changedTouches is not reliable).
	var touches = event.touches || [];
	var length = touches.length;
	var exists = {};
	for (var i = 0; i < length; i ++) {
		var touch = touches[i];
		var sid = touch.identifier;
		exists[sid || Infinity] = true;
	}
	for (var sid in conf.tracker) {
		var track = conf.tracker[sid];
		if (exists[sid] || track.up) continue;
		if (onPointerUp) { // add changedTouches to mouse.
			onPointerUp({
				pageX: track.pageX,
				pageY: track.pageY,
				changedTouches: [{
					pageX: track.pageX,
					pageY: track.pageY,
					identifier: sid === "Infinity" ? Infinity : sid
				}]
			}, "up");
		}
		track.up = true;
		conf.fingers --;
	}
/*	// This should work but fails in Safari on iOS4 so not using it.
	var touches = event.changedTouches || root.getCoords(event);
	var length = touches.length;
	// Record changed touches have ended (this should work).
	for (var i = 0; i < length; i ++) {
		var touch = touches[i];
		var sid = touch.identifier || Infinity;
		var track = conf.tracker[sid];
		if (track && !track.up) {
			if (onPointerUp) { // add changedTouches to mouse.
				onPointerUp({
					changedTouches: [{
						pageX: track.pageX,
						pageY: track.pageY,
						identifier: sid === "Infinity" ? Infinity : sid
					}]
				}, "up");
			}
			track.up = true;
			conf.fingers --;
		}
	} */
	// Wait for all fingers to be released.
	if (conf.fingers !== 0) return false;
	// Record total number of fingers gesture used.
	var ids = [];
	conf.gestureFingers = 0;
	for (var sid in conf.tracker) {
		conf.gestureFingers ++;
		ids.push(sid);
	}
	self.identifier = ids.join(",");
	// Our pointer gesture has ended.
	return true;
};

/*
	Returns mouse coords in an array to match event.*Touches
	------------------------------------------------------------
	var touch = event.changedTouches || root.getCoords(event);
*/

root.getCoords = function(event) {
	if (typeof(event.pageX) !== "undefined") { // Desktop browsers.
		root.getCoords = function(event) {
			return Array({
				type: "mouse",
				x: event.pageX,
				y: event.pageY,
				pageX: event.pageX,
				pageY: event.pageY,
				identifier: event.pointerId || Infinity // pointerId is MS
			});
		};
	} else { // Internet Explorer <= 8.0
		root.getCoords = function(event) {
			var doc = document.documentElement;
			event = event || window.event;
			return Array({
				type: "mouse",
				x: event.clientX + doc.scrollLeft,
				y: event.clientY + doc.scrollTop,
				pageX: event.clientX + doc.scrollLeft,
				pageY: event.clientY + doc.scrollTop,
				identifier: Infinity
			});
		};
	}
	return root.getCoords(event);
};

/*
	Returns single coords in an object.
	------------------------------------------------------------
	var mouse = root.getCoord(event);
*/

root.getCoord = function(event) {
	if ("ontouchstart" in window) { // Mobile browsers.
		var pX = 0;
		var pY = 0;
		root.getCoord = function(event) {
			var touches = event.changedTouches;
			if (touches && touches.length) { // ontouchstart + ontouchmove
				return {
					x: pX = touches[0].pageX,
					y: pY = touches[0].pageY
				};
			} else { // ontouchend
				return {
					x: pX,
					y: pY
				};
			}
		};
	} else if(typeof(event.pageX) !== "undefined" && typeof(event.pageY) !== "undefined") { // Desktop browsers.
		root.getCoord = function(event) {
			return {
				x: event.pageX,
				y: event.pageY
			};
		};
	} else { // Internet Explorer <=8.0
		root.getCoord = function(event) {
			var doc = document.documentElement;
			event = event || window.event;
			return {
				x: event.clientX + doc.scrollLeft,
				y: event.clientY + doc.scrollTop
			};
		};
	}
	return root.getCoord(event);
};

/*
	Get target scale and position in space.
*/

var getPropertyAsFloat = function(o, type) {
	var n = parseFloat(o.getPropertyValue(type), 10);
	return isFinite(n) ? n : 0;
};

root.getBoundingBox = function(o) {
	if (o === window || o === document) o = document.body;
	///
	var bbox = {};
	var bcr = o.getBoundingClientRect();
	bbox.width = bcr.width;
	bbox.height = bcr.height;
	bbox.x1 = bcr.left;
	bbox.y1 = bcr.top;
	bbox.scaleX = bcr.width / o.offsetWidth || 1;
	bbox.scaleY = bcr.height / o.offsetHeight || 1;
	bbox.scrollLeft = 0;
	bbox.scrollTop = 0;
	///
	var style = window.getComputedStyle(o);
	var borderBox = style.getPropertyValue("box-sizing") === "border-box";
	///
	if (borderBox === false) {
		var left = getPropertyAsFloat(style, "border-left-width");
		var right = getPropertyAsFloat(style, "border-right-width");
		var bottom = getPropertyAsFloat(style, "border-bottom-width");
		var top = getPropertyAsFloat(style, "border-top-width");
		bbox.border = [ left, right, top, bottom ];
		bbox.x1 += left;
		bbox.y1 += top;
		bbox.width -= right + left;
		bbox.height -= bottom + top;
	}

/*	var left = getPropertyAsFloat(style, "padding-left");
	var right = getPropertyAsFloat(style, "padding-right");
	var bottom = getPropertyAsFloat(style, "padding-bottom");
	var top = getPropertyAsFloat(style, "padding-top");
	bbox.padding = [ left, right, top, bottom ];*/
	///
	bbox.x2 = bbox.x1 + bbox.width;
	bbox.y2 = bbox.y1 + bbox.height;

	/// Get the scroll of container element.
	var position = style.getPropertyValue("position");
	var tmp = position === "fixed" ? o : o.parentNode;
	while (tmp !== null) {
		if (tmp === document.body) break;
		if (tmp.scrollTop === undefined) break;
		var style = window.getComputedStyle(tmp);
		var position = style.getPropertyValue("position");
		if (position === "absolute") {

		} else if (position === "fixed") {
//			bbox.scrollTop += document.body.scrollTop;
//			bbox.scrollLeft += document.body.scrollLeft;
			bbox.scrollTop -= tmp.parentNode.scrollTop;
			bbox.scrollLeft -= tmp.parentNode.scrollLeft;
			break;
		} else {
			bbox.scrollLeft += tmp.scrollLeft;
			bbox.scrollTop += tmp.scrollTop;
		}
		///
		tmp = tmp.parentNode;
	};
	///
	bbox.scrollBodyLeft = (window.pageXOffset !== undefined) ? window.pageXOffset : (document.documentElement || document.body.parentNode || document.body).scrollLeft;
	bbox.scrollBodyTop = (window.pageYOffset !== undefined) ? window.pageYOffset : (document.documentElement || document.body.parentNode || document.body).scrollTop;
	///
	bbox.scrollLeft -= bbox.scrollBodyLeft;
	bbox.scrollTop -= bbox.scrollBodyTop;
	///
	return bbox;
};

/*
	Keep track of metaKey, the proper ctrlKey for users platform.
	----------------------------------------------------
	http://www.quirksmode.org/js/keys.html
	-----------------------------------
	http://unixpapa.com/js/key.html
*/

(function() {
	var agent = navigator.userAgent.toLowerCase();
	var mac = agent.indexOf("macintosh") !== -1;
	var metaKeys;
	if (mac && agent.indexOf("khtml") !== -1) { // chrome, safari.
		metaKeys = { 91: true, 93: true };
	} else if (mac && agent.indexOf("firefox") !== -1) {  // mac firefox.
		metaKeys = { 224: true };
	} else { // windows, linux, or mac opera.
		metaKeys = { 17: true };
	}
	(root.metaTrackerReset = function() {
		eventjs.fnKey = root.fnKey = false;
		eventjs.metaKey = root.metaKey = false;
		eventjs.escKey = root.escKey = false;
		eventjs.ctrlKey = root.ctrlKey = false;
		eventjs.shiftKey = root.shiftKey = false;
		eventjs.altKey = root.altKey = false;
	})();
	root.metaTracker = function(event) {
		var isKeyDown = event.type === "keydown";
		if (event.keyCode === 27) eventjs.escKey = root.escKey = isKeyDown;
		if (metaKeys[event.keyCode]) eventjs.metaKey = root.metaKey = isKeyDown;
		eventjs.ctrlKey = root.ctrlKey = event.ctrlKey;
		eventjs.shiftKey = root.shiftKey = event.shiftKey;
		eventjs.altKey = root.altKey = event.altKey;
	};
})();

return root;

})(eventjs.proxy);
/*:
	----------------------------------------------------
	"MutationObserver" event proxy.
	----------------------------------------------------
	author: Selvakumar Arumugam - MIT LICENSE
	   src: http://stackoverflow.com/questions/10868104/can-you-have-a-javascript-hook-trigger-after-a-dom-elements-style-object-change
	----------------------------------------------------
*/
if (typeof(eventjs) === "undefined") var eventjs = {};

eventjs.MutationObserver = (function() {
	var MutationObserver = window.MutationObserver || window.WebKitMutationObserver || window.MozMutationObserver;
	var DOMAttrModifiedSupported = !MutationObserver && (function() {
		var p = document.createElement("p");
		var flag = false;
		var fn = function() { flag = true };
		if (p.addEventListener) {
			p.addEventListener("DOMAttrModified", fn, false);
		} else if (p.attachEvent) {
			p.attachEvent("onDOMAttrModified", fn);
		} else {
			return false;
		}
		///
		p.setAttribute("id", "target");
		///
		return flag;
	})();
	///
	return function(container, callback) {
		if (MutationObserver) {
			var options = {
				subtree: false,
				attributes: true
			};
			var observer = new MutationObserver(function(mutations) {
				mutations.forEach(function(e) {
					callback.call(e.target, e.attributeName);
				});
			});
			observer.observe(container, options)
		} else if (DOMAttrModifiedSupported) {
			eventjs.add(container, "DOMAttrModified", function(e) {
				callback.call(container, e.attrName);
			});
		} else if ("onpropertychange" in document.body) {
			eventjs.add(container, "propertychange", function(e) {
				callback.call(container, window.event.propertyName);
			});
		}
	}
})();
/*:
	"Click" event proxy.
	----------------------------------------------------
	eventjs.add(window, "click", function(event, self) {});
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

root.click = function(conf) {
	conf.gesture = conf.gesture || "click";
	conf.maxFingers = conf.maxFingers || conf.fingers || 1;
	/// Tracking the events.
	conf.onPointerDown = function (event) {
		if (root.pointerStart(event, self, conf)) {
			eventjs.add(conf.target, "mouseup", conf.onPointerUp);
		}
	};
	conf.onPointerUp = function(event) {
		if (root.pointerEnd(event, self, conf)) {
			eventjs.remove(conf.target, "mouseup", conf.onPointerUp);
			var pointers = event.changedTouches || root.getCoords(event);
			var pointer = pointers[0];
			var bbox = conf.bbox;
			var newbbox = root.getBoundingBox(conf.target);
			var y = pointer.pageY - newbbox.scrollBodyTop;
			var x = pointer.pageX - newbbox.scrollBodyLeft;
			////
			if (x > bbox.x1 && y > bbox.y1 &&
				x < bbox.x2 && y < bbox.y2 &&
				bbox.scrollTop === newbbox.scrollTop) { // has not been scrolled
				///
				for (var key in conf.tracker) break; //- should be modularized? in dblclick too
				var point = conf.tracker[key];
				self.x = point.start.x;
				self.y = point.start.y;
				///
				conf.listener(event, self);
			}
		}
	};
	// Generate maintenance commands, and other configurations.
	var self = root.pointerSetup(conf);
	self.state = "click";
	// Attach events.
	eventjs.add(conf.target, "mousedown", conf.onPointerDown);
	// Return this object.
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.click = root.click;

return root;

})(eventjs.proxy);
/*:
	"Double-Click" aka "Double-Tap" event proxy.
	----------------------------------------------------
	eventjs.add(window, "dblclick", function(event, self) {});
	----------------------------------------------------
	Touch an target twice for <= 700ms, with less than 25 pixel drift.
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

root.dbltap =
root.dblclick = function(conf) {
	conf.gesture = conf.gesture || "dbltap";
	conf.maxFingers = conf.maxFingers || conf.fingers || 1;
	// Setting up local variables.
	var delay = 700; // in milliseconds
	var time0, time1, timeout;
	var pointer0, pointer1;
	// Tracking the events.
	conf.onPointerDown = function (event) {
		var pointers = event.changedTouches || root.getCoords(event);
		if (time0 && !time1) { // Click #2
			pointer1 = pointers[0];
			time1 = (new Date()).getTime() - time0;
		} else { // Click #1
			pointer0 = pointers[0];
			time0 = (new Date()).getTime();
			time1 = 0;
			clearTimeout(timeout);
			timeout = setTimeout(function() {
				time0 = 0;
			}, delay);
		}
		if (root.pointerStart(event, self, conf)) {
			eventjs.add(conf.target, "mousemove", conf.onPointerMove).listener(event);
			eventjs.add(conf.target, "mouseup", conf.onPointerUp);
		}
	};
	conf.onPointerMove = function (event) {
		if (time0 && !time1) {
			var pointers = event.changedTouches || root.getCoords(event);
			pointer1 = pointers[0];
		}
		var bbox = conf.bbox;
		var ax = (pointer1.pageX - bbox.x1);
		var ay = (pointer1.pageY - bbox.y1);
		if (!(ax > 0 && ax < bbox.width && // Within target coordinates..
			  ay > 0 && ay < bbox.height &&
			  Math.abs(pointer1.pageX - pointer0.pageX) <= 25 && // Within drift deviance.
			  Math.abs(pointer1.pageY - pointer0.pageY) <= 25)) {
			// Cancel out this listener.
			eventjs.remove(conf.target, "mousemove", conf.onPointerMove);
			clearTimeout(timeout);
			time0 = time1 = 0;
		}
	};
	conf.onPointerUp = function(event) {
		if (root.pointerEnd(event, self, conf)) {
			eventjs.remove(conf.target, "mousemove", conf.onPointerMove);
			eventjs.remove(conf.target, "mouseup", conf.onPointerUp);
		}
		if (time0 && time1) {
			if (time1 <= delay) { // && !(event.cancelBubble && ++event.cancelBubbleCount > 1)) {
				self.state = conf.gesture;
				for (var key in conf.tracker) break;
				var point = conf.tracker[key];
				self.x = point.start.x;
				self.y = point.start.y;
				conf.listener(event, self);
			}
			clearTimeout(timeout);
			time0 = time1 = 0;
		}
	};
	// Generate maintenance commands, and other configurations.
	var self = root.pointerSetup(conf);
	self.state = "dblclick";
	// Attach events.
	eventjs.add(conf.target, "mousedown", conf.onPointerDown);
	// Return this object.
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.dbltap = root.dbltap;
eventjs.Gesture._gestureHandlers.dblclick = root.dblclick;

return root;

})(eventjs.proxy);
/*:
	"Drag" event proxy (1+ fingers).
	----------------------------------------------------
	CONFIGURE: maxFingers, position.
	----------------------------------------------------
	eventjs.add(window, "drag", function(event, self) {
		console.log(self.gesture, self.state, self.start, self.x, self.y, self.bbox);
	});
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

root.dragElement = function(that, event) {
	root.drag({
		event: event,
		target: that,
		position: "move",
		listener: function(event, self) {
			that.style.left = self.x + "px";
			that.style.top = self.y + "px";
			eventjs.prevent(event);
		}
	});
};

root.drag = function(conf) {
	conf.gesture = "drag";
	conf.onPointerDown = function (event) {
		if (root.pointerStart(event, self, conf)) {
			if (!conf.monitor) {
				eventjs.add(conf.doc, "mousemove", conf.onPointerMove);
				eventjs.add(conf.doc, "mouseup", conf.onPointerUp);
			}
		}
		// Process event listener.
		conf.onPointerMove(event, "down");
	};
	conf.onPointerMove = function (event, state) {
		if (!conf.tracker) return conf.onPointerDown(event);
		var bbox = conf.bbox;
		var touches = event.changedTouches || root.getCoords(event);
		var length = touches.length;
		for (var i = 0; i < length; i ++) {
			var touch = touches[i];
			var identifier = touch.identifier || Infinity;
			var pt = conf.tracker[identifier];
			// Identifier defined outside of listener.
			if (!pt) continue;
			pt.pageX = touch.pageX;
			pt.pageY = touch.pageY;
			// Record data.
			self.state = state || "move";
			self.identifier = identifier;
			self.start = pt.start;
			self.fingers = conf.fingers;
			if (conf.position === "differenceFromLast") {
				self.x = (pt.pageX - pt.offsetX);
				self.y = (pt.pageY - pt.offsetY);
				pt.offsetX = pt.pageX;
				pt.offsetY = pt.pageY;
			} else {
				self.x = (pt.pageX - pt.offsetX);
				self.y = (pt.pageY - pt.offsetY);
			}
			///
			conf.listener(event, self);
		}
	};
	conf.onPointerUp = function(event) {
		// Remove tracking for touch.
		if (root.pointerEnd(event, self, conf, conf.onPointerMove)) {
			if (!conf.monitor) {
				eventjs.remove(conf.doc, "mousemove", conf.onPointerMove);
				eventjs.remove(conf.doc, "mouseup", conf.onPointerUp);
			}
		}
	};
	// Generate maintenance commands, and other configurations.
	var self = root.pointerSetup(conf);
	// Attach events.
	if (conf.event) {
		conf.onPointerDown(conf.event);
	} else { //
		eventjs.add(conf.target, "mousedown", conf.onPointerDown);
		if (conf.monitor) {
			eventjs.add(conf.doc, "mousemove", conf.onPointerMove);
			eventjs.add(conf.doc, "mouseup", conf.onPointerUp);
		}
	}
	// Return this object.
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.drag = root.drag;

return root;

})(eventjs.proxy);
/*:
	"Gesture" event proxy (2+ fingers).
	----------------------------------------------------
	CONFIGURE: minFingers, maxFingers.
	----------------------------------------------------
	eventjs.add(window, "gesture", function(event, self) {
		console.log(
			self.x, // centroid
			self.y,
			self.rotation,
			self.scale,
			self.fingers,
			self.state
		);
	});
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

var RAD_DEG = Math.PI / 180;
var getCentroid = function(self, points) {
	var centroidx = 0;
	var centroidy = 0;
	var length = 0;
	for (var sid in points) {
		var touch = points[sid];
		if (touch.up) continue;
		centroidx += touch.move.x;
		centroidy += touch.move.y;
		length ++;
	}
	self.x = centroidx /= length;
	self.y = centroidy /= length;
	return self;
};

root.gesture = function(conf) {
	conf.gesture = conf.gesture || "gesture";
	conf.minFingers = conf.minFingers || conf.fingers || 2;
	// Tracking the events.
	conf.onPointerDown = function (event) {
		var fingers = conf.fingers;
		if (root.pointerStart(event, self, conf)) {
			eventjs.add(conf.doc, "mousemove", conf.onPointerMove);
			eventjs.add(conf.doc, "mouseup", conf.onPointerUp);
		}
		// Record gesture start.
		if (conf.fingers === conf.minFingers && fingers !== conf.fingers) {
			self.fingers = conf.minFingers;
			self.scale = 1;
			self.rotation = 0;
			self.state = "start";
			var sids = ""; //- FIXME(mud): can generate duplicate IDs.
			for (var key in conf.tracker) sids += key;
			self.identifier = parseInt(sids);
			getCentroid(self, conf.tracker);
			conf.listener(event, self);
		}
	};
	///
	conf.onPointerMove = function (event, state) {
		var bbox = conf.bbox;
		var points = conf.tracker;
		var touches = event.changedTouches || root.getCoords(event);
		var length = touches.length;
		// Update tracker coordinates.
		for (var i = 0; i < length; i ++) {
			var touch = touches[i];
			var sid = touch.identifier || Infinity;
			var pt = points[sid];
			// Check whether "pt" is used by another gesture.
			if (!pt) continue;
			// Find the actual coordinates.
			pt.move.x = (touch.pageX - bbox.x1);
			pt.move.y = (touch.pageY - bbox.y1);
		}
		///
		if (conf.fingers < conf.minFingers) return;
		///
		var touches = [];
		var scale = 0;
		var rotation = 0;

		/// Calculate centroid of gesture.
		getCentroid(self, points);
		///
		for (var sid in points) {
			var touch = points[sid];
			if (touch.up) continue;
			var start = touch.start;
			if (!start.distance) {
				var dx = start.x - self.x;
				var dy = start.y - self.y;
				start.distance = Math.sqrt(dx * dx + dy * dy);
				start.angle = Math.atan2(dx, dy) / RAD_DEG;
			}
			// Calculate scale.
			var dx = touch.move.x - self.x;
			var dy = touch.move.y - self.y;
			var distance = Math.sqrt(dx * dx + dy * dy);
			// If touch start.distance from centroid is 0, scale should not be updated.
			// This prevents dividing by 0 in cases where start.distance is oddly 0.
			if (start.distance !== 0) {
			  scale += distance / start.distance;
			}
			// Calculate rotation.
			var angle = Math.atan2(dx, dy) / RAD_DEG;
			var rotate = (start.angle - angle + 360) % 360 - 180;
			touch.DEG2 = touch.DEG1; // Previous degree.
			touch.DEG1 = rotate > 0 ? rotate : -rotate; // Current degree.
			if (typeof(touch.DEG2) !== "undefined") {
				if (rotate > 0) {
					touch.rotation += touch.DEG1 - touch.DEG2;
				} else {
					touch.rotation -= touch.DEG1 - touch.DEG2;
				}
				rotation += touch.rotation;
			}
			// Attach current points to self.
			touches.push(touch.move);
		}
		///
		self.touches = touches;
		self.fingers = conf.fingers;
		self.scale = scale / conf.fingers;
		self.rotation = rotation / conf.fingers;
		self.state = "change";
		conf.listener(event, self);
	};
	conf.onPointerUp = function(event) {
		// Remove tracking for touch.
		var fingers = conf.fingers;
		if (root.pointerEnd(event, self, conf)) {
			eventjs.remove(conf.doc, "mousemove", conf.onPointerMove);
			eventjs.remove(conf.doc, "mouseup", conf.onPointerUp);
		}
		// Check whether fingers has dropped below minFingers.
		if (fingers === conf.minFingers && conf.fingers < conf.minFingers) {
			self.fingers = conf.fingers;
			self.state = "end";
			conf.listener(event, self);
		}
	};
	// Generate maintenance commands, and other configurations.
	var self = root.pointerSetup(conf);
	// Attach events.
	eventjs.add(conf.target, "mousedown", conf.onPointerDown);
	// Return this object.
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.gesture = root.gesture;

return root;

})(eventjs.proxy);
/*:
	"Pointer" event proxy (1+ fingers).
	----------------------------------------------------
	CONFIGURE: minFingers, maxFingers.
	----------------------------------------------------
	eventjs.add(window, "gesture", function(event, self) {
		console.log(self.rotation, self.scale, self.fingers, self.state);
	});
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

root.pointerdown =
root.pointermove =
root.pointerup = function(conf) {
	conf.gesture = conf.gesture || "pointer";
	if (conf.target.isPointerEmitter) return;
	// Tracking the events.
	var isDown = true;
	conf.onPointerDown = function (event) {
		isDown = false;
		self.gesture = "pointerdown";
		conf.listener(event, self);
	};
	conf.onPointerMove = function (event) {
		self.gesture = "pointermove";
		conf.listener(event, self, isDown);
	};
	conf.onPointerUp = function (event) {
		isDown = true;
		self.gesture = "pointerup";
		conf.listener(event, self, true);
	};
	// Generate maintenance commands, and other configurations.
	var self = root.pointerSetup(conf);
	// Attach events.
	eventjs.add(conf.target, "mousedown", conf.onPointerDown);
	eventjs.add(conf.target, "mousemove", conf.onPointerMove);
	eventjs.add(conf.doc, "mouseup", conf.onPointerUp);
	// Return this object.
	conf.target.isPointerEmitter = true;
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.pointerdown = root.pointerdown;
eventjs.Gesture._gestureHandlers.pointermove = root.pointermove;
eventjs.Gesture._gestureHandlers.pointerup = root.pointerup;

return root;

})(eventjs.proxy);
/*:
	"Device Motion" and "Shake" event proxy.
	----------------------------------------------------
	http://developer.android.com/reference/android/hardware/Sensoreventjs.html#values
	----------------------------------------------------
	eventjs.add(window, "shake", function(event, self) {});
	eventjs.add(window, "devicemotion", function(event, self) {
		console.log(self.acceleration, self.accelerationIncludingGravity);
	});
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

root.shake = function(conf) {
	// Externally accessible data.
	var self = {
		gesture: "devicemotion",
		acceleration: {},
		accelerationIncludingGravity: {},
		target: conf.target,
		listener: conf.listener,
		remove: function() {
			window.removeEventListener('devicemotion', onDeviceMotion, false);
		}
	};
	// Setting up local variables.
	var threshold = 4; // Gravitational threshold.
	var timeout = 1000; // Timeout between shake events.
	var timeframe = 200; // Time between shakes.
	var shakes = 3; // Minimum shakes to trigger event.
	var lastShake = (new Date()).getTime();
	var gravity = { x: 0, y: 0, z: 0 };
	var delta = {
		x: { count: 0, value: 0 },
		y: { count: 0, value: 0 },
		z: { count: 0, value: 0 }
	};
	// Tracking the events.
	var onDeviceMotion = function(e) {
		var alpha = 0.8; // Low pass filter.
		var o = e.accelerationIncludingGravity;
		gravity.x = alpha * gravity.x + (1 - alpha) * o.x;
		gravity.y = alpha * gravity.y + (1 - alpha) * o.y;
		gravity.z = alpha * gravity.z + (1 - alpha) * o.z;
		self.accelerationIncludingGravity = gravity;
		self.acceleration.x = o.x - gravity.x;
		self.acceleration.y = o.y - gravity.y;
		self.acceleration.z = o.z - gravity.z;
		///
		if (conf.gesture === "devicemotion") {
			conf.listener(e, self);
			return;
		}
		var data = "xyz";
		var now = (new Date()).getTime();
		for (var n = 0, length = data.length; n < length; n ++) {
			var letter = data[n];
			var ACCELERATION = self.acceleration[letter];
			var DELTA = delta[letter];
			var abs = Math.abs(ACCELERATION);
			/// Check whether another shake event was recently registered.
			if (now - lastShake < timeout) continue;
			/// Check whether delta surpasses threshold.
			if (abs > threshold) {
				var idx = now * ACCELERATION / abs;
				var span = Math.abs(idx + DELTA.value);
				// Check whether last delta was registered within timeframe.
				if (DELTA.value && span < timeframe) {
					DELTA.value = idx;
					DELTA.count ++;
					// Check whether delta count has enough shakes.
					if (DELTA.count === shakes) {
						conf.listener(e, self);
						// Reset tracking.
						lastShake = now;
						DELTA.value = 0;
						DELTA.count = 0;
					}
				} else {
					// Track first shake.
					DELTA.value = idx;
					DELTA.count = 1;
				}
			}
		}
	};
	// Attach events.
	if (!window.addEventListener) return;
	window.addEventListener('devicemotion', onDeviceMotion, false);
	// Return this object.
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.shake = root.shake;

return root;

})(eventjs.proxy);
/*:
	"Swipe" event proxy (1+ fingers).
	----------------------------------------------------
	CONFIGURE: snap, threshold, maxFingers.
	----------------------------------------------------
	eventjs.add(window, "swipe", function(event, self) {
		console.log(self.velocity, self.angle);
	});
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

var RAD_DEG = Math.PI / 180;

root.swipe = function(conf) {
	conf.snap = conf.snap || 90; // angle snap.
	conf.threshold = conf.threshold || 1; // velocity threshold.
	conf.gesture = conf.gesture || "swipe";
	// Tracking the events.
	conf.onPointerDown = function (event) {
		if (root.pointerStart(event, self, conf)) {
			eventjs.add(conf.doc, "mousemove", conf.onPointerMove).listener(event);
			eventjs.add(conf.doc, "mouseup", conf.onPointerUp);
		}
	};
	conf.onPointerMove = function (event) {
		var touches = event.changedTouches || root.getCoords(event);
		var length = touches.length;
		for (var i = 0; i < length; i ++) {
			var touch = touches[i];
			var sid = touch.identifier || Infinity;
			var o = conf.tracker[sid];
			// Identifier defined outside of listener.
			if (!o) continue;
			o.move.x = touch.pageX;
			o.move.y = touch.pageY;
			o.moveTime = (new Date()).getTime();
		}
	};
	conf.onPointerUp = function(event) {
		if (root.pointerEnd(event, self, conf)) {
			eventjs.remove(conf.doc, "mousemove", conf.onPointerMove);
			eventjs.remove(conf.doc, "mouseup", conf.onPointerUp);
			///
			var velocity1;
			var velocity2
			var degree1;
			var degree2;
			/// Calculate centroid of gesture.
			var start = { x: 0, y: 0 };
			var endx = 0;
			var endy = 0;
			var length = 0;
			///
			for (var sid in conf.tracker) {
				var touch = conf.tracker[sid];
				var xdist = touch.move.x - touch.start.x;
				var ydist = touch.move.y - touch.start.y;
				///
				endx += touch.move.x;
				endy += touch.move.y;
				start.x += touch.start.x;
				start.y += touch.start.y;
				length ++;
				///
				var distance = Math.sqrt(xdist * xdist + ydist * ydist);
				var ms = touch.moveTime - touch.startTime;
				var degree2 = Math.atan2(xdist, ydist) / RAD_DEG + 180;
				var velocity2 = ms ? distance / ms : 0;
				if (typeof(degree1) === "undefined") {
					degree1 = degree2;
					velocity1 = velocity2;
				} else if (Math.abs(degree2 - degree1) <= 20) {
					degree1 = (degree1 + degree2) / 2;
					velocity1 = (velocity1 + velocity2) / 2;
				} else {
					return;
				}
			}
			///
			var fingers = conf.gestureFingers;
			if (conf.minFingers <= fingers && conf.maxFingers >= fingers) {
				if (velocity1 > conf.threshold) {
					start.x /= length;
					start.y /= length;
					self.start = start;
					self.x = endx / length;
					self.y = endy / length;
					self.angle = -((((degree1 / conf.snap + 0.5) >> 0) * conf.snap || 360) - 360);
					self.velocity = velocity1;
					self.fingers = fingers;
					self.state = "swipe";
					conf.listener(event, self);
				}
			}
		}
	};
	// Generate maintenance commands, and other configurations.
	var self = root.pointerSetup(conf);
	// Attach events.
	eventjs.add(conf.target, "mousedown", conf.onPointerDown);
	// Return this object.
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.swipe = root.swipe;

return root;

})(eventjs.proxy);
/*:
	"Tap" and "Longpress" event proxy.
	----------------------------------------------------
	CONFIGURE: delay (longpress), timeout (tap).
	----------------------------------------------------
	eventjs.add(window, "tap", function(event, self) {
		console.log(self.fingers);
	});
	----------------------------------------------------
	multi-finger tap // touch an target for <= 250ms.
	multi-finger longpress // touch an target for >= 500ms
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

root.longpress = function(conf) {
	conf.gesture = "longpress";
	return root.tap(conf);
};

root.tap = function(conf) {
	conf.delay = conf.delay || 500;
	conf.timeout = conf.timeout || 250;
	conf.driftDeviance = conf.driftDeviance || 10;
	conf.gesture = conf.gesture || "tap";
	// Setting up local variables.
	var timestamp, timeout;
	// Tracking the events.
	conf.onPointerDown = function (event) {
		if (root.pointerStart(event, self, conf)) {
			timestamp = (new Date()).getTime();
			// Initialize event listeners.
			eventjs.add(conf.doc, "mousemove", conf.onPointerMove).listener(event);
			eventjs.add(conf.doc, "mouseup", conf.onPointerUp);
			// Make sure this is a "longpress" event.
			if (conf.gesture !== "longpress") return;
			timeout = setTimeout(function() {
				if (event.cancelBubble && ++event.cancelBubbleCount > 1) return;
				// Make sure no fingers have been changed.
				var fingers = 0;
				for (var key in conf.tracker) {
					var point = conf.tracker[key];
					if (point.end === true) return;
					if (conf.cancel) return;
					fingers ++;
				}
				// Send callback.
				if (conf.minFingers <= fingers && conf.maxFingers >= fingers) {
					self.state = "start";
					self.fingers = fingers;
					self.x = point.start.x;
					self.y = point.start.y;
					conf.listener(event, self);
				}
			}, conf.delay);
		}
	};
	conf.onPointerMove = function (event) {
		var bbox = conf.bbox;
		var touches = event.changedTouches || root.getCoords(event);
		var length = touches.length;
		for (var i = 0; i < length; i ++) {
			var touch = touches[i];
			var identifier = touch.identifier || Infinity;
			var pt = conf.tracker[identifier];
			if (!pt) continue;
			var x = (touch.pageX - bbox.x1 - parseInt(window.scrollX));
			var y = (touch.pageY - bbox.y1 - parseInt(window.scrollY));
			///
			var dx = x - pt.start.x;
			var dy = y - pt.start.y;
			var distance = Math.sqrt(dx * dx + dy * dy);
			if (!(x > 0 && x < bbox.width && // Within target coordinates..
				  y > 0 && y < bbox.height &&
				  distance <= conf.driftDeviance)) { // Within drift deviance.
				// Cancel out this listener.
				eventjs.remove(conf.doc, "mousemove", conf.onPointerMove);
				conf.cancel = true;
				return;
			}
		}
	};
	conf.onPointerUp = function(event) {
		if (root.pointerEnd(event, self, conf)) {
			clearTimeout(timeout);
			eventjs.remove(conf.doc, "mousemove", conf.onPointerMove);
			eventjs.remove(conf.doc, "mouseup", conf.onPointerUp);
			if (event.cancelBubble && ++event.cancelBubbleCount > 1) return;
			// Callback release on longpress.
			if (conf.gesture === "longpress") {
				if (self.state === "start") {
					self.state = "end";
					conf.listener(event, self);
				}
				return;
			}
			// Cancel event due to movement.
			if (conf.cancel) return;
			// Ensure delay is within margins.
			if ((new Date()).getTime() - timestamp > conf.timeout) return;
			// Send callback.
			var fingers = conf.gestureFingers;
			if (conf.minFingers <= fingers && conf.maxFingers >= fingers) {
				self.state = "tap";
				self.fingers = conf.gestureFingers;
				conf.listener(event, self);
			}
		}
	};
	// Generate maintenance commands, and other configurations.
	var self = root.pointerSetup(conf);
	// Attach events.
	eventjs.add(conf.target, "mousedown", conf.onPointerDown);
	// Return this object.
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.tap = root.tap;
eventjs.Gesture._gestureHandlers.longpress = root.longpress;

return root;

})(eventjs.proxy);
/*:
	"Mouse Wheel" event proxy.
	----------------------------------------------------
	eventjs.add(window, "wheel", function(event, self) {
		console.log(self.state, self.wheelDelta);
	});
*/

if (typeof(eventjs) === "undefined") var eventjs = {};
if (typeof(eventjs.proxy) === "undefined") eventjs.proxy = {};

eventjs.proxy = (function(root) { "use strict";

root.wheelPreventElasticBounce = function(el) {
	if (!el) return;
	if (typeof(el) === "string") el = document.querySelector(el);
	eventjs.add(el, "wheel", function(event, self) {
		self.preventElasticBounce();
		eventjs.stop(event);
	});
};

root.wheel = function(conf) {
	// Configure event listener.
	var interval;
	var timeout = conf.timeout || 150;
	var count = 0;
	// Externally accessible data.
	var self = {
		gesture: "wheel",
		state: "start",
		wheelDelta: 0,
		target: conf.target,
		listener: conf.listener,
		preventElasticBounce: function(event) {
			var target = this.target;
			var scrollTop = target.scrollTop;
			var top = scrollTop + target.offsetHeight;
			var height = target.scrollHeight;
			if (top === height && this.wheelDelta <= 0) eventjs.cancel(event);
			else if (scrollTop === 0 && this.wheelDelta >= 0) eventjs.cancel(event);
			eventjs.stop(event);
		},
		add: function() {
			conf.target[add](type, onMouseWheel, false);
		},
		remove: function() {
			conf.target[remove](type, onMouseWheel, false);
		}
	};
	// Tracking the events.
	var onMouseWheel = function(event) {
		event = event || window.event;
		self.state = count++ ? "change" : "start";
		self.wheelDelta = event.detail ? event.detail * -20 : event.wheelDelta;
		conf.listener(event, self);
		clearTimeout(interval);
		interval = setTimeout(function() {
			count = 0;
			self.state = "end";
			self.wheelDelta = 0;
			conf.listener(event, self);
		}, timeout);
	};
	// Attach events.
	var add = document.addEventListener ? "addEventListener" : "attachEvent";
	var remove = document.removeEventListener ? "removeEventListener" : "detachEvent";
	var type = eventjs.getEventSupport("mousewheel") ? "mousewheel" : "DOMMouseScroll";
	conf.target[add](type, onMouseWheel, false);
	// Return this object.
	return self;
};

eventjs.Gesture = eventjs.Gesture || {};
eventjs.Gesture._gestureHandlers = eventjs.Gesture._gestureHandlers || {};
eventjs.Gesture._gestureHandlers.wheel = root.wheel;

return root;

})(eventjs.proxy);
/*
	"Orientation Change"
	----------------------------------------------------
	https://developer.apple.com/library/safari/documentation/SafariDOMAdditions/Reference/DeviceOrientationEventClassRef/DeviceOrientationEvent/DeviceOrientationEvent.html#//apple_ref/doc/uid/TP40010526
	----------------------------------------------------
	Event.add(window, "deviceorientation", function(event, self) {});
*/

if (typeof(Event) === "undefined") var Event = {};
if (typeof(Event.proxy) === "undefined") Event.proxy = {};

Event.proxy = (function(root) { "use strict";

root.orientation = function(conf) {
	// Externally accessible data.
	var self = {
		gesture: "orientationchange",
		previous: null, /* Report the previous orientation */
		current: window.orientation,
		target: conf.target,
		listener: conf.listener,
		remove: function() {
			window.removeEventListener('orientationchange', onOrientationChange, false);
		}
	};

	// Tracking the events.
	var onOrientationChange = function(e) {

		self.previous = self.current;
		self.current = window.orientation;
	    if(self.previous !== null && self.previous != self.current) {
			conf.listener(e, self);
			return;
	    }


	};
	// Attach events.
	if (window.DeviceOrientationEvent) {
    	window.addEventListener("orientationchange", onOrientationChange, false);
  	}
	// Return this object.
	return self;
};

Event.Gesture = Event.Gesture || {};
Event.Gesture._gestureHandlers = Event.Gesture._gestureHandlers || {};
Event.Gesture._gestureHandlers.orientation = root.orientation;

return root;

})(Event.proxy);
(function() {

  /**
   * @private
   * @param {String} eventName
   * @param {Function} handler
   */
  function _removeEventListener(eventName, handler) {
    if (!this.__eventListeners[eventName]) {
      return;
    }
    var eventListener = this.__eventListeners[eventName];
    if (handler) {
      eventListener[eventListener.indexOf(handler)] = false;
    }
    else {
      fabric.util.array.fill(eventListener, false);
    }
  }

  /**
   * Observes specified event
   * @memberOf fabric.Observable
   * @alias on
   * @param {String|Object} eventName Event name (eg. 'after:render') or object with key/value pairs (eg. {'after:render': handler, 'selection:cleared': handler})
   * @param {Function} handler Function that receives a notification when an event of the specified type occurs
   * @return {Self} thisArg
   * @chainable
   */
  function on(eventName, handler) {
    if (!this.__eventListeners) {
      this.__eventListeners = { };
    }
    // one object with key/value pairs was passed
    if (arguments.length === 1) {
      for (var prop in eventName) {
        this.on(prop, eventName[prop]);
      }
    }
    else {
      if (!this.__eventListeners[eventName]) {
        this.__eventListeners[eventName] = [];
      }
      this.__eventListeners[eventName].push(handler);
    }
    return this;
  }

  function _once(eventName, handler) {
    var _handler = function () {
      handler.apply(this, arguments);
      this.off(eventName, _handler);
    }.bind(this);
    this.on(eventName, _handler);
  }

  function once(eventName, handler) {
    // one object with key/value pairs was passed
    if (arguments.length === 1) {
      for (var prop in eventName) {
        _once.call(this, prop, eventName[prop]);
      }
    }
    else {
      _once.call(this, eventName, handler);
    }
    return this;
  }

  /**
   * Stops event observing for a particular event handler. Calling this method
   * without arguments removes all handlers for all events
   * @memberOf fabric.Observable
   * @alias off
   * @param {String|Object} eventName Event name (eg. 'after:render') or object with key/value pairs (eg. {'after:render': handler, 'selection:cleared': handler})
   * @param {Function} handler Function to be deleted from EventListeners
   * @return {Self} thisArg
   * @chainable
   */
  function off(eventName, handler) {
    if (!this.__eventListeners) {
      return this;
    }

    // remove all key/value pairs (event name -> event handler)
    if (arguments.length === 0) {
      for (eventName in this.__eventListeners) {
        _removeEventListener.call(this, eventName);
      }
    }
    // one object with key/value pairs was passed
    else if (arguments.length === 1 && typeof arguments[0] === 'object') {
      for (var prop in eventName) {
        _removeEventListener.call(this, prop, eventName[prop]);
      }
    }
    else {
      _removeEventListener.call(this, eventName, handler);
    }
    return this;
  }

  /**
   * Fires event with an optional options object
   * @memberOf fabric.Observable
   * @param {String} eventName Event name to fire
   * @param {Object} [options] Options object
   * @return {Self} thisArg
   * @chainable
   */
  function fire(eventName, options) {
    if (!this.__eventListeners) {
      return this;
    }

    var listenersForEvent = this.__eventListeners[eventName];
    if (!listenersForEvent) {
      return this;
    }

    for (var i = 0, len = listenersForEvent.length; i < len; i++) {
      listenersForEvent[i] && listenersForEvent[i].call(this, options || { });
    }
    this.__eventListeners[eventName] = listenersForEvent.filter(function(value) {
      return value !== false;
    });
    return this;
  }

  /**
   * @namespace fabric.Observable
   * @tutorial {@link http://fabric5.fabricjs.com/fabric-intro-part-2#events}
   * @see {@link http://fabric5.fabricjs.com/events|Events demo}
   */
  fabric.Observable = {
    fire: fire,
    on: on,
    once: once,
    off: off,
  };
})();
/**
 * @namespace fabric.Collection
 */
fabric.Collection = {

  _objects: [],

  /**
   * Adds objects to collection, Canvas or Group, then renders canvas
   * (if `renderOnAddRemove` is not `false`).
   * in case of Group no changes to bounding box are made.
   * Objects should be instances of (or inherit from) fabric.Object
   * Use of this function is highly discouraged for groups.
   * you can add a bunch of objects with the add method but then you NEED
   * to run a addWithUpdate call for the Group class or position/bbox will be wrong.
   * @param {...fabric.Object} object Zero or more fabric instances
   * @return {Self} thisArg
   * @chainable
   */
  add: function () {
    this._objects.push.apply(this._objects, arguments);
    if (this._onObjectAdded) {
      for (var i = 0, length = arguments.length; i < length; i++) {
        this._onObjectAdded(arguments[i]);
      }
    }
    this.renderOnAddRemove && this.requestRenderAll();
    return this;
  },

  /**
   * Inserts an object into collection at specified index, then renders canvas (if `renderOnAddRemove` is not `false`)
   * An object should be an instance of (or inherit from) fabric.Object
   * Use of this function is highly discouraged for groups.
   * you can add a bunch of objects with the insertAt method but then you NEED
   * to run a addWithUpdate call for the Group class or position/bbox will be wrong.
   * @param {Object} object Object to insert
   * @param {Number} index Index to insert object at
   * @param {Boolean} nonSplicing When `true`, no splicing (shifting) of objects occurs
   * @return {Self} thisArg
   * @chainable
   */
  insertAt: function (object, index, nonSplicing) {
    var objects = this._objects;
    if (nonSplicing) {
      objects[index] = object;
    }
    else {
      objects.splice(index, 0, object);
    }
    this._onObjectAdded && this._onObjectAdded(object);
    this.renderOnAddRemove && this.requestRenderAll();
    return this;
  },

  /**
   * Removes objects from a collection, then renders canvas (if `renderOnAddRemove` is not `false`)
   * @param {...fabric.Object} object Zero or more fabric instances
   * @return {Self} thisArg
   * @chainable
   */
  remove: function() {
    var objects = this._objects,
        index, somethingRemoved = false;

    for (var i = 0, length = arguments.length; i < length; i++) {
      index = objects.indexOf(arguments[i]);

      // only call onObjectRemoved if an object was actually removed
      if (index !== -1) {
        somethingRemoved = true;
        objects.splice(index, 1);
        this._onObjectRemoved && this._onObjectRemoved(arguments[i]);
      }
    }

    this.renderOnAddRemove && somethingRemoved && this.requestRenderAll();
    return this;
  },

  /**
   * Executes given function for each object in this group
   * @param {Function} callback
   *                   Callback invoked with current object as first argument,
   *                   index - as second and an array of all objects - as third.
   *                   Callback is invoked in a context of Global Object (e.g. `window`)
   *                   when no `context` argument is given
   *
   * @param {Object} context Context (aka thisObject)
   * @return {Self} thisArg
   * @chainable
   */
  forEachObject: function(callback, context) {
    var objects = this.getObjects();
    for (var i = 0, len = objects.length; i < len; i++) {
      callback.call(context, objects[i], i, objects);
    }
    return this;
  },

  /**
   * Returns an array of children objects of this instance
   * Type parameter introduced in 1.3.10
   * since 2.3.5 this method return always a COPY of the array;
   * @param {String} [type] When specified, only objects of this type are returned
   * @return {Array}
   */
  getObjects: function(type) {
    if (typeof type === 'undefined') {
      return this._objects.concat();
    }
    return this._objects.filter(function(o) {
      return o.type === type;
    });
  },

  /**
   * Returns object at specified index
   * @param {Number} index
   * @return {Self} thisArg
   */
  item: function (index) {
    return this._objects[index];
  },

  /**
   * Returns true if collection contains no objects
   * @return {Boolean} true if collection is empty
   */
  isEmpty: function () {
    return this._objects.length === 0;
  },

  /**
   * Returns a size of a collection (i.e: length of an array containing its objects)
   * @return {Number} Collection size
   */
  size: function() {
    return this._objects.length;
  },

  /**
   * Returns true if collection contains an object
   * @param {Object} object Object to check against
   * @param {Boolean} [deep=false] `true` to check all descendants, `false` to check only `_objects`
   * @return {Boolean} `true` if collection contains an object
   */
  contains: function (object, deep) {
    if (this._objects.indexOf(object) > -1) {
      return true;
    }
    else if (deep) {
      return this._objects.some(function (obj) {
        return typeof obj.contains === 'function' && obj.contains(object, true);
      });
    }
    return false;
  },

  /**
   * Returns number representation of a collection complexity
   * @return {Number} complexity
   */
  complexity: function () {
    return this._objects.reduce(function (memo, current) {
      memo += current.complexity ? current.complexity() : 0;
      return memo;
    }, 0);
  }
};
/**
 * @namespace fabric.CommonMethods
 */
fabric.CommonMethods = {

  /**
   * Sets object's properties from options
   * @param {Object} [options] Options object
   */
  _setOptions: function(options) {
    for (var prop in options) {
      this.set(prop, options[prop]);
    }
  },

  /**
   * @private
   * @param {Object} [filler] Options object
   * @param {String} [property] property to set the Gradient to
   */
  _initGradient: function(filler, property) {
    if (filler && filler.colorStops && !(filler instanceof fabric.Gradient)) {
      this.set(property, new fabric.Gradient(filler));
    }
  },

  /**
   * @private
   * @param {Object} [filler] Options object
   * @param {String} [property] property to set the Pattern to
   * @param {Function} [callback] callback to invoke after pattern load
   */
  _initPattern: function(filler, property, callback) {
    if (filler && filler.source && !(filler instanceof fabric.Pattern)) {
      this.set(property, new fabric.Pattern(filler, callback));
    }
    else {
      callback && callback();
    }
  },

  /**
   * @private
   */
  _setObject: function(obj) {
    for (var prop in obj) {
      this._set(prop, obj[prop]);
    }
  },

  /**
   * Sets property to a given value. When changing position/dimension -related properties (left, top, scale, angle, etc.) `set` does not update position of object's borders/controls. If you need to update those, call `setCoords()`.
   * @param {String|Object} key Property name or object (if object, iterate over the object properties)
   * @param {Object|Function} value Property value (if function, the value is passed into it and its return value is used as a new one)
   * @return {fabric.Object} thisArg
   * @chainable
   */
  set: function(key, value) {
    if (typeof key === 'object') {
      this._setObject(key);
    }
    else {
      this._set(key, value);
    }
    return this;
  },

  _set: function(key, value) {
    this[key] = value;
  },

  /**
   * Toggles specified property from `true` to `false` or from `false` to `true`
   * @param {String} property Property to toggle
   * @return {fabric.Object} thisArg
   * @chainable
   */
  toggle: function(property) {
    var value = this.get(property);
    if (typeof value === 'boolean') {
      this.set(property, !value);
    }
    return this;
  },

  /**
   * Basic getter
   * @param {String} property Property name
   * @return {*} value of a property
   */
  get: function(property) {
    return this[property];
  }
};
(function(global) {

  var sqrt = Math.sqrt,
      atan2 = Math.atan2,
      pow = Math.pow,
      PiBy180 = Math.PI / 180,
      PiBy2 = Math.PI / 2;

  /**
   * @namespace fabric.util
   */
  fabric.util = {

    /**
     * Calculate the cos of an angle, avoiding returning floats for known results
     * @static
     * @memberOf fabric.util
     * @param {Number} angle the angle in radians or in degree
     * @return {Number}
     */
    cos: function(angle) {
      if (angle === 0) { return 1; }
      if (angle < 0) {
        // cos(a) = cos(-a)
        angle = -angle;
      }
      var angleSlice = angle / PiBy2;
      switch (angleSlice) {
        case 1: case 3: return 0;
        case 2: return -1;
      }
      return Math.cos(angle);
    },

    /**
     * Calculate the sin of an angle, avoiding returning floats for known results
     * @static
     * @memberOf fabric.util
     * @param {Number} angle the angle in radians or in degree
     * @return {Number}
     */
    sin: function(angle) {
      if (angle === 0) { return 0; }
      var angleSlice = angle / PiBy2, sign = 1;
      if (angle < 0) {
        // sin(-a) = -sin(a)
        sign = -1;
      }
      switch (angleSlice) {
        case 1: return sign;
        case 2: return 0;
        case 3: return -sign;
      }
      return Math.sin(angle);
    },

    /**
     * Removes value from an array.
     * Presence of value (and its position in an array) is determined via `Array.prototype.indexOf`
     * @static
     * @memberOf fabric.util
     * @param {Array} array
     * @param {*} value
     * @return {Array} original array
     */
    removeFromArray: function(array, value) {
      var idx = array.indexOf(value);
      if (idx !== -1) {
        array.splice(idx, 1);
      }
      return array;
    },

    /**
     * Returns random number between 2 specified ones.
     * @static
     * @memberOf fabric.util
     * @param {Number} min lower limit
     * @param {Number} max upper limit
     * @return {Number} random value (between min and max)
     */
    getRandomInt: function(min, max) {
      return Math.floor(Math.random() * (max - min + 1)) + min;
    },

    /**
     * Transforms degrees to radians.
     * @static
     * @memberOf fabric.util
     * @param {Number} degrees value in degrees
     * @return {Number} value in radians
     */
    degreesToRadians: function(degrees) {
      return degrees * PiBy180;
    },

    /**
     * Transforms radians to degrees.
     * @static
     * @memberOf fabric.util
     * @param {Number} radians value in radians
     * @return {Number} value in degrees
     */
    radiansToDegrees: function(radians) {
      return radians / PiBy180;
    },

    /**
     * Rotates `point` around `origin` with `radians`
     * @static
     * @memberOf fabric.util
     * @param {fabric.Point} point The point to rotate
     * @param {fabric.Point} origin The origin of the rotation
     * @param {Number} radians The radians of the angle for the rotation
     * @return {fabric.Point} The new rotated point
     */
    rotatePoint: function(point, origin, radians) {
      var newPoint = new fabric.Point(point.x - origin.x, point.y - origin.y),
          v = fabric.util.rotateVector(newPoint, radians);
      return new fabric.Point(v.x, v.y).addEquals(origin);
    },

    /**
     * Rotates `vector` with `radians`
     * @static
     * @memberOf fabric.util
     * @param {Object} vector The vector to rotate (x and y)
     * @param {Number} radians The radians of the angle for the rotation
     * @return {Object} The new rotated point
     */
    rotateVector: function(vector, radians) {
      var sin = fabric.util.sin(radians),
          cos = fabric.util.cos(radians),
          rx = vector.x * cos - vector.y * sin,
          ry = vector.x * sin + vector.y * cos;
      return {
        x: rx,
        y: ry
      };
    },

    /**
     * Creates a vetor from points represented as a point
     * @static
     * @memberOf fabric.util
     *
     * @typedef {Object} Point
     * @property {number} x
     * @property {number} y
     *
     * @param {Point} from
     * @param {Point} to
     * @returns {Point} vector
     */
    createVector: function (from, to) {
      return new fabric.Point(to.x - from.x, to.y - from.y);
    },

    /**
     * Calculates angle between 2 vectors using dot product
     * @static
     * @memberOf fabric.util
     * @param {Point} a
     * @param {Point} b
     * @returns the angle in radian between the vectors
     */
    calcAngleBetweenVectors: function (a, b) {
      return Math.acos((a.x * b.x + a.y * b.y) / (Math.hypot(a.x, a.y) * Math.hypot(b.x, b.y)));
    },

    /**
     * @static
     * @memberOf fabric.util
     * @param {Point} v
     * @returns {Point} vector representing the unit vector of pointing to the direction of `v`
     */
    getHatVector: function (v) {
      return new fabric.Point(v.x, v.y).multiply(1 / Math.hypot(v.x, v.y));
    },

    /**
     * @static
     * @memberOf fabric.util
     * @param {Point} A
     * @param {Point} B
     * @param {Point} C
     * @returns {{ vector: Point, angle: number }} vector representing the bisector of A and A's angle
     */
    getBisector: function (A, B, C) {
      var AB = fabric.util.createVector(A, B), AC = fabric.util.createVector(A, C);
      var alpha = fabric.util.calcAngleBetweenVectors(AB, AC);
      //  check if alpha is relative to AB->BC
      var ro = fabric.util.calcAngleBetweenVectors(fabric.util.rotateVector(AB, alpha), AC);
      var phi = alpha * (ro === 0 ? 1 : -1) / 2;
      return {
        vector: fabric.util.getHatVector(fabric.util.rotateVector(AB, phi)),
        angle: alpha
      };
    },

    /**
     * Project stroke width on points returning 2 projections for each point as follows:
     * - `miter`: 2 points corresponding to the outer boundary and the inner boundary of stroke.
     * - `bevel`: 2 points corresponding to the bevel boundaries, tangent to the bisector.
     * - `round`: same as `bevel`
     * Used to calculate object's bounding box
     * @static
     * @memberOf fabric.util
     * @param {Point[]} points
     * @param {Object} options
     * @param {number} options.strokeWidth
     * @param {'miter'|'bevel'|'round'} options.strokeLineJoin
     * @param {number} options.strokeMiterLimit https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/stroke-miterlimit
     * @param {boolean} options.strokeUniform
     * @param {number} options.scaleX
     * @param {number} options.scaleY
     * @param {boolean} [openPath] whether the shape is open or not, affects the calculations of the first and last points
     * @returns {fabric.Point[]} array of size 2n/4n of all suspected points
     */
    projectStrokeOnPoints: function (points, options, openPath) {
      var coords = [], s = options.strokeWidth / 2,
          strokeUniformScalar = options.strokeUniform ?
            new fabric.Point(1 / options.scaleX, 1 / options.scaleY) : new fabric.Point(1, 1),
          getStrokeHatVector = function (v) {
            var scalar = s / (Math.hypot(v.x, v.y));
            return new fabric.Point(v.x * scalar * strokeUniformScalar.x, v.y * scalar * strokeUniformScalar.y);
          };
      if (points.length <= 1) {return coords;}
      points.forEach(function (p, index) {
        var A = new fabric.Point(p.x, p.y), B, C;
        if (index === 0) {
          C = points[index + 1];
          B = openPath ? getStrokeHatVector(fabric.util.createVector(C, A)).addEquals(A) : points[points.length - 1];
        }
        else if (index === points.length - 1) {
          B = points[index - 1];
          C = openPath ? getStrokeHatVector(fabric.util.createVector(B, A)).addEquals(A) : points[0];
        }
        else {
          B = points[index - 1];
          C = points[index + 1];
        }
        var bisector = fabric.util.getBisector(A, B, C),
            bisectorVector = bisector.vector,
            alpha = bisector.angle,
            scalar,
            miterVector;
        if (options.strokeLineJoin === 'miter') {
          scalar = -s / Math.sin(alpha / 2);
          miterVector = new fabric.Point(
            bisectorVector.x * scalar * strokeUniformScalar.x,
            bisectorVector.y * scalar * strokeUniformScalar.y
          );
          if (Math.hypot(miterVector.x, miterVector.y) / s <= options.strokeMiterLimit) {
            coords.push(A.add(miterVector));
            coords.push(A.subtract(miterVector));
            return;
          }
        }
        scalar = -s * Math.SQRT2;
        miterVector = new fabric.Point(
          bisectorVector.x * scalar * strokeUniformScalar.x,
          bisectorVector.y * scalar * strokeUniformScalar.y
        );
        coords.push(A.add(miterVector));
        coords.push(A.subtract(miterVector));
      });
      return coords;
    },

    /**
     * Apply transform t to point p
     * @static
     * @memberOf fabric.util
     * @param  {fabric.Point} p The point to transform
     * @param  {Array} t The transform
     * @param  {Boolean} [ignoreOffset] Indicates that the offset should not be applied
     * @return {fabric.Point} The transformed point
     */
    transformPoint: function(p, t, ignoreOffset) {
      if (ignoreOffset) {
        return new fabric.Point(
          t[0] * p.x + t[2] * p.y,
          t[1] * p.x + t[3] * p.y
        );
      }
      return new fabric.Point(
        t[0] * p.x + t[2] * p.y + t[4],
        t[1] * p.x + t[3] * p.y + t[5]
      );
    },

    /**
     * Returns coordinates of points's bounding rectangle (left, top, width, height)
     * @param {Array} points 4 points array
     * @param {Array} [transform] an array of 6 numbers representing a 2x3 transform matrix
     * @return {Object} Object with left, top, width, height properties
     */
    makeBoundingBoxFromPoints: function(points, transform) {
      if (transform) {
        for (var i = 0; i < points.length; i++) {
          points[i] = fabric.util.transformPoint(points[i], transform);
        }
      }
      var xPoints = [points[0].x, points[1].x, points[2].x, points[3].x],
          minX = fabric.util.array.min(xPoints),
          maxX = fabric.util.array.max(xPoints),
          width = maxX - minX,
          yPoints = [points[0].y, points[1].y, points[2].y, points[3].y],
          minY = fabric.util.array.min(yPoints),
          maxY = fabric.util.array.max(yPoints),
          height = maxY - minY;

      return {
        left: minX,
        top: minY,
        width: width,
        height: height
      };
    },

    /**
     * Invert transformation t
     * @static
     * @memberOf fabric.util
     * @param {Array} t The transform
     * @return {Array} The inverted transform
     */
    invertTransform: function(t) {
      var a = 1 / (t[0] * t[3] - t[1] * t[2]),
          r = [a * t[3], -a * t[1], -a * t[2], a * t[0]],
          o = fabric.util.transformPoint({ x: t[4], y: t[5] }, r, true);
      r[4] = -o.x;
      r[5] = -o.y;
      return r;
    },

    /**
     * A wrapper around Number#toFixed, which contrary to native method returns number, not string.
     * @static
     * @memberOf fabric.util
     * @param {Number|String} number number to operate on
     * @param {Number} fractionDigits number of fraction digits to "leave"
     * @return {Number}
     */
    toFixed: function(number, fractionDigits) {
      return parseFloat(Number(number).toFixed(fractionDigits));
    },

    /**
     * Converts from attribute value to pixel value if applicable.
     * Returns converted pixels or original value not converted.
     * @param {Number|String} value number to operate on
     * @param {Number} fontSize
     * @return {Number|String}
     */
    parseUnit: function(value, fontSize) {
      var unit = /\D{0,2}$/.exec(value),
          number = parseFloat(value);
      if (!fontSize) {
        fontSize = fabric.Text.DEFAULT_SVG_FONT_SIZE;
      }
      switch (unit[0]) {
        case 'mm':
          return number * fabric.DPI / 25.4;

        case 'cm':
          return number * fabric.DPI / 2.54;

        case 'in':
          return number * fabric.DPI;

        case 'pt':
          return number * fabric.DPI / 72; // or * 4 / 3

        case 'pc':
          return number * fabric.DPI / 72 * 12; // or * 16

        case 'em':
          return number * fontSize;

        default:
          return number;
      }
    },

    /**
     * Function which always returns `false`.
     * @static
     * @memberOf fabric.util
     * @return {Boolean}
     */
    falseFunction: function() {
      return false;
    },

    /**
     * Returns klass "Class" object of given namespace
     * @memberOf fabric.util
     * @param {String} type Type of object (eg. 'circle')
     * @param {String} namespace Namespace to get klass "Class" object from
     * @return {Object} klass "Class"
     */
    getKlass: function(type, namespace) {
      // capitalize first letter only
      type = fabric.util.string.camelize(type.charAt(0).toUpperCase() + type.slice(1));
      return fabric.util.resolveNamespace(namespace)[type];
    },

    /**
     * Returns array of attributes for given svg that fabric parses
     * @memberOf fabric.util
     * @param {String} type Type of svg element (eg. 'circle')
     * @return {Array} string names of supported attributes
     */
    getSvgAttributes: function(type) {
      var attributes = [
        'instantiated_by_use',
        'style',
        'id',
        'class'
      ];
      switch (type) {
        case 'linearGradient':
          attributes = attributes.concat(['x1', 'y1', 'x2', 'y2', 'gradientUnits', 'gradientTransform']);
          break;
        case 'radialGradient':
          attributes = attributes.concat(['gradientUnits', 'gradientTransform', 'cx', 'cy', 'r', 'fx', 'fy', 'fr']);
          break;
        case 'stop':
          attributes = attributes.concat(['offset', 'stop-color', 'stop-opacity']);
          break;
      }
      return attributes;
    },

    /**
     * Returns object of given namespace
     * @memberOf fabric.util
     * @param {String} namespace Namespace string e.g. 'fabric.Image.filter' or 'fabric'
     * @return {Object} Object for given namespace (default fabric)
     */
    resolveNamespace: function(namespace) {
      if (!namespace) {
        return fabric;
      }

      var parts = namespace.split('.'),
          len = parts.length, i,
          obj = global || fabric.window;

      for (i = 0; i < len; ++i) {
        obj = obj[parts[i]];
      }

      return obj;
    },

    /**
     * Loads image element from given url and passes it to a callback
     * @memberOf fabric.util
     * @param {String} url URL representing an image
     * @param {Function} callback Callback; invoked with loaded image
     * @param {*} [context] Context to invoke callback in
     * @param {Object} [crossOrigin] crossOrigin value to set image element to
     */
    loadImage: function(url, callback, context, crossOrigin) {
      if (!url) {
        callback && callback.call(context, url);
        return;
      }

      var img = fabric.util.createImage();

      /** @ignore */
      var onLoadCallback = function () {
        callback && callback.call(context, img, false);
        img = img.onload = img.onerror = null;
      };

      img.onload = onLoadCallback;
      /** @ignore */
      img.onerror = function() {
        fabric.log('Error loading ' + img.src);
        callback && callback.call(context, null, true);
        img = img.onload = img.onerror = null;
      };

      // data-urls appear to be buggy with crossOrigin
      // https://github.com/kangax/fabric.js/commit/d0abb90f1cd5c5ef9d2a94d3fb21a22330da3e0a#commitcomment-4513767
      // see https://code.google.com/p/chromium/issues/detail?id=315152
      //     https://bugzilla.mozilla.org/show_bug.cgi?id=935069
      // crossOrigin null is the same as not set.
      if (url.indexOf('data') !== 0 &&
        crossOrigin !== undefined &&
        crossOrigin !== null) {
        img.crossOrigin = crossOrigin;
      }

      // IE10 / IE11-Fix: SVG contents from data: URI
      // will only be available if the IMG is present
      // in the DOM (and visible)
      if (url.substring(0,14) === 'data:image/svg') {
        img.onload = null;
        fabric.util.loadImageInDom(img, onLoadCallback);
      }

      img.src = url;
    },

    /**
     * Attaches SVG image with data: URL to the dom
     * @memberOf fabric.util
     * @param {Object} img Image object with data:image/svg src
     * @param {Function} callback Callback; invoked with loaded image
     * @return {Object} DOM element (div containing the SVG image)
     */
    loadImageInDom: function(img, onLoadCallback) {
      var div = fabric.document.createElement('div');
      div.style.width = div.style.height = '1px';
      div.style.left = div.style.top = '-100%';
      div.style.position = 'absolute';
      div.appendChild(img);
      fabric.document.querySelector('body').appendChild(div);
      /**
       * Wrap in function to:
       *   1. Call existing callback
       *   2. Cleanup DOM
       */
      img.onload = function () {
        onLoadCallback();
        div.parentNode.removeChild(div);
        div = null;
      };
    },

    /**
     * Creates corresponding fabric instances from their object representations
     * @static
     * @memberOf fabric.util
     * @param {Array} objects Objects to enliven
     * @param {Function} callback Callback to invoke when all objects are created
     * @param {String} namespace Namespace to get klass "Class" object from
     * @param {Function} reviver Method for further parsing of object elements,
     * called after each fabric object created.
     */
    enlivenObjects: function(objects, callback, namespace, reviver) {
      objects = objects || [];

      var enlivenedObjects = [],
          numLoadedObjects = 0,
          numTotalObjects = objects.length;

      function onLoaded() {
        if (++numLoadedObjects === numTotalObjects) {
          callback && callback(enlivenedObjects.filter(function(obj) {
            // filter out undefined objects (objects that gave error)
            return obj;
          }));
        }
      }

      if (!numTotalObjects) {
        callback && callback(enlivenedObjects);
        return;
      }

      objects.forEach(function (o, index) {
        // if sparse array
        if (!o || !o.type) {
          onLoaded();
          return;
        }
        var klass = fabric.util.getKlass(o.type, namespace);
        klass.fromObject(o, function (obj, error) {
          error || (enlivenedObjects[index] = obj);
          reviver && reviver(o, obj, error);
          onLoaded();
        });
      });
    },

    /**
     * Creates corresponding fabric instances residing in an object, e.g. `clipPath`
     * @see {@link fabric.Object.ENLIVEN_PROPS}
     * @param {Object} object
     * @param {Object} [context] assign enlived props to this object (pass null to skip this)
     * @param {(objects:fabric.Object[]) => void} callback
     */
    enlivenObjectEnlivables: function (object, context, callback) {
      var enlivenProps = fabric.Object.ENLIVEN_PROPS.filter(function (key) { return !!object[key]; });
      fabric.util.enlivenObjects(enlivenProps.map(function (key) { return object[key]; }), function (enlivedProps) {
        var objects = {};
        enlivenProps.forEach(function (key, index) {
          objects[key] = enlivedProps[index];
          context && (context[key] = enlivedProps[index]);
        });
        callback && callback(objects);
      });
    },

    /**
     * Create and wait for loading of patterns
     * @static
     * @memberOf fabric.util
     * @param {Array} patterns Objects to enliven
     * @param {Function} callback Callback to invoke when all objects are created
     * called after each fabric object created.
     */
    enlivenPatterns: function(patterns, callback) {
      patterns = patterns || [];

      function onLoaded() {
        if (++numLoadedPatterns === numPatterns) {
          callback && callback(enlivenedPatterns);
        }
      }

      var enlivenedPatterns = [],
          numLoadedPatterns = 0,
          numPatterns = patterns.length;

      if (!numPatterns) {
        callback && callback(enlivenedPatterns);
        return;
      }

      patterns.forEach(function (p, index) {
        if (p && p.source) {
          new fabric.Pattern(p, function(pattern) {
            enlivenedPatterns[index] = pattern;
            onLoaded();
          });
        }
        else {
          enlivenedPatterns[index] = p;
          onLoaded();
        }
      });
    },

    /**
     * Groups SVG elements (usually those retrieved from SVG document)
     * @static
     * @memberOf fabric.util
     * @param {Array} elements SVG elements to group
     * @param {Object} [options] Options object
     * @param {String} path Value to set sourcePath to
     * @return {fabric.Object|fabric.Group}
     */
    groupSVGElements: function(elements, options, path) {
      var object;
      if (elements && elements.length === 1) {
        return elements[0];
      }
      if (options) {
        if (options.width && options.height) {
          options.centerPoint = {
            x: options.width / 2,
            y: options.height / 2
          };
        }
        else {
          delete options.width;
          delete options.height;
        }
      }
      object = new fabric.Group(elements, options);
      if (typeof path !== 'undefined') {
        object.sourcePath = path;
      }
      return object;
    },

    /**
     * Populates an object with properties of another object
     * @static
     * @memberOf fabric.util
     * @param {Object} source Source object
     * @param {Object} destination Destination object
     * @return {Array} properties Properties names to include
     */
    populateWithProperties: function(source, destination, properties) {
      if (properties && Array.isArray(properties)) {
        for (var i = 0, len = properties.length; i < len; i++) {
          if (properties[i] in source) {
            destination[properties[i]] = source[properties[i]];
          }
        }
      }
    },

    /**
     * Creates canvas element
     * @static
     * @memberOf fabric.util
     * @return {CanvasElement} initialized canvas element
     */
    createCanvasElement: function() {
      return fabric.document.createElement('canvas');
    },

    /**
     * Creates a canvas element that is a copy of another and is also painted
     * @param {CanvasElement} canvas to copy size and content of
     * @static
     * @memberOf fabric.util
     * @return {CanvasElement} initialized canvas element
     */
    copyCanvasElement: function(canvas) {
      var newCanvas = fabric.util.createCanvasElement();
      newCanvas.width = canvas.width;
      newCanvas.height = canvas.height;
      newCanvas.getContext('2d').drawImage(canvas, 0, 0);
      return newCanvas;
    },

    /**
     * since 2.6.0 moved from canvas instance to utility.
     * @param {CanvasElement} canvasEl to copy size and content of
     * @param {String} format 'jpeg' or 'png', in some browsers 'webp' is ok too
     * @param {Number} quality <= 1 and > 0
     * @static
     * @memberOf fabric.util
     * @return {String} data url
     */
    toDataURL: function(canvasEl, format, quality) {
      return canvasEl.toDataURL('image/' + format, quality);
    },

    /**
     * Creates image element (works on client and node)
     * @static
     * @memberOf fabric.util
     * @return {HTMLImageElement} HTML image element
     */
    createImage: function() {
      return fabric.document.createElement('img');
    },

    /**
     * Multiply matrix A by matrix B to nest transformations
     * @static
     * @memberOf fabric.util
     * @param  {Array} a First transformMatrix
     * @param  {Array} b Second transformMatrix
     * @param  {Boolean} is2x2 flag to multiply matrices as 2x2 matrices
     * @return {Array} The product of the two transform matrices
     */
    multiplyTransformMatrices: function(a, b, is2x2) {
      // Matrix multiply a * b
      return [
        a[0] * b[0] + a[2] * b[1],
        a[1] * b[0] + a[3] * b[1],
        a[0] * b[2] + a[2] * b[3],
        a[1] * b[2] + a[3] * b[3],
        is2x2 ? 0 : a[0] * b[4] + a[2] * b[5] + a[4],
        is2x2 ? 0 : a[1] * b[4] + a[3] * b[5] + a[5]
      ];
    },

    /**
     * Decomposes standard 2x3 matrix into transform components
     * @static
     * @memberOf fabric.util
     * @param  {Array} a transformMatrix
     * @return {Object} Components of transform
     */
    qrDecompose: function(a) {
      var angle = atan2(a[1], a[0]),
          denom = pow(a[0], 2) + pow(a[1], 2),
          scaleX = sqrt(denom),
          scaleY = (a[0] * a[3] - a[2] * a[1]) / scaleX,
          skewX = atan2(a[0] * a[2] + a[1] * a [3], denom);
      return {
        angle: angle / PiBy180,
        scaleX: scaleX,
        scaleY: scaleY,
        skewX: skewX / PiBy180,
        skewY: 0,
        translateX: a[4],
        translateY: a[5]
      };
    },

    /**
     * Returns a transform matrix starting from an object of the same kind of
     * the one returned from qrDecompose, useful also if you want to calculate some
     * transformations from an object that is not enlived yet
     * @static
     * @memberOf fabric.util
     * @param  {Object} options
     * @param  {Number} [options.angle] angle in degrees
     * @return {Number[]} transform matrix
     */
    calcRotateMatrix: function(options) {
      if (!options.angle) {
        return fabric.iMatrix.concat();
      }
      var theta = fabric.util.degreesToRadians(options.angle),
          cos = fabric.util.cos(theta),
          sin = fabric.util.sin(theta);
      return [cos, sin, -sin, cos, 0, 0];
    },

    /**
     * Returns a transform matrix starting from an object of the same kind of
     * the one returned from qrDecompose, useful also if you want to calculate some
     * transformations from an object that is not enlived yet.
     * is called DimensionsTransformMatrix because those properties are the one that influence
     * the size of the resulting box of the object.
     * @static
     * @memberOf fabric.util
     * @param  {Object} options
     * @param  {Number} [options.scaleX]
     * @param  {Number} [options.scaleY]
     * @param  {Boolean} [options.flipX]
     * @param  {Boolean} [options.flipY]
     * @param  {Number} [options.skewX]
     * @param  {Number} [options.skewY]
     * @return {Number[]} transform matrix
     */
    calcDimensionsMatrix: function(options) {
      var scaleX = typeof options.scaleX === 'undefined' ? 1 : options.scaleX,
          scaleY = typeof options.scaleY === 'undefined' ? 1 : options.scaleY,
          scaleMatrix = [
            options.flipX ? -scaleX : scaleX,
            0,
            0,
            options.flipY ? -scaleY : scaleY,
            0,
            0],
          multiply = fabric.util.multiplyTransformMatrices,
          degreesToRadians = fabric.util.degreesToRadians;
      if (options.skewX) {
        scaleMatrix = multiply(
          scaleMatrix,
          [1, 0, Math.tan(degreesToRadians(options.skewX)), 1],
          true);
      }
      if (options.skewY) {
        scaleMatrix = multiply(
          scaleMatrix,
          [1, Math.tan(degreesToRadians(options.skewY)), 0, 1],
          true);
      }
      return scaleMatrix;
    },

    /**
     * Returns a transform matrix starting from an object of the same kind of
     * the one returned from qrDecompose, useful also if you want to calculate some
     * transformations from an object that is not enlived yet
     * @static
     * @memberOf fabric.util
     * @param  {Object} options
     * @param  {Number} [options.angle]
     * @param  {Number} [options.scaleX]
     * @param  {Number} [options.scaleY]
     * @param  {Boolean} [options.flipX]
     * @param  {Boolean} [options.flipY]
     * @param  {Number} [options.skewX]
     * @param  {Number} [options.skewX]
     * @param  {Number} [options.translateX]
     * @param  {Number} [options.translateY]
     * @return {Number[]} transform matrix
     */
    composeMatrix: function(options) {
      var matrix = [1, 0, 0, 1, options.translateX || 0, options.translateY || 0],
          multiply = fabric.util.multiplyTransformMatrices;
      if (options.angle) {
        matrix = multiply(matrix, fabric.util.calcRotateMatrix(options));
      }
      if (options.scaleX !== 1 || options.scaleY !== 1 ||
          options.skewX || options.skewY || options.flipX || options.flipY) {
        matrix = multiply(matrix, fabric.util.calcDimensionsMatrix(options));
      }
      return matrix;
    },

    /**
     * reset an object transform state to neutral. Top and left are not accounted for
     * @static
     * @memberOf fabric.util
     * @param  {fabric.Object} target object to transform
     */
    resetObjectTransform: function (target) {
      target.scaleX = 1;
      target.scaleY = 1;
      target.skewX = 0;
      target.skewY = 0;
      target.flipX = false;
      target.flipY = false;
      target.rotate(0);
    },

    /**
     * Extract Object transform values
     * @static
     * @memberOf fabric.util
     * @param  {fabric.Object} target object to read from
     * @return {Object} Components of transform
     */
    saveObjectTransform: function (target) {
      return {
        scaleX: target.scaleX,
        scaleY: target.scaleY,
        skewX: target.skewX,
        skewY: target.skewY,
        angle: target.angle,
        left: target.left,
        flipX: target.flipX,
        flipY: target.flipY,
        top: target.top
      };
    },

    /**
     * Returns true if context has transparent pixel
     * at specified location (taking tolerance into account)
     * @param {CanvasRenderingContext2D} ctx context
     * @param {Number} x x coordinate
     * @param {Number} y y coordinate
     * @param {Number} tolerance Tolerance
     */
    isTransparent: function(ctx, x, y, tolerance) {

      // If tolerance is > 0 adjust start coords to take into account.
      // If moves off Canvas fix to 0
      if (tolerance > 0) {
        if (x > tolerance) {
          x -= tolerance;
        }
        else {
          x = 0;
        }
        if (y > tolerance) {
          y -= tolerance;
        }
        else {
          y = 0;
        }
      }

      var _isTransparent = true, i, temp,
          imageData = ctx.getImageData(x, y, (tolerance * 2) || 1, (tolerance * 2) || 1),
          l = imageData.data.length;

      // Split image data - for tolerance > 1, pixelDataSize = 4;
      for (i = 3; i < l; i += 4) {
        temp = imageData.data[i];
        _isTransparent = temp <= 0;
        if (_isTransparent === false) {
          break; // Stop if colour found
        }
      }

      imageData = null;

      return _isTransparent;
    },

    /**
     * Parse preserveAspectRatio attribute from element
     * @param {string} attribute to be parsed
     * @return {Object} an object containing align and meetOrSlice attribute
     */
    parsePreserveAspectRatioAttribute: function(attribute) {
      var meetOrSlice = 'meet', alignX = 'Mid', alignY = 'Mid',
          aspectRatioAttrs = attribute.split(' '), align;

      if (aspectRatioAttrs && aspectRatioAttrs.length) {
        meetOrSlice = aspectRatioAttrs.pop();
        if (meetOrSlice !== 'meet' && meetOrSlice !== 'slice') {
          align = meetOrSlice;
          meetOrSlice = 'meet';
        }
        else if (aspectRatioAttrs.length) {
          align = aspectRatioAttrs.pop();
        }
      }
      //divide align in alignX and alignY
      alignX = align !== 'none' ? align.slice(1, 4) : 'none';
      alignY = align !== 'none' ? align.slice(5, 8) : 'none';
      return {
        meetOrSlice: meetOrSlice,
        alignX: alignX,
        alignY: alignY
      };
    },

    /**
     * Clear char widths cache for the given font family or all the cache if no
     * fontFamily is specified.
     * Use it if you know you are loading fonts in a lazy way and you are not waiting
     * for custom fonts to load properly when adding text objects to the canvas.
     * If a text object is added when its own font is not loaded yet, you will get wrong
     * measurement and so wrong bounding boxes.
     * After the font cache is cleared, either change the textObject text content or call
     * initDimensions() to trigger a recalculation
     * @memberOf fabric.util
     * @param {String} [fontFamily] font family to clear
     */
    clearFabricFontCache: function(fontFamily) {
      fontFamily = (fontFamily || '').toLowerCase();
      if (!fontFamily) {
        fabric.charWidthsCache = { };
      }
      else if (fabric.charWidthsCache[fontFamily]) {
        delete fabric.charWidthsCache[fontFamily];
      }
    },

    /**
     * Given current aspect ratio, determines the max width and height that can
     * respect the total allowed area for the cache.
     * @memberOf fabric.util
     * @param {Number} ar aspect ratio
     * @param {Number} maximumArea Maximum area you want to achieve
     * @return {Object.x} Limited dimensions by X
     * @return {Object.y} Limited dimensions by Y
     */
    limitDimsByArea: function(ar, maximumArea) {
      var roughWidth = Math.sqrt(maximumArea * ar),
          perfLimitSizeY = Math.floor(maximumArea / roughWidth);
      return { x: Math.floor(roughWidth), y: perfLimitSizeY };
    },

    capValue: function(min, value, max) {
      return Math.max(min, Math.min(value, max));
    },

    /**
     * Finds the scale for the object source to fit inside the object destination,
     * keeping aspect ratio intact.
     * respect the total allowed area for the cache.
     * @memberOf fabric.util
     * @param {Object | fabric.Object} source
     * @param {Number} source.height natural unscaled height of the object
     * @param {Number} source.width natural unscaled width of the object
     * @param {Object | fabric.Object} destination
     * @param {Number} destination.height natural unscaled height of the object
     * @param {Number} destination.width natural unscaled width of the object
     * @return {Number} scale factor to apply to source to fit into destination
     */
    findScaleToFit: function(source, destination) {
      return Math.min(destination.width / source.width, destination.height / source.height);
    },

    /**
     * Finds the scale for the object source to cover entirely the object destination,
     * keeping aspect ratio intact.
     * respect the total allowed area for the cache.
     * @memberOf fabric.util
     * @param {Object | fabric.Object} source
     * @param {Number} source.height natural unscaled height of the object
     * @param {Number} source.width natural unscaled width of the object
     * @param {Object | fabric.Object} destination
     * @param {Number} destination.height natural unscaled height of the object
     * @param {Number} destination.width natural unscaled width of the object
     * @return {Number} scale factor to apply to source to cover destination
     */
    findScaleToCover: function(source, destination) {
      return Math.max(destination.width / source.width, destination.height / source.height);
    },

    /**
     * given an array of 6 number returns something like `"matrix(...numbers)"`
     * @memberOf fabric.util
     * @param {Array} transform an array with 6 numbers
     * @return {String} transform matrix for svg
     * @return {Object.y} Limited dimensions by Y
     */
    matrixToSVG: function(transform) {
      return 'matrix(' + transform.map(function(value) {
        return fabric.util.toFixed(value, fabric.Object.NUM_FRACTION_DIGITS);
      }).join(' ') + ')';
    },

    /**
     * given an object and a transform, apply the inverse transform to the object,
     * this is equivalent to remove from that object that transformation, so that
     * added in a space with the removed transform, the object will be the same as before.
     * Removing from an object a transform that scale by 2 is like scaling it by 1/2.
     * Removing from an object a transfrom that rotate by 30deg is like rotating by 30deg
     * in the opposite direction.
     * This util is used to add objects inside transformed groups or nested groups.
     * @memberOf fabric.util
     * @param {fabric.Object} object the object you want to transform
     * @param {Array} transform the destination transform
     */
    removeTransformFromObject: function(object, transform) {
      var inverted = fabric.util.invertTransform(transform),
          finalTransform = fabric.util.multiplyTransformMatrices(inverted, object.calcOwnMatrix());
      fabric.util.applyTransformToObject(object, finalTransform);
    },

    /**
     * given an object and a transform, apply the transform to the object.
     * this is equivalent to change the space where the object is drawn.
     * Adding to an object a transform that scale by 2 is like scaling it by 2.
     * This is used when removing an object from an active selection for example.
     * @memberOf fabric.util
     * @param {fabric.Object} object the object you want to transform
     * @param {Array} transform the destination transform
     */
    addTransformToObject: function(object, transform) {
      fabric.util.applyTransformToObject(
        object,
        fabric.util.multiplyTransformMatrices(transform, object.calcOwnMatrix())
      );
    },

    /**
     * discard an object transform state and apply the one from the matrix.
     * @memberOf fabric.util
     * @param {fabric.Object} object the object you want to transform
     * @param {Array} transform the destination transform
     */
    applyTransformToObject: function(object, transform) {
      var options = fabric.util.qrDecompose(transform),
          center = new fabric.Point(options.translateX, options.translateY);
      object.flipX = false;
      object.flipY = false;
      object.set('scaleX', options.scaleX);
      object.set('scaleY', options.scaleY);
      object.skewX = options.skewX;
      object.skewY = options.skewY;
      object.angle = options.angle;
      object.setPositionByOrigin(center, 'center', 'center');
    },

    /**
     * given a width and height, return the size of the bounding box
     * that can contains the box with width/height with applied transform
     * described in options.
     * Use to calculate the boxes around objects for controls.
     * @memberOf fabric.util
     * @param {Number} width
     * @param {Number} height
     * @param {Object} options
     * @param {Number} options.scaleX
     * @param {Number} options.scaleY
     * @param {Number} options.skewX
     * @param {Number} options.skewY
     * @return {Object.x} width of containing
     * @return {Object.y} height of containing
     */
    sizeAfterTransform: function(width, height, options) {
      var dimX = width / 2, dimY = height / 2,
          points = [
            {
              x: -dimX,
              y: -dimY
            },
            {
              x: dimX,
              y: -dimY
            },
            {
              x: -dimX,
              y: dimY
            },
            {
              x: dimX,
              y: dimY
            }],
          transformMatrix = fabric.util.calcDimensionsMatrix(options),
          bbox = fabric.util.makeBoundingBoxFromPoints(points, transformMatrix);
      return {
        x: bbox.width,
        y: bbox.height,
      };
    },

    /**
     * Merges 2 clip paths into one visually equal clip path
     *
     * **IMPORTANT**:\
     * Does **NOT** clone the arguments, clone them proir if necessary.
     *
     * Creates a wrapper (group) that contains one clip path and is clipped by the other so content is kept where both overlap.
     * Use this method if both the clip paths may have nested clip paths of their own, so assigning one to the other's clip path property is not possible.
     *
     * In order to handle the `inverted` property we follow logic described in the following cases:\
     * **(1)** both clip paths are inverted - the clip paths pass the inverted prop to the wrapper and loose it themselves.\
     * **(2)** one is inverted and the other isn't - the wrapper shouldn't become inverted and the inverted clip path must clip the non inverted one to produce an identical visual effect.\
     * **(3)** both clip paths are not inverted - wrapper and clip paths remain unchanged.
     *
     * @memberOf fabric.util
     * @param {fabric.Object} c1
     * @param {fabric.Object} c2
     * @returns {fabric.Object} merged clip path
     */
    mergeClipPaths: function (c1, c2) {
      var a = c1, b = c2;
      if (a.inverted && !b.inverted) {
        //  case (2)
        a = c2;
        b = c1;
      }
      //  `b` becomes `a`'s clip path so we transform `b` to `a` coordinate plane
      fabric.util.applyTransformToObject(
        b,
        fabric.util.multiplyTransformMatrices(
          fabric.util.invertTransform(a.calcTransformMatrix()),
          b.calcTransformMatrix()
        )
      );
      //  assign the `inverted` prop to the wrapping group
      var inverted = a.inverted && b.inverted;
      if (inverted) {
        //  case (1)
        a.inverted = b.inverted = false;
      }
      return new fabric.Group([a], { clipPath: b, inverted: inverted });
    },

    /**
     * @memberOf fabric.util
     * @param {Object} prevStyle first style to compare
     * @param {Object} thisStyle second style to compare
     * @param {boolean} forTextSpans whether to check overline, underline, and line-through properties
     * @return {boolean} true if the style changed
     */
    hasStyleChanged: function(prevStyle, thisStyle, forTextSpans) {
      forTextSpans = forTextSpans || false;
      return (prevStyle.fill !== thisStyle.fill ||
              prevStyle.stroke !== thisStyle.stroke ||
              prevStyle.strokeWidth !== thisStyle.strokeWidth ||
              prevStyle.fontSize !== thisStyle.fontSize ||
              prevStyle.fontFamily !== thisStyle.fontFamily ||
              prevStyle.fontWeight !== thisStyle.fontWeight ||
              prevStyle.fontStyle !== thisStyle.fontStyle ||
              prevStyle.deltaY !== thisStyle.deltaY) ||
              (forTextSpans &&
                (prevStyle.overline !== thisStyle.overline ||
                prevStyle.underline !== thisStyle.underline ||
                prevStyle.linethrough !== thisStyle.linethrough));
    },

    /**
     * Returns the array form of a text object's inline styles property with styles grouped in ranges
     * rather than per character. This format is less verbose, and is better suited for storage
     * so it is used in serialization (not during runtime).
     * @memberOf fabric.util
     * @param {object} styles per character styles for a text object
     * @param {String} text the text string that the styles are applied to
     * @return {{start: number, end: number, style: object}[]}
     */
    stylesToArray: function(styles, text) {
      // clone style structure to prevent mutation
      var styles = fabric.util.object.clone(styles, true),
          textLines = text.split('\n'),
          charIndex = -1, prevStyle = {}, stylesArray = [];
      //loop through each textLine
      for (var i = 0; i < textLines.length; i++) {
        if (!styles[i]) {
          //no styles exist for this line, so add the line's length to the charIndex total
          charIndex += textLines[i].length;
          continue;
        }
        //loop through each character of the current line
        for (var c = 0; c < textLines[i].length; c++) {
          charIndex++;
          var thisStyle = styles[i][c];
          //check if style exists for this character
          if (thisStyle) {
            var styleChanged = fabric.util.hasStyleChanged(prevStyle, thisStyle, true);
            if (styleChanged) {
              stylesArray.push({
                start: charIndex,
                end: charIndex + 1,
                style: thisStyle
              });
            }
            else {
              //if style is the same as previous character, increase end index
              stylesArray[stylesArray.length - 1].end++;
            }
          }
          prevStyle = thisStyle || {};
        }
      }
      return stylesArray;
    },

    /**
     * Returns the object form of the styles property with styles that are assigned per
     * character rather than grouped by range. This format is more verbose, and is
     * only used during runtime (not for serialization/storage)
     * @memberOf fabric.util
     * @param {Array} styles the serialized form of a text object's styles
     * @param {String} text the text string that the styles are applied to
     * @return {Object}
     */
    stylesFromArray: function(styles, text) {
      if (!Array.isArray(styles)) {
        return styles;
      }
      var textLines = text.split('\n'),
          charIndex = -1, styleIndex = 0, stylesObject = {};
      //loop through each textLine
      for (var i = 0; i < textLines.length; i++) {
        //loop through each character of the current line
        for (var c = 0; c < textLines[i].length; c++) {
          charIndex++;
          //check if there's a style collection that includes the current character
          if (styles[styleIndex]
            && styles[styleIndex].start <= charIndex
            && charIndex < styles[styleIndex].end) {
            //create object for line index if it doesn't exist
            stylesObject[i] = stylesObject[i] || {};
            //assign a style at this character's index
            stylesObject[i][c] = Object.assign({}, styles[styleIndex].style);
            //if character is at the end of the current style collection, move to the next
            if (charIndex === styles[styleIndex].end - 1) {
              styleIndex++;
            }
          }
        }
      }
      return stylesObject;
    }
  };
})(typeof exports !== 'undefined' ? exports : this);
(function() {

  var slice = Array.prototype.slice;

  /**
   * Invokes method on all items in a given array
   * @memberOf fabric.util.array
   * @param {Array} array Array to iterate over
   * @param {String} method Name of a method to invoke
   * @return {Array}
   */
  function invoke(array, method) {
    var args = slice.call(arguments, 2), result = [];
    for (var i = 0, len = array.length; i < len; i++) {
      result[i] = args.length ? array[i][method].apply(array[i], args) : array[i][method].call(array[i]);
    }
    return result;
  }

  /**
   * Finds maximum value in array (not necessarily "first" one)
   * @memberOf fabric.util.array
   * @param {Array} array Array to iterate over
   * @param {String} byProperty
   * @return {*}
   */
  function max(array, byProperty) {
    return find(array, byProperty, function(value1, value2) {
      return value1 >= value2;
    });
  }

  /**
   * Finds minimum value in array (not necessarily "first" one)
   * @memberOf fabric.util.array
   * @param {Array} array Array to iterate over
   * @param {String} byProperty
   * @return {*}
   */
  function min(array, byProperty) {
    return find(array, byProperty, function(value1, value2) {
      return value1 < value2;
    });
  }

  /**
   * @private
   */
  function fill(array, value) {
    var k = array.length;
    while (k--) {
      array[k] = value;
    }
    return array;
  }

  /**
   * @private
   */
  function find(array, byProperty, condition) {
    if (!array || array.length === 0) {
      return;
    }

    var i = array.length - 1,
        result = byProperty ? array[i][byProperty] : array[i];
    if (byProperty) {
      while (i--) {
        if (condition(array[i][byProperty], result)) {
          result = array[i][byProperty];
        }
      }
    }
    else {
      while (i--) {
        if (condition(array[i], result)) {
          result = array[i];
        }
      }
    }
    return result;
  }

  /**
   * @namespace fabric.util.array
   */
  fabric.util.array = {
    fill: fill,
    invoke: invoke,
    min: min,
    max: max
  };

})();
(function() {
  /**
   * Copies all enumerable properties of one js object to another
   * this does not and cannot compete with generic utils.
   * Does not clone or extend fabric.Object subclasses.
   * This is mostly for internal use and has extra handling for fabricJS objects
   * it skips the canvas and group properties in deep cloning.
   * @memberOf fabric.util.object
   * @param {Object} destination Where to copy to
   * @param {Object} source Where to copy from
   * @param {Boolean} [deep] Whether to extend nested objects
   * @return {Object}
   */

  function extend(destination, source, deep) {
    // JScript DontEnum bug is not taken care of
    // the deep clone is for internal use, is not meant to avoid
    // javascript traps or cloning html element or self referenced objects.
    if (deep) {
      if (!fabric.isLikelyNode && source instanceof Element) {
        // avoid cloning deep images, canvases,
        destination = source;
      }
      else if (source instanceof Array) {
        destination = [];
        for (var i = 0, len = source.length; i < len; i++) {
          destination[i] = extend({ }, source[i], deep);
        }
      }
      else if (source && typeof source === 'object') {
        for (var property in source) {
          if (property === 'canvas' || property === 'group') {
            // we do not want to clone this props at all.
            // we want to keep the keys in the copy
            destination[property] = null;
          }
          else if (source.hasOwnProperty(property)) {
            destination[property] = extend({ }, source[property], deep);
          }
        }
      }
      else {
        // this sounds odd for an extend but is ok for recursive use
        destination = source;
      }
    }
    else {
      for (var property in source) {
        destination[property] = source[property];
      }
    }
    return destination;
  }

  /**
   * Creates an empty object and copies all enumerable properties of another object to it
   * This method is mostly for internal use, and not intended for duplicating shapes in canvas.
   * @memberOf fabric.util.object
   * @param {Object} object Object to clone
   * @param {Boolean} [deep] Whether to clone nested objects
   * @return {Object}
   */

  //TODO: this function return an empty object if you try to clone null
  function clone(object, deep) {
    return extend({ }, object, deep);
  }

  /** @namespace fabric.util.object */
  fabric.util.object = {
    extend: extend,
    clone: clone
  };
  fabric.util.object.extend(fabric.util, fabric.Observable);
})();
(function() {

  /**
   * Camelizes a string
   * @memberOf fabric.util.string
   * @param {String} string String to camelize
   * @return {String} Camelized version of a string
   */
  function camelize(string) {
    return string.replace(/-+(.)?/g, function(match, character) {
      return character ? character.toUpperCase() : '';
    });
  }

  /**
   * Capitalizes a string
   * @memberOf fabric.util.string
   * @param {String} string String to capitalize
   * @param {Boolean} [firstLetterOnly] If true only first letter is capitalized
   * and other letters stay untouched, if false first letter is capitalized
   * and other letters are converted to lowercase.
   * @return {String} Capitalized version of a string
   */
  function capitalize(string, firstLetterOnly) {
    return string.charAt(0).toUpperCase() +
      (firstLetterOnly ? string.slice(1) : string.slice(1).toLowerCase());
  }

  /**
   * Escapes XML in a string
   * @memberOf fabric.util.string
   * @param {String} string String to escape
   * @return {String} Escaped version of a string
   */
  function escapeXml(string) {
    return string.replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  /**
   * Divide a string in the user perceived single units
   * @memberOf fabric.util.string
   * @param {String} textstring String to escape
   * @return {Array} array containing the graphemes
   */
  function graphemeSplit(textstring) {
    var i = 0, chr, graphemes = [];
    for (i = 0, chr; i < textstring.length; i++) {
      if ((chr = getWholeChar(textstring, i)) === false) {
        continue;
      }
      graphemes.push(chr);
    }
    return graphemes;
  }

  // taken from mdn in the charAt doc page.
  function getWholeChar(str, i) {
    var code = str.charCodeAt(i);

    if (isNaN(code)) {
      return ''; // Position not found
    }
    if (code < 0xD800 || code > 0xDFFF) {
      return str.charAt(i);
    }

    // High surrogate (could change last hex to 0xDB7F to treat high private
    // surrogates as single characters)
    if (0xD800 <= code && code <= 0xDBFF) {
      if (str.length <= (i + 1)) {
        throw 'High surrogate without following low surrogate';
      }
      var next = str.charCodeAt(i + 1);
      if (0xDC00 > next || next > 0xDFFF) {
        throw 'High surrogate without following low surrogate';
      }
      return str.charAt(i) + str.charAt(i + 1);
    }
    // Low surrogate (0xDC00 <= code && code <= 0xDFFF)
    if (i === 0) {
      throw 'Low surrogate without preceding high surrogate';
    }
    var prev = str.charCodeAt(i - 1);

    // (could change last hex to 0xDB7F to treat high private
    // surrogates as single characters)
    if (0xD800 > prev || prev > 0xDBFF) {
      throw 'Low surrogate without preceding high surrogate';
    }
    // We can pass over low surrogates now as the second component
    // in a pair which we have already processed
    return false;
  }


  /**
   * String utilities
   * @namespace fabric.util.string
   */
  fabric.util.string = {
    camelize: camelize,
    capitalize: capitalize,
    escapeXml: escapeXml,
    graphemeSplit: graphemeSplit
  };
})();
(function() {

  var slice = Array.prototype.slice, emptyFunction = function() { },

      IS_DONTENUM_BUGGY = (function() {
        for (var p in { toString: 1 }) {
          if (p === 'toString') {
            return false;
          }
        }
        return true;
      })(),

      /** @ignore */
      addMethods = function(klass, source, parent) {
        for (var property in source) {

          if (property in klass.prototype &&
              typeof klass.prototype[property] === 'function' &&
              (source[property] + '').indexOf('callSuper') > -1) {

            klass.prototype[property] = (function(property) {
              return function() {

                var superclass = this.constructor.superclass;
                this.constructor.superclass = parent;
                var returnValue = source[property].apply(this, arguments);
                this.constructor.superclass = superclass;

                if (property !== 'initialize') {
                  return returnValue;
                }
              };
            })(property);
          }
          else {
            klass.prototype[property] = source[property];
          }

          if (IS_DONTENUM_BUGGY) {
            if (source.toString !== Object.prototype.toString) {
              klass.prototype.toString = source.toString;
            }
            if (source.valueOf !== Object.prototype.valueOf) {
              klass.prototype.valueOf = source.valueOf;
            }
          }
        }
      };

  function Subclass() { }

  function callSuper(methodName) {
    var parentMethod = null,
        _this = this;

    // climb prototype chain to find method not equal to callee's method
    while (_this.constructor.superclass) {
      var superClassMethod = _this.constructor.superclass.prototype[methodName];
      if (_this[methodName] !== superClassMethod) {
        parentMethod = superClassMethod;
        break;
      }
      // eslint-disable-next-line
      _this = _this.constructor.superclass.prototype;
    }

    if (!parentMethod) {
      return console.log('tried to callSuper ' + methodName + ', method not found in prototype chain', this);
    }

    return (arguments.length > 1)
      ? parentMethod.apply(this, slice.call(arguments, 1))
      : parentMethod.call(this);
  }

  /**
   * Helper for creation of "classes".
   * @memberOf fabric.util
   * @param {Function} [parent] optional "Class" to inherit from
   * @param {Object} [properties] Properties shared by all instances of this class
   *                  (be careful modifying objects defined here as this would affect all i

