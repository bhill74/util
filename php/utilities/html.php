<?php

/****************************************************
 * Includes:
 */
set_include_path( get_include_path() . PATH_SEPARATOR . "$_ENV[HOME]/public_html/charts" );

include_once( "arguments.php" );
include_once( "file.php" );

/* ##################################################
 * Class HTML
 *
 * Used to construct valid HTML tags.
 *
 */
class HTML {  
  /* Array to store all previously loaded files */
  private static $loaded_files = array();
  
  /**************************************************
   *%FUNCTION: append
   *%DESCRIPTION:
   * Used to manipulate a settings array and append
   * a new value to an already existing property
   *%ARGUMENTS:
   * settings -- The array of settings [by reference]
   * name -- The name of the setting.
   * value -- The value to append.
   *%RETURNS:
   * Nothing, but the settings array is modified.
   */
  public static function append( &$settings, $name, $value ) {
    if ( isset( $settings[$name] ) ) {
      if ( is_array( $settings[$name] ) ) {
	array_push( $settings[$name], $value );
      } else {
	$settings[$name] .= ';' . $value;
      }
    } else {
      $settings[$name] = $value;
     }
  }
  
  /**************************************************
   *%FUNCTION: append
   *%DESCRIPTION:
   * Used to manipulate a settings array and prepend
   * a new value to an already existing property
   *%ARGUMENTS:
   * settings -- The array of settings [by reference]
   * name -- The name of the setting.
   * value -- The value to prepend.
   *%RETURNS:
   * Nothing, but the settings array is modified.
   */
  public static function prepend( &$settings, $name, $value ) {
    if ( isset( $settings[$name] ) ) {
      if ( is_array( $settings[$name] ) ) {
	array_unshift( $settings[$name], $value );
      } else {
	$settings[$name] = $value . ';' . $settings[$name];
      }
    } else {
      $settings[$name] = $value;
    }
  }

  /**************************************************
   *%FUNCTION: get_value
   *%DESCRIPTION:
   * Used to extract a value from a given array or
   * if it is not an array simply return the given value.
   *%ARGUMENTS:
   * value -- The value (or array of values) to return.
   * [name] -- The name index for the value (if an array).
   *%RETURNS:
   * The extracted value.
   */
  private function get_value( $value, $name = '' ) {
    if ( is_array( $value ) ) {
      return ( isset( $value[$name] ) ) ? $value[$name] : '';
    }
    return $value;
  }

  /**************************************************
   *%FUNCTION: tag
   *%DESCRIPTION:
   * Used to create a single HTML tag with any additional
   * properties provided.
   *%ARGUMENTS:
   * tag -- The name of the tag.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */
  public static function tag( $tag, $settings = array() ) {
    return "<${tag} " . 
      HTML::settings( $settings,
		      HTML::get_value( $settings, 'name' ) ) . 
      " />";
  }
  
  /**************************************************
   *%FUNCTION: tag
   *%DESCRIPTION:
   * Used to create a HTML tag that begins and ends around
   * some included text/code.
   *%ARGUMENTS:
   * tag -- The name of the tag.
   * code -- The content to place between the BEING and END.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */
  public static function wrap( $tag, $code, $settings = array() ) {   
    $delim = ( ( $code != '' && preg_match( '/\n/', $code ) ) ||
	       strlen( $code ) > 100 ) ? "\n" : '';
    
    return "<${tag} " . 
      HTML::settings( $settings,
		     HTML::get_value( $settings, 'name' ) ) . 
      ">${delim}${code}${delim}</${tag}>\n";
  } 

  /**************************************************
   *%FUNCTION: setting
   *%DESCRIPTION:
   * Used to convert a setting to HTML code for the tag.
   *%ARGUMENTS:
   * property -- The property name.
   * value -- The value (or array of values) to insert.
   * [name] -- The name index for the value (if an array).
   *%RETURNS:
   * The generated code.
   */
  private static function setting( $property, $value, $name = '' ) {
    $value = HTML::get_value( $value, $name );
    if ( $value === true ) {
      return $property;
    }
    return "${property}=\"${value}\"";
  }
  
