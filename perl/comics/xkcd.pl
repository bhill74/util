# Comic Downloader from Comics.com
use LWP::Simple;
use Time::Local;

my $site = "http://www.xkcd.com";

sub getArchive {
  my $name = shift;
  my $dayShift = shift;
  $dayShift = 0 if ( $dayShift < 0 ); 

  my $path = $site . "/archive";
  $content = get( $path );

  my ( $day, $month, $year ) = ( localtime(time - $dayShift*24*60*60) )[3,4,5]; 
  my $timeA = timelocal( 0,0,0, $day, $month, $year );  
  my $minimum = 0;
  my $number = '';
  while ( $content =~ m!a href=\"/(\d{1,4})/\" title=\"(\d{4})-(\d{1,2})-(\d{1,2})\">! ) {
    $content = $';
    $timeB = timelocal( 0,0,0, $4, $3-1, $2-1900 );    
    $difference = abs($timeA - $timeB);
    if ( $number eq '' || $difference < $minimum ) {
       $number = $1;
       $minimum = $difference;
    } else {
       $break;
    }
  }

  return $site . "/$number/";
}

sub getImage {
  my $url = getArchive( @_ );
  if ($opt_debug) {
    print STDERR "URL - $url\n";
  }

  $_ = get( $url );
  if ( m!SRC=\"(http://imgs.xkcd.com/comics/.*?(gif|jpg|png))\"!i ) {
    if ($opt_debug) {
      print STDERR "IMAGE - $1\n";
    }
    return $1;
  }
}

sub getFlash {
  return "";
}
