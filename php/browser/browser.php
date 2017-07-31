<?php

class Browser {
  static private $info = array();

  /* The keywords that appear in USER_AGENT and what
   * they correspond to
   */
  static private $keywords =
    array( /* Languages */
	  'en' => array( 'language' => 'en-us' ),
	  'en-us' => array( 'language' => 'en-us' ),	  
	  /* Misc */
	  'KHTML, like Gecko' => array( 'KHTML' => true,
					'Gecko' => true ),
	  /* Security */
	  'U' => array( 'security' => 'U.S',
			'encryption' => 'high' ),
	  'I' => array( 'security' => 'International',
			'encryption' => 'weak' ),
	  /* Mozilla -- Firefox */
	  'Firefox' => array( 'browser' => 'Firefox#' ),
	  'Fennec' => array( 'browser' => 'Firefox#',
			     'mobile' => true ),
	  /* Google - Chrome/Android */
	  'Chrome' => array( 'browser' => 'Chrome#' ),
	  'Android' => array( 'browser' => 'Android#',
			      'mobile' => true ),
	  /* Microsoft - Windows/IE/CE */
	  'MSIE' => array( 'browser' => 'MSIE#' ),
	  'MSIEMobile' => array( 'browser' => 'MSIE#',
				 'mobile' => true ),
	  'IEMobile' => array( 'browser' => 'MSIE#',
			       'mobile' => true ),
	  'WindowsCE' => array( 'os' => 'WindowsCE',				
				'mobile' => true ),
	  'Windows CE' => array( 'os' => 'WindowsCE',
				 'mobile' => true ),
	  'WOW64' => array( 'browser' => 'MSIE#',
			    'browser_bits' => '32' ),
	  'SV1' => array( 'browser' => 'MSIE#',
			  'browser_version' => '6.0' ),
	  'Win64' => array( 'os_bits' => '64' ),
	  'IA64' => array( 'processor' => 'Intel',
			   'os_bits' => '64' ),
	  'x64' => array( 'processor' => 'AMD',
			  'os_bits' => '64' ),
	  'Windows NT' => array( 'os' => 'Windows7' ),
	  'WinNT' => array( 'os' => 'WindowsNT#' ),
	  'Win95' => array( 'os' => 'Windows95' ),
	  /* Apple - Safari/iPhone/iPad */
	  'Safari' => array( 'browser' => 'Safari#' ),
	  'iPhone' => array( 'browser' => 'Safari#',
			     'device' => 'iPhone',
			     'mobile' => true ),
	  'iPad' => array( 'browser' => 'Safari#',
			   'device' => 'iPad',
			   'tablet' => true ),
	  /* Opera */
	  'Opera' => array( 'browser' => 'Opera#' ),
	  'Opera Mobi' => array( 'browser' => 'Opera#',
				 'mobile' => true ),
	  'Opera Mini' => array( 'browser' => 'Opera#',
				 'mobile' => true ),
	  /* BlackBerry */
	  'BlackBerry' => array( 'browser' => 'BlackBerry#',
				 'brand' => 'RIM',
				 'mobile' => true ),
	  /* Nokia */
	  'Tear' => array( 'browser' => 'Tear#',
			   'device' => 'Nokia',
			   'mobile' => true ),
	  'Midori' => array( 'browser' => 'Midori#',
			     'device' => 'Nokia',
			     'mobile' => true ),
	  'Nokia' => array( 'brand' => 'Nokia',
			    'mobile' => true ),
	  'armv6|' => array( 'brand' => 'Nokia',
			     'mobile' => true ),
	  'armv7|' => array( 'brand' => 'Nokia',
			     'mobile' => true ),	  
	  /* Hewlett Packard */
	  'HP iPAQ' => array( 'brand' => 'Hewlett Packard',
			      'mobile' => true ),
	  /* HTC */
	  'HTC' => array( 'brand' => 'HTC',
			  'mobile' => true ),
	  /* LG */
	  'LG' => array( 'brand' => 'LG',
			 'mobile' => true ),
	  /* Motorola */
	  'MOT' => array( 'brand' => 'Motorola',
			  'mobile' => true ),
	  /* Palm */
	  'webOS' => array( 'device' => 'Palm',
			    'os' => 'webOS',
			    'mobile' => true ),  
	  'Palm' => array( 'device' => 'Palm',
			   'os' => 'webOS',
			   'mobile' => true ), 
	  /* Samsung */
	  'Samsung' => array( 'brand' => 'Samsung',
			      'mobile' => true ),
	  'SGH' => array( 'brand' => 'Samsung',
			  'mobile' => true ),  
	  /* Siemens */
	  'SIE' => array( 'brand' => 'Siemens',
			  'mobile' => true ), 
	  /* SonyEricsson */
	  'SonyEricsson' => array( 'brand' => 'SonyEricsson',
				   'mobile' => true ), 
	  /* Mobile (Generic) */
	  'MIDP' => array( 'mobile' => true ),
	  'Maemo' => array( 'os' => 'Linux',
			    'mobile' => true ),	 
	  'Smartphone' => array( 'mobile' => true ),
	  '240x320' => array( 'mobile' => true,
			      'display' => '240x320' ), 
	  '176x220' => array( 'mobile' => true,
			      'display' => '176x220' ),
	  '320x320' => array( 'mobile' => true,
			      'display' => '320x320' ),
	  '160x160' => array( 'mobile' => true,
			      'display' => '160x160' ),
	  'Sagem' => array( 'mobile' => true ), 
	  'MMP' => array( 'mobile' => true ), 
	  'UCWEB' => array( 'mobile' => true ) );
  
