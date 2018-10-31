# Comic Downloader from Dilbert.com
use LWP::Simple;

my $site = "http://dilbert.com";

sub getArchive {
  my $dayShift = shift;
  $dayShift = 0 if ( $dayShift < 0 );

  my $yearShift = shift;
  $yearShift = 0 if ( $yearShift < 0 );

  my ( $day, $month, $year ) = ( localtime(time - $dayShift*24*60*60) )[3,4,5];
  $month++;
  $year += 1900;
  $year -= $yearShift;

  return sprintf( "%s/strips/comic/%04d-%02d-%02d", $site, $year, $month, $day );
}

sub getImage {
  my $url = getArchive( @_ );
  if ($opt_debug) {
    print STDERR "URL - $url\n";
  }

  my $category = shift;
  my $name = shift;
  my $path = "/$category/$name";
  $_ = get( $url );
  if ( m!SRC=\"(/dyn/str_strip/.*?\.strip\.(sunday\.)?(gif|jpg))\"!i ) {
    if ($opt_debug) {
      print STDERR "$site$1\n";
    }
    return $site.$1;
  }
}

sub getFlash {
  return "";
}
