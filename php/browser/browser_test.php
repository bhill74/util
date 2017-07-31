<?php

include_once( "browser.php" );

$examples = 
  array( 'BlackBerry' =>     'BlackBerry8520/5.0.0.0.900 Profile/MIDP-2.1 Configuration/CLDC-1.1 VendorID/107',
	 //'iPhone' =>         'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1C25 Safari/419.3',
	 //'iPad' =>           'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405',
	 //'Safari on Mac' =>  'Mozilla/5.0 (Macintosh: Intel Mac OS X 10_6_8) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
	 //'Firefox on Mac' => 'Mozilla/5.0 (Macintosh: Intel Mac OS X 10.6;rv:6.0.2) Gecko/20100101 Firefox/6.0.2',
	 'IE on PC' =>       'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/4.0; GTB7.1; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2)',
	 //'Firefox on PC' =>  'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0.2) Gecko/20100101 Firefox/6.0.2',
	 //'Safari on PC' =>   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
	 'Chrome on PC' =>   'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1' );

foreach ( array_keys( $examples ) as $key ) {
  $info = Browser::parse( $examples[$key] );
  print "AGENT ($key) --> $examples[$key]\n";
  print_r( $info );
  print "\n";
}

?>