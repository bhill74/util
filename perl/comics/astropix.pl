# Cosmic Downloader from NASA
# Usage: perl axtropix.pl 

use LWP::Simple;

$site = "http://antwrp.gsfc.nasa.gov";
$path = "/apod";
$dateShift = $ARGV[0] + 0;

if ( $dateShift <= 0 ) {
   ( $day, $month, $year ) = ( localtime(time + $dateShift*24*60*60) )[3,4,5];
   $month++;
   $year = $year % 100;

   $url = sprintf( "%s%s/ap%02d%02d%02d.html", $site, $path, $year, $month, $day );
} else {
   $url = sprintf( "%s%s/astropix.html", $site, $path );
}

$_ = get( $url );

$date = sprintf( "%02d%02d", $year, $month );

if ( m|SRC=\"(image/($date/)?[\w_\.]+)\"|i ) {
   $url = sprintf( "%s%s/%s", $site, $path, $1 );
   print STDOUT get( $url );
}