  /**************************************************
   *%FUNCTION: settings
   *%DESCRIPTION:
   * Used to converts an array of settings to HTML 
   * code for the tag.
   *%ARGUMENTS:
   * settings -- The array of setting values.
   * name -- The name of the HTML element to use in looking
   * up values.
   *%RETURNS:
   * The generated code.
   */
  private function settings( $settings, $name = '' ) {   
    $code = array();
    foreach ( array_keys( $settings ) as $key ) {      
      $value = ( is_array( $settings[$key] ) && $key == 'style' ) ? 
	implode( ';', $settings[$key] ) : $settings[$key];     
      array_push( $code, HTML::setting( $key, $value, $name ) );
    }
    return implode( ' ', $code );
  }

  /**************************************************
   *%FUNCTION: is_assoc_array
   *%DESCRIPTION:
   * Used to determine if the given value is an
   * associative array (hash) or regular one.
   *%ARGUMENTS:
   * array -- The array to test.
   *%RETURNS:
   * TRUE if the array is associative, FALSE otherwise.
   */
  private static function is_assoc_array( $array ) {    
    return array_keys( $array ) !== range(0, count($array) - 1);
  }

  /**************************************************
   * Javascript (JSS)
   */

  /**************************************************
   *%FUNCTION: js_load
   *%DESCRIPTION:
   * Used to create a SCRIPT tag that will source a 
   * Javascript (JS) file from the given path.
   * Note: If this file as previous used it, this
   * function will output an empty string rather than
   * duplicate code.
   *%ARGUMENTS:
   * file -- The Javascript (JS) file to load.
   *%RETURNS:
   * The generated HTML.
   */
  public static function js_load( $file ) {
    if (array_search( $file, HTML::$loaded_files, true ) !== false) {
      return;
    }

    array_push( HTML::$loaded_files, $file );
    $directory = File::getRelativePath( $file, '', 'up' );
    return HTML::wrap( 'script', '', 
		       array( 'type' => 'text/javascript',
			      'src' => "${directory}${file}" ) );
  }

  /**************************************************
   *%FUNCTION: js_jquery
   *%DESCRIPTION:
   * Used to include the Javascript Query plugin.
   *%ARGUMENTS:
   * None
   *%RETURNS:
   * The generated HTML.
   */
  public static function js_jquery() {
    $version = '1.6.4';
    return HTML::js_load( "js/jquery/jquery-${version}.js" );
  }
  
  /**************************************************
   *%FUNCTION: js_jquery_ui
   *%DESCRIPTION:
   * Used to include the Javascript Query UI plugin.
   *%ARGUMENTS:
   * None
   *%RETURNS:
   * The generated HTML.
   */
  public static function js_jquery_ui( $theme = 'lightness' ) {
    $html =  HTML::js_jquery();
    $version = '1.8.16.custom';
    $html .= HTML::js_load( "js/jquery-ui/js/jquery-ui-${version}.min.js" );
    $html .= HTML::css_load( "js/jquery-ui/css/ui-${theme}/jquery-ui-${version}.css" );
    return $html;
  }

  /**************************************************
   *%FUNCTION: js_code
   *%DESCRIPTION:
   * Used to create a SCRIPT tag that will wrap around
   * Javascript (JS) code that should be executed by
   * the browser.
   *%ARGUMENTS:
   * code -- The code to be included in the tag.
   *%RETURNS:
   * The generated HTML.
   */
  public static function js_code( $code ) {
    return HTML::wrap( 'script', $code, array( 'language' => 'javascript' ) );
  }

  /**************************************************
   * Cascading Style Sheets (CSS)
   */

  /**************************************************
   *%FUNCTION: css_load
   *%DESCRIPTION:
   * Used to create a SCRIPT tag that will source a 
   * Cascading Style Sheet (CSS) file from the given path.
   * Note: If this file as previous used it, this
   * function will output an empty string rather than
   * duplicate code.
   *%ARGUMENTS:
   * file -- The Cascading Style Sheet (CSS) file to load.
   *%RETURNS:
   * The generated HTML.
   */
  public static function css_load( $file ) {
    if (array_search( $file, HTML::$loaded_files, true ) !== false) {
      return;
    }

    array_push( HTML::$loaded_files, $file );
    $directory = File::getRelativePath( $file, '', 'up' );
    return HTML::tag( 'link', 
		      array( 'rel' => 'stylesheet',
			     'type' => 'text/css',
			     'href' => "${directory}${file}" ) );
  }    

  /**************************************************
   *%FUNCTION: span
   *%DESCRIPTION:
   * Used to create a SPAN element.
   *%ARGUMENTS:
   * code -- The code to include in the span.
   * [settings] -- Any extra settings to be provided.
   *%RETURNS:
   * The generated HTML.
   */
  function span( $code, $settings = array() ) {
    return HTML::wrap( 'span', $code, $settings );
  }

