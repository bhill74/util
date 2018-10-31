# Comic Downloader from Comics.com
use LWP::Simple;

my $site = "http://www.comics.com";

sub getArchive {
  my $name = shift;
  my $dayShift = shift;
  $dayShift = 0 if ( $dayShift < 0 ); 

  my $yearShift = shift;
  $yearShift = 0 if ( $yearShift < 0 );

  my $path = "/$name";

  my ( $day, $month, $year ) = ( localtime(time - $dayShift*24*60*60) )[3,4,5];
  $month++;
  $year += 1900;    
  $year -= $yearShift;

  return sprintf( "%s%s/%04d-%02d-%02d", $site, $path, $year, $month, $day );
}

sub getImage {
  my $url = getArchive( @_ );
  if ($opt_debug) {
    print STDERR "URL - $url\n";
  }

  $_ = get( $url );
  if ( m!SRC=\"(http://assets.comics.com.*?\.full\.(gif|jpg))\"!i ||
       m!SRC=\"(http://.*?\.full\.(gif|jpg))\"!i ) {
    if ($opt_debug) {
      print STDERR "IMAGE - $1\n";
    }
    return $1;
  }
}

sub getFlash {
  return "";
}
