/**
 * jsselectmenu, JavaScript Select for Tree structures
 *
 * @version 0.1
 * @license GNU Lesser General Public License, http://www.gnu.org/copyleft/lesser.html
 * @author  Brian Hill
 * @created 2011-09-13
 * @link    http://www.glowfish.ca
 */


var jsselectmenu = {

  bindMapping : new Array(),  // Track class names with options
                              // that should be provided.
  binding : true,             // If enabled then binding will
                              // automatically occur for all
                              // matching elements.
                              // <select class="...">
  
  //*******************************************************
  //%FUNCTION: add()
  //%DESCRIPTION: Used to associate a particular class name
  // with a set of menu options to offer.
  //%ARGUMENTS:
  // className -- The class name to consider.
  // options -- The menu of options to present.
  //%RETURNS: Nothing.
  //*******************************************************
  add : function( className, options ) {
    jsselectmenu.bindMapping[className] = options;
  },

  //*******************************************************
  //%FUNCTION: install()
  //%DESCRIPTION: Used to attach the initialization event
  // to the completion of the window loading.
  //%ARGUMENTS:
  // None.
  //%RETURNS: Nothing.
  //*******************************************************
  install : function() {
    jsselectmenu.addEvent( window, 'load', jsselectmenu.init );
  },

  //*******************************************************
  //%FUNCTION: init()
  //%DESCRIPTION: Used to initialize and bind all applicable
  // select objects.
  //%ARGUMENTS:
  // None.
  //%RETURNS: Nothing.
  //*******************************************************
  init : function() {
    if (jsselectmenu.binding) {
      jsselectmenu.bind();
    }
  },

  //*******************************************************
  //%FUNCTION: bind()
  //%DESCRIPTION: Used to process all the existing select
  // objects with the proper class name and attach
  // the new jsselectmenu object.
  //%ARGUMENTS:
  // None.
  //%RETURNS: Nothing.
  //*******************************************************
  bind : function() {
    for (var className in jsselectmenu.bindMapping) {
      var matchClass = new RegExp('(^|\\s)('+className+')\\s*(\\{([^\\}]*)\\})?', 'i');
      var select = document.getElementsByTagName( 'select' );
      for(var index=0; index < select.length; index+=1 ) {      
	var match;
	if ( !select[index].menu && 
	     select[index].className &&
	     (match = select[index].className.match(matchClass)) ) {
	  jsselectmenu.attach( select[index], 
			       match[0],
			       jsselectmenu.bindMapping[className] );	

	  var value = select[index].getAttribute( '_default' );
	  if (!value && match[4]) {
	    try {
	      eval('value=\''+match[4]+'\'');
	    } catch (eInvalidProp) {}
	  }
	  if ( value && value != '' ) {
	    jsselectmenu.set( select[index], value );
	  }
	}
      }
    }
  },
  
  //*******************************************************
  //%FUNCTION: attach()
  //%DESCRIPTION: Used to attach a new jsselectmenu object
  // to a given select and configure it with the proper
  // menu options.
  //%ARGUMENTS:
  // select -- The DOM select dropdown to modify.
  // className -- The classname to associate with the 
  // options.
  // options -- The tree of options to use for this select.
  //%RETURNS: Nothing.
  //*******************************************************
  attach : function( select, className, options ) {
    select.menu = new jsselectmenu.menu( select, className, options );
  },

  //*******************************************************
  //%FUNCTION: set()
  //%DESCRIPTION: Used to set the value for a given select
  //%ARGUMENTS:
  // select -- The DOM select dropdown to modify.
  // value -- The value to select.
  //%RETURNS: Nothing.
  //*******************************************************
  set : function( select, value ) {
    if (select.menu) {
      select.menu.set( value );
    }
  },

  //*******************************************************
  //%FUNCTION: addEvent()
  //%DESCRIPTION: Used to attach a given event function to
  // an element on the specific event type.
  //%ARGUMENTS:
  // element -- The DOM element to attach to.
  // event -- The type of event.
  // func -- The function to attach to the event.
  //%RETURN: Nothing.
  //*******************************************************
  addEvent : function( element, event, func ) {
    if (element.addEventListener) {
      element.addEventListener( event, func, false );
    } else if (element.attachEvent) {
      element.attachEvent('on'+event, func );
    }
  },

  //*******************************************************
  //%FUNCTION: isArray()
  //%DESCRIPTION: Used to determine if a given object is
  // an array or not.
  //%ARGUMENTS:
  // item -- The item to test.
  //%RETURNS: TRUE if the object is an array, FALSE otherwise.
  //*******************************************************
  isArray : function( item ) {
    return ( item instanceof Array );
  },

  //*******************************************************
  //%FUNCTION: arrayKeys()
  //%DESCRIPTION: Used to collect all the keys from an
  // associative array and return them as a new array.
  //%ARGUMENTS:
  // items -- The array of items.
  //%RETURNS: The array of key values.
  //*******************************************************
  arrayKeys : function( items ) {
    var keys = new Array();
    var index = 0;
    for (var key in items ) {
      keys[index] = key;
      index += 1;
    }
    return keys;
  },

  //*******************************************************
  //%FUNCTION: merge()
  //%DESCRIPTION: Used to combine the key/values from the
  // second associative array into the first.
  //%ARGUMENTS:
  // itemsA, itemsB -- The two associative arrays to combine.
  //%RETURNS: The combined array.
  //*******************************************************
  merge : function( itemsA, itemsB ) {
    for (var key in itemsB) {
      itemsA[key] = itemsB[key];
    }
    return itemsA;
  },

  //*******************************************************
  //%OBJECT: menu
  //%DESCRIPTION: Used to adjust the update the select
  // dropdown based on the given options.
  //%ARGUMENTS:
  // target -- The select element to modify and update.
  // className -- The class name to associate with the
  // options.
  // options -- The tree of options to provide with the
  // select.
  //%RETURNS: The new menu object.
  //*******************************************************
  menu : function( target, className, options ) {
    this.select = target;
    this.allOptions = options;
    this.className = className;
    this.cache = new Array();
    this.top = 'Top';
    
    //*****************************************************
    //%FUNCTION: clear()
    //%DESCRIPTION: Used to remove all elements from the
    // known select dropdown.
    //%ARGUMENTS:
    // None.
    //%RETURNS: Nothing.
    //*****************************************************    
    this.clear = function() {
      while( this.select.options.length > 0 ) {
	this.select.remove( 0 );
      }
    }
    
    //*****************************************************
    //%FUNCTION: populate()
    //%DESCRIPTION: Used to add items to the dropdown.
    // * Items that child options are in BOLD and [] brackets.
    // * If not in the top level, the first option will be to 
    // go back 1 level.
    // * If a value is given, it will be selected.
    //%ARGUMENTS:
    // values -- The values to populate.
    // value -- The value to select.
    //%RETURNS: Nothing.
    //*****************************************************    
    this.populate = function( values, value ) { 
      var option;
      var index = 0;

      var parent = this.parent( value );      
      option = document.createElement( 'option' );
      if ( parent !== undefined && parent != '' ) {	
	option.text = '<- Back to ' + parent;
	option.value = parent;
	option.className = this.className + 'Back';
      } else {
	option.text = 'Please choose ...';
	option.value = '';
	option.className = this.className;
      }    
      this.select.add( option, null );
      index++;
     
      var isCategory = this.isCategory( value );

      var group = -1;
      var selected = false;
      for (var key in values) {
	option = document.createElement( 'option' );
	option.value = key;
	if (jsselectmenu.isArray( values[key] )) {
	  var keys = jsselectmenu.arrayKeys( values[key] );
          var size = keys.length;
	  var text = '[' + key;
          if ( size > 0 ) {
	    text += '(' + size + ')';
	  }
          text += ']';
	  option.text = text;
	  option.className = this.className + 'Group';
	} else {
	  option.text = values[key];
	  option.className = this.className + 'Value';
	}	
	this.select.add( option, null );
	       
	if ( key == value ) {
	  this.select.selectedIndex = index;
	  selected = true;
	} else if ( isCategory && value == values[key] ) {
	  group = index;
	}
	  
	index++;
      }

      if ( selected === false &&
	   group >= 0 ) {
	this.select.selectedIndex = group;
      }
    }

    //*****************************************************
    //%FUNCTION: init()
    //%DESCRIPTION: Used to check the cache for defined
    // values and if not set, to initialize it.
    //%ARGUMENTS:
    // None.
    //%RETURNS: Nothing.
    //*****************************************************  
    this.init = function() {
      if ( this.cache.length > 0 ) {
	return;
      }
      this.process( this.allOptions, this.top );
    }

    //*****************************************************
    //%FUNCTION: process()
    //%DESCRIPTION: Used to process the options and 
    // recursively populate the cache.
    //%ARGUMENTS:
    // values -- The menu values to process.
    // parent -- The parent to associate with these values.
    //%RETURNS: Nothing.
    //*****************************************************  
    this.process = function( values, parent ) {
      for (var key in values) {
	if (jsselectmenu.isArray( values[key] )) {
	  this.cache['_options/'+key] = values[key];
	  this.process( values[key], key );
	}
	this.cache['_parent/'+key] = parent;
      }
    }

    //*****************************************************
    //%FUNCTION: parent()
    //%DESCRIPTION: Used to retrieve the parent associated
    // with the given value.
    //%ARGUMENTS:
    // value -- The value to search for.
    //%RETURNS: The found parent or 'undefined'.
    //*****************************************************  
    this.parent = function( value ) {
      if ( value == '' ) {
	return '';
      }
      this.init();
      return this.cache['_parent/'+value];
    }

    //*****************************************************
    //%FUNCTION: isCategory()
    //%DESCRIPTION: Used to determine if the given value
    // is a category (for more options).
    //%ARGUMENTS:
    // value -- The value to search for.
    //%RETURNS: TRUE if the value is a category and FALSE 
    // otherwise.
    //*****************************************************  
    this.isCategory = function( value ) {
      if ( value == '' ) {
	return '';
      }
      this.init();
      return ( this.cache['_options/'+value] !== undefined );
    }
	
    //*****************************************************
    //%FUNCTION: options()
    //%DESCRIPTION: Used to retrieve the options associated
    // with the given value.
    //%ARGUMENTS:
    // value -- The value to search for.
    //%RETURNS: The found options or 'undefined'.
    //*****************************************************  
    this.options = function( value ) {
      this.init();
      return this.cache['_options/'+value];
    } 

    //*****************************************************
    //%FUNCTION: set()
    //%DESCRIPTION: Used to set the select to a given value
    // and to adjust the options to the appropriate level.
    //%ARGUMENTS:
    // value -- The value to set.
    //%RETURNS: Nothing.
    //*****************************************************
    this.set = function( value ) {
      var values = this.values;  

      if ( this.isCategory( value ) ) {
	var first = new Array();
	var values = new Array();

	var options = this.options( value );

	var found = false;
	for( var key in options ) {
	  if ( options[key] == value ) {
	    found = true;
	    first[key] = value;	    
	  } else {
	    values[key] = options[key];
	  }
	}

	if ( found === false ) {
	  first[value] = value;
	}

	values = jsselectmenu.merge( first, values );	
      } else {  
	var parent = this.parent( value );       
	if ( parent !== undefined && parent != '' ) {
	  values = this.options( parent );
	}
      }
      
      if ( values === undefined ) {
	values = this.allOptions;
      }

      this.clear();     
      this.populate( values, value );
    }
    
    //*****************************************************
    //%FUNCTION: update()
    //%DESCRIPTION: Used to update the options of the
    // select once a choice is made.
    //%ARGUMENTS:
    // None.
    //%RETURNS: Nothing.
    //*****************************************************
    this.update = function() {
      var option = this.select.options[this.select.selectedIndex];
      if ( option.value == this.top ) {
	this.set( '' );
      } else if ( this.isCategory( option.value ) ) {
	this.set( option.value );
      }
    }

    // Attach the update() function to the 'change' event
    // of the select.
    var THIS = this;
    jsselectmenu.addEvent( target, 'change', function( ) {
			     THIS.update(); } );

    this.set( '' );
  }
};

// Install this code.
jsselectmenu.install();