  /**************************************************
   *%FUNCTION: div
   *%DESCRIPTION:
   * Used to create a DIV element.
   *%ARGUMENTS:
   * code -- The code to include in the div.
   * [settings] -- Any extra settings to be provided.
   *%RETURNS:
   * The generated HTML.
   */
  function div( $code, $settings = array() ) {
    return HTML::wrap( 'div', $code, $settings );
  }
  
  /**************************************************
   *%FUNCTION: font
   *%DESCRIPTION:
   * Used to create a FONT element.
   *%ARGUMENTS:
   * code -- The code to include in the font.
   * [settings] -- Any extra settings to be provided.
   *%RETURNS:
   * The generated HTML.
   */
  function font( $code, $settings = array() ) {
    return HTML::wrap( 'font', $code, $settings );
  }

  /**************************************************
   *%FUNCTION: br
   *%DESCRIPTION:
   * Used to create a BR element.
   *%ARGUMENTS:
   * [number] -- The number of consecutive BR elements.
   * [settings] -- Any extra settings to be provided.
   *%RETURNS:
   * The generated HTML.
   */
  function br( $number = 1, $settings = array() ) {
    $tag = HTML::tag( 'br', $settings );
    $html = '';
    for( $index = 0; $index < $number; $index++ ) {
      $html .= $tag;
    }
    return $html . "\n";
  }

  /**************************************************
   *%FUNCTION: href
   *%DESCRIPTION:
   * Used to create an A HREF element.
   *%ARGUMENTS:
   * code -- THe code to wrap around.
   * link -- The link to include.
   * [settings] -- Any extra settings to be provided.
   *%RETURNS:
   * The generated HTML.
   */
  function href( $code, $link, $settings = array() ) {
    $settings['href'] = $link;
    return HTML::wrap( 'a', $code, $settings );
  }

  /**************************************************
   *%FUNCTION: ul
   *%DESCRIPTION:
   * Used to create a UL element (Unordered List).
   *%ARGUMENTS:
   * code -- The code to include in the ul.
   * [settings] -- Any extra settings to be provided.
   *%RETURNS:
   * The generated HTML.
   */
  function ul( $code, $settings = array() ) {
    return HTML::wrap( 'ul', $code, $settings );
  }

  /**************************************************
   * Images
   */

  /**************************************************
   *%FUNCTION: img (alias 'image')
   *%DESCRIPTION:
   * Used to create an 'IMG' HTML tag.
   *%ARGUMENTS:
   * image -- The URL/location of the image file to
   * include.
   * [settings] -- Any extra settings to be provided.
   *%RETURNS:
   * The generated HTML.
   */
  function img( $image, $settings = array() ) {
    $settings['src'] = $image;
    return HTML::tag( 'img', $settings );
  }

  /* Alias: of HTML::img() */
  function image( $image, $settings = array() ) {
    return HTML::img( $image, $settings );
  }

  /**************************************************
   * Form & Form Elements
   */
  
  /**************************************************
   *%FUNCTION: form
   *%DESCRIPTION:
   * Used to wrap given HTML code into a HTML FORM
   * tag.
   *%ARGUMENTS:
   * code -- The code to insert.
   * [name] -- The name of the form.
   * [action = false] -- The link to use when executing this
   * form. If not provided the same as the current page is used.
   * [method = 'post'] -- The method to use in transferring the
   * data. Either 'post' or 'get'.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */
  function form( $code, $name = '', $action = false, $method = 'post',
		 $settings = array() ) {
    $settings['method'] = $method;
    if ( $action === false ) {
      $settings['action'] = Arguments::getUrl();
    } else {
      $settings['action'] = $action;
    }
    $settings['name'] = $name;
    return HTML::wrap( 'form', $code, $settings );
  }

  /**************************************************
   *%FUNCTION: input
   *%DESCRIPTION:
   * Used to create a FORM INPUT element.
   *%ARGUMENTS:
   * name -- The name of the input.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */
  function input( $name, $settings = array() ) {
    $settings['name'] = $name;
    return HTML::tag( 'input', $settings );
  }