  function language_support( &$results ) {  
    $os = ( isset( $results['os'] ) ) ? $results['os'] : '';
    $browser = ( isset( $results['browser'] ) ) ? $results['browser'] : '';
    $version = ( isset( $results['browser_version'] ) ) ? $results['browser_version'] : 0;

    if ( $browser == 'BlackBerry' ) {
      $results['javascript'] = true;
      $results['css'] = true;
    } else if ( $browser == 'Firefox' ) {
      if ( $version >= 3.0 ) {
	$results['javascript'] = true;
      }
      if ( $version >= 4.0 ) {
	$results['css'] = true;
      }
    } else if ( preg_match( '/^Windows/', $os ) ) {
      if ( $browser == 'MSIE' ) {
	if ( $version >= 4.0 ) {
	  $results['javascript'] = true;
	  $results['css'] = true;
	}
      } else {
	$results['javascript'] = true;
	$results['css'] = true;
      }
    } 
  }
  
  function agent() {
    return ( isset( $_SERVER['HTTP_USER_AGENT'] ) ) ? $_SERVER['HTTP_USER_AGENT'] : '';
  }

  private static function process( &$results, $tag, $extra_tag = '' ) {
    foreach ( array_keys( Browser::$keywords ) as $keyword ) {
      $info = Browser::$keywords[$keyword];
      if ( !isset( $info[$tag] ) ) {
	continue;
      }

      foreach ( array_keys( $results ) as $string ) {	
	$pattern = '/^' . preg_quote( $keyword ) . '(.*)$/i';      
	if ( preg_match( $pattern, $string, $match ) ) {	
	  $extra = $match[1];
	} else {
	  continue;
	}
	
	//print "## $keyword - $tag - $string/$results[$string] - $extra ($extra_tag)\n";
	//print_r( $info );
	
	if ( !isset( $results[$tag] ) ) {	  
	  /* Check the format involved */

	  /* Get the version number and store it */
	  if ( preg_match( '/^(.*?)#$/', $info[$tag], $match ) ) {
	    $results[$tag] = $match[1];
	    if ( $results[$string] !== '' &&
		 $results[$string] !== true ) {
	      $results["${tag}_version"] = $results[$string];
	    }
	  }
	  /* If the tag is NOT boolean then use the value */	 
	  else if ( !is_bool( $info[$tag] ) ) {
	    $results[$tag] = $info[$tag];
	  }
	}
	 
	foreach ( array_keys( $info ) as $key ) {
	  if ( !isset( $results[$key] ) ) {
	    $results[$key] = $info[$key];
	  }
	}
      
	unset( $results[$keyword] );     
	if ( $extra_tag != '' &&
	     $extra != '' &&
	     !isset( $results[$extra_tag] ) ) {
	  $results[$extra_tag] = $extra;
	  unset( $results[$string] );
	}
      }
    }
  }

  private static function add( &$results, $key, $value ) {   
    if ( isset( $results[$key] ) ) {
      if ( !is_array( $results[$key] ) ) {
	$results[$key] = array( $results[$key] );
      }
      array_push( $results[$key], $value );
    } else {
      $results[$key] = $value;
    }
  }

  function parse( $agent = '' ) {
    $agent = ( $agent != '' ) ? $agent : Browser::agent();
    $results = array();
    while ( true ) {
      if ( preg_match( '|^([^\s\(]+)\s*(.*)$|', $agent, $match ) ) {
	$values = explode( '/', $match[1] );
	$agent = $match[2];
	$platform = $values[0];
	$version = $values[1];
	Browser::add( $results, $platform, $version );
      } else if ( preg_match( '|^\(([^\)]+)\)\s*(.*)$|', $agent, $match ) ) {       
	$agent = $match[2];	 
	foreach ( preg_split( '/;\s+/', $match[1] ) as $value ) {
	  if ( preg_match( '/CPU\s+OS\s+(\S+)\s+like\s+Mac\s+OS\s+X/i', $value, $match ) ) {
	    Browser::add( $results, 'mac', true );
	    Browser::add( $results, 'os', 'OSX' );
	    Browser::add( $results, 'os_version', preg_replace( '/_/', '.', $match[1] ) );
	  } else if ( preg_match( '/^macintosh:\s+(\w+)\s+mac\s+os\s+x\s+(\S+)/i', $value, $match ) ) {
	    Browser::add( $results, 'mac', true );
	    Browser::add( $results, 'os', 'OSX' );
	    Browser::add( $results, 'os_version', preg_replace( '/_/', '.', $match[2] ) );
	    Browser::add( $results, 'processor', $match[1] );
	  } else if ( preg_match( '|(.*?\S)\s*\W?\s*(\d+\.[\d\.]+)$|', $value, $match ) ) {	    
	    Browser::add( $results, $match[1], $match[2] );
	  } else {	      
	    $results[$value] = true;
	  }
	}
      } else {
	break;
      }
    }

    if ( isset( $results['.net clr'] ) ) {
      $results['netclr'] = $results['.net clr'];
      unset( $results['.net clr'] );
    }
    
    Browser::process( $results, 'browser' );
    Browser::process( $results, 'language' );
    Browser::process( $results, 'mobile', 'model' );
    Browser::process( $results, 'os' );
    Browser::process( $results, 'KHTML' );
    Browser::process( $results, 'security' );
    
    if ( !isset( $results['language'] ) ) {
      $results['language'] = 'en-us';
    }

    Browser::language_support( $results );

    return $results;
  }

  function init() {
    if ( sizeof( Browser::$info ) == 0 ) {
      Browser::$info = Browser::parse( Browser::agent() );
    }
  }
  
  function get( $string ) {
    Browser::init();
    return ( isset( Browser::$info[$string] ) ) ? Browser::$info[$string] : '';
  } 
  
  function isWindows() {
    return ( preg_match( '/^Windows/', Browser::get( 'os' ) ) );
  } 
}

?>