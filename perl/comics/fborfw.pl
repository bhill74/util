# Comic Downloader from fborfw.com
use LWP::Simple;

my $site = "http://www.fborfw.com";
my $path = "/strip_fix";

sub getArchive {
  shift;

  $url = sprintf( "%s%s", $site, $path );
  $_ = get( $url );

  if ( $dayShift ) {
    $_ = get( $url );
    unless ( m|<A\s+HREF=\"$site$path/archives/(\d+).php\">.*?PREV|i ) {
      return;
    }
    my $id = $1+1;
    $id -= $dayShift;

    $url = sprintf( "%s%s/archives/%06d.php", $site, $path, $id );
  }

  return $url;
}

sub getImage {
  my $dayShift = shift;
  $dayShift = 0 if ( $dayShift < 0 );

  my $url = getArchive( @_ );
  if ($opt_debug) {
    print STDERR "URL - $url\n";
  }

  $_ = get( $url );

  my ( $day, $month, $year ) = ( localtime(time - $dayShift*24*60*60) )[3,4,5];
  $month++;
  $year += 1900;
  $year -= $yearShift;
  $date = sprintf( "%02d%02d%02d", $year%100, $month, $day );

  if ( m!SRC=\"(.*?$date\w+.(gif|jpg))\"!i ) {
    if ($opt_debug) {
      print STDERR "IMAGE - $site.$1\n";
    }
    return $site . $1; 
  }
}