  /*************************************************
   *%FUNCTION: entry
   *%DESCRIPTION:
   * Used to create a FORM ENTRY input element.
   *%ARGUMENTS:
   * name -- The name of the input.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  function entry( $name, $settings = array() ) {    
    unset( $settings['name'] );
    $settings['type'] = 'text';
    return HTML::input( $name, $settings );
  }
  
  /*************************************************
   *%FUNCTION: hidden
   *%DESCRIPTION:
   * Used to create a FORM HIDDEN input element.
   *%ARGUMENTS:
   * name -- The name of the input.
   * value -- The value to insert in the input.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  function hidden( $name, $value, $settings = array() ) {    
    unset( $settings['name'] );
    $settings['type'] = 'hidden';
    $settings['value'] = $value;
    return HTML::input( $name, $settings );
  }

  /*************************************************
   *%FUNCTION: button
   *%DESCRIPTION:
   * Used to create a FORM BUTTON input element.
   *%ARGUMENTS:
   * name -- The name of the input.
   * value -- The value to insert in the input.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  function button( $name, $value, $settings = array() ) {    
    unset( $settings['name'] );
    $settings['type'] = 'button';
    $settings['value'] = $value;
    return HTML::input( $name, $settings );
  }

  /*************************************************
   *%FUNCTION: checkbox
   *%DESCRIPTION:
   * Used to create a FORM CHECKBOX input element.
   *%ARGUMENTS:
   * name -- The name of the input.
   * value -- The value to insert in the input.
   * checked -- Whether the button should be checked.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  function checkbox( $name, $value, $checked, $settings = array() ) {    
    unset( $settings['name'] );
    $settings['type'] = 'checkbox';
    $settings['value'] = $value;
    unset( $settings['checked'] );
    if ( $checked === true ) {
      $settings['checked'] = $checked;
    }
    return HTML::input( $name, $settings );
  }

  /*************************************************
   *%FUNCTION: radio
   *%DESCRIPTION:
   * Used to create a FORM RADIO input element.
   *%ARGUMENTS:
   * name -- The name of the input.
   * value -- The value to insert in the input.
   * checked -- Whether the button should be checked.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  function radio( $name, $value, $checked, $settings = array() ) {    
    unset( $settings['name'] );
    $settings['type'] = 'radio';
    $settings['value'] = $value;
    if ( $checked === true ) {
      $settings['checked'] = $checked;
    }
    return HTML::input( $name, $settings );
  }

  /*************************************************
   *%FUNCTION: radio_grp
   *%DESCRIPTION:
   * Used to create a group of FORM RADIO input 
   * elements.
   *%ARGUMENTS:
   * name -- The name of the input.
   * info -- The information to add (options).
   * value -- The value to insert in the input.
   * order -- The order of the options from the info list.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  function radio_grp( $name, $info, 
		      $value = '',
		      $order = false, 
		      $settings = array() ) {    
    if ( !HTML::is_assoc_array( $info ) ) {
      $order = $info;
      $info = array();
      foreach( $order as $key ) {
	$info[$key] = $key;
      }
      return HTML::radio_grp( $name, $info, $value,
			      $order,
			      $settings );
    }

    if ( $order === false ) {
      $order = array_keys( $info );
    }

    $html = '';   

    if ( sizeof( $info ) == 1 ) {
      $key = end( $order );
      $html .= HTML::hidden( $name, $key );
      $html .= $info[$key];
      return $html;
    }

    $option_settings = ( isset( $settings['option'] ) ) ? $settings['option'] : array();
    unset( $settings['option'] ); 

    unset( $settings['name'] );

    $columns_order = HTML::process_order( $order );

    $columns = array();
    foreach ( $columns_order as $order ) {
      $options = array();
      foreach ( $order as $key ) {
	$single_settings = $option_settings;
	$single_settings['value'] = $key;  
	$checked = ( HTML::get_value( $value, $name ) == $key );
	array_push( $options,
		    HTML::radio( $name, $key, $checked,
				 $single_settings ) . $info[$key] );
      }
      
      array_push( $columns, implode( HTML::br(), $options ) );
    }

    if ( sizeof( $columns ) <= 1 ) {
      return implode( '', $columns );
    }
    
    $html = "<table>";
    $html .= "<tr><td valign=top>";
    $html .= implode( "</td><td valign=top>", $columns );
    $html .= "</td></tr>\n";
    $html .= "</table>\n";
    
    return $html;
  }

  /*************************************************
   *%FUNCTION: process_order
   *%DESCRIPTION:
   * Used to process the order string into different
   * columns (if necessary).
   *%ARGUMENTS:
   * order -- The order strings. If grouped into arrays the
   * different columns are desired.
   *%RETURNS:
   * The processed column order.
   */ 
  private function process_order( $order ) {
    $columns_order = array();
    $was_array = true;
    $last = -1;
    foreach ( $order as $key ) {
      if ( is_array( $key ) ) {
	array_push( $columns_order, $key );
      } else {
	if ( $was_array === true ) {	  
	  array_push( $columns_order, array() );
	  $was_array = false;
	  $last += 1;
	}
	array_push( $columns_order[$last], $key );
      }
    }
    return $columns_order;
  }

