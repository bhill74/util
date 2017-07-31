<?php

class Arguments {
  /****************************************************
   *%FUNCTION: toBool
   *%DESCRIPTION: Used to convert a given value to a 
   * boolean.
   *%ARGUMENTS:
   * value -- The value to convert.
   *%RETURNS:
   * The boolean equivalent.
   */
  private function toBool( $value ) {
    if ( $value === false ||
	 $value === '' ||
	 $value === '0' ||
	 $value === 'off' ) {
      return false;
    }
    return true;
  }
  
  /****************************************************
   *%FUNCTION: process
   *%DESCRIPTION: Used to process all _POST and _GET
   * arguments and store them.
   * Value types are derived from the existing settings.
   *%ARGUMENTS:
   * [settings ]-- The array to store the default values and 
   * new settings.
   * [get_settings] -- The array to store the values in a format
   * applicable to GET statements. If given, it should be passed
   * by reference.
   * [extra] -- The array of fields that should be considered
   * extra. If given, it should be passed by reference.
   *%RETURNS:
   * Returns the settings that are retrieved.
   */
  public function process( $settings = array(), 
			   &$get_settings = array(), 
			   &$extra = array() ) {
    /* First, collect all the default values as GET settings */        
    foreach( array_keys( $settings ) as $key ) {
      if ( is_array( $settings[$key] ) ) {
	$get_settings[$key] = implode( ',', $settings[$key] );
      } else if ( is_bool( $settings[$key] ) ) {
	$get_settings[$key] = Arguments::toBool( $settings[$key] );
      } else {
	$get_settings[$key] = $settings[$key];
      }
    }
    
    /* Assume that arguments will either be POST or GET, not both */
    $post_keys = array_keys( $_POST );
    $get_keys = array_keys( $_GET );
    
    /* If there are ANY POST arguments, then process them */
    if ( sizeof( $post_keys ) ) {
      foreach ( $post_keys as $key ) {
	if ( !isset( $settings[$key] ) ) {
	  array_push( $extra, $key );
	}        
        
	$get_value;
	$value = $_POST[$key];
	if ( is_array( $_POST[$key] ) ) {
	  $get_value = implode( ',', $_POST[$key] );
	} else if ( is_bool( $_POST[$key] ) ) {
	  $get_value = ( $_POST[$key] == 0 ) ? 0 : 1;
	  $value = Arguments::toBool( $_POST[$key] );
	} else {
	  $get_value = $_POST[$key];
	}
	$settings[$key] = $value;
	$get_settings[$key] = $get_value;
      }
    } 
    /* Next check for GET arguments */
    else if ( sizeof( $get_keys ) ) {
      foreach ( $get_keys as $key ) {
	$value = $_GET[$key];
	if ( !isset( $settings[$key] ) ) {
	  array_push( $extra, $key );
	} else if ( is_array( $settings[$key] ) ) {
	  $value = explode( ',', $_GET[$key] );
	} else if ( is_bool( $settings[$key] ) ) {
	  $value = Arguments::toBool( $_GET[$key] );
	  }
	$settings[$key] = $value;
	$get_settings[$key] = $_GET[$key];            
      }
    }
    /* Otherwise check for command line arguments (for testing) */
    else {
      global $argv;
      foreach ( $argv as $value ) {
	$pair = explode( '=', $value );
	if ( sizeof( $pair ) != 2 ) {
	  continue;
	}
	
	$key = $pair[0];
	$value = $pair[1];
	$get_settings[$key] = $value;
	if ( !isset( $settings[$key] ) ) {
	  array_push( $extra, $key );
	} else if ( is_array( $settings[$key] ) ) {
	  $value = explode( ',', $value );
	} else if ( is_bool( $settings[$key] ) ) {
	  $value = Arguments::toBool( $value );
	}
	$settings[$key] = $value;    
      }
    }        
    
    return $settings;
  }
  
  /****************************************************
   *%FUNCTION: getURL
   *%DESCRIPTION: Used to get the URL and append arguments
   * to it.
   *%ARGUMENTS:
   * [arguments] -- The arguments to provide to the URL if needed.
   * [url] -- The URL to use, otherwise the running script
   * is used.
   *%RETURNS:
   * The combined URL.
   */
  public function getURL( $arguments = '', $url = '' ) {
    if ( $url == '' ) {
      if ( isset( $_SERVER['SCRIPT_NAME'] ) ) {
	$url = $_SERVER['SCRIPT_NAME'];
      } else {
	$url = __FILE__;
      }            
    }
    
    if ( is_array( $arguments ) && 
	 sizeof( $arguments ) > 0 ) {
      $fields = array();
      foreach( array_keys( $arguments ) as $key ) {
	$value = $arguments[$key];
	if ( is_array( $value ) ) {
	  $value = implode( ',', $value );
	} else if ( $value === false ) {
	  $value = 0;
	}
	array_push( $fields, "${key}=${value}" );
      }
      
      $url .= '?' . implode( '&', $fields );
    }
    
    return $url;
  }   
}

?>