  /*************************************************
   *%FUNCTION: select
   *%DESCRIPTION:
   * Used to create a FORM SELECT element.
   *%ARGUMENTS:
   * name -- The name of the select.
   * info -- The array of values to use for options.
   * [value] -- The selected value
   * [order] -- The order of the options.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  public static function select( $name, $info, 
				 $value = '', 
				 $order = false, 
				 $settings = array() ) {
    if ( !HTML::is_assoc_array( $info ) ) {
      $order = $info;
      $info = array();
      foreach( $order as $key ) {
	$info[$key] = $key;
      }
      return HTML::select( $name, $info, $value, 
			   $order, 
			   $settings );
    }
    
    if ( $order === false ) {
      $order = array_keys( $info );
    }

    $html = '';   

    if ( ( isset( $settings['multiple'] ) && 
	   $settings['multiple'] === true ) &&
	 ( isset( $settings['checkbox'] ) && 
	   $settings['checkbox'] === true ) ) {
      if ( !is_array( $value ) ) {
	$value = array( $value );
      }

      $columns_order = HTML::process_order( $order );      

      $columns = array();
      foreach ( $columns_order as $order ) {
	$options = array();
	foreach( $order as $key ) {
	  $checked = ( array_search( $key, $value, true ) !== false );
	  array_push( $options,
		      HTML::checkbox( "${name}[]", $key, $checked ) . $info[$key] );
	}
	array_push( $columns, implode( HTML::br(), $options ) );
      }

      if ( sizeof( $columns ) <= 1 ) {
	return $html . implode( '', $columns );
      }
      
      $html .= "<table>";
      $html .= "<tr><td valign=top>";
      $html .= implode( "</td><td valign=top>", $columns );
      $html .= "</td></tr>\n";
      $html .= "</table>\n";
      
      return $html;    
    }   
    unset( $settings['checkbox'] );

    if ( sizeof( $info ) == 1 ) {
      $key = end( $order );
      $html .= HTML::hidden( $name, $key );
      $html .= $info[$key];
      return $html;
    }               
    
    $option_settings = ( isset( $settings['option'] ) ) ? $settings['option'] : array();
    unset( $settings['option'] );       
    
    $settings['name'] = $name;    

    $html_options = array();
    foreach( $order as $key ) {      
      $single_settings = $option_settings;
      $single_settings['value'] = $key;      
      if ( HTML::get_value( $value, $name ) == $key ) {
	$single_settings['selected'] = true;
      }
      array_push( $html_options,
		  HTML::wrap( 'option', $info[$key], $single_settings ) );
    }
    
    $html .= HTML::wrap( 'select', implode( '', $html_options ), $settings );
    
    return $html;
  }  

  /*************************************************
   *%FUNCTION: submit
   *%DESCRIPTION:
   * Used to create a FORM SUBMIT input element.
   *%ARGUMENTS:
   * value -- The value to associate with the input.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  function submit( $value, $settings = array() ) {    
    unset( $settings['name'] );
    $settings['type'] = 'submit';
    $settings['value'] = $value;
    return HTML::input( '', $settings );
  }
  
  /*************************************************
   *%FUNCTION: submit_image
   *%DESCRIPTION:
   * Used to create a FORM SUBMIT input element using
   * an image.
   *%ARGUMENTS:
   * image -- The location of the image.
   * [settings] -- The settings to be included in the HTML element.
   *%RETURNS:
   * The generated HTML.
   */ 
  function submit_image( $image, $settings = array() ) {
    $name = ( isset( $settings['name'] ) ) ? $settings['name'] : '';
    unset( $settings['name'] );
    $settings['type'] = 'image';
    $settings['src'] = $image;
    return HTML::input( $name, $settings );
  }
}

?>
