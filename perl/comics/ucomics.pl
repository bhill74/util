# Comic Downloader from UComics
use LWP::UserAgent;

my $site = "http://www.gocomics.com";

sub getArchive {
  my $name = shift;
  my $code = shift; 

  my $yearShift = shift;
  $yearShift = 0 if ( $yearShift < 0 );

  my $dayShift = shift;
  $dayShift = 0 if ( $dayShift < 0 );

  my $path = "/$name";

  my ( $day, $month, $year ) = ( localtime(time - $dayShift*24*60*60) )[3,4,5];
  $month++;
  $year += 1900;
  $year -= $yearShift;
	
  return sprintf( "%s%s/%04d/%02d/%02d/", $site, $path, $year, $month, $day );
}

sub getImage {
  my $url = getArchive( @_ );
  if ($opt_debug) {
    print STDERR "URL - $url\n";
  }

  my $name = shift;
  my $code = shift;

  my $yearShift = shift;
  $yearShift = 0 if ( $yearShift < 0 );

  my $dayShift = shift;
  $dayShift = 0 if ( $dayShift < 0 );

  my ( $day, $month, $year ) = ( localtime(time - $dayShift*24*60*60) )[3,4,5];
  $month++;
  $year += 1900;
  $year -= $yearShift;

  my $ua = LWP::UserAgent->new;
  $ua->agent( 'BrianTool/1.5' ); 
  my $request = new HTTP::Request GET => $url;
  my $result = $ua->request( $request );
  my $page = $result->content;

  $image = sprintf( "/comics/%s/%04d/%s%02d%02d%02d.(gif|jpg)",
		    $code, $year, $code, $year%100, $month, $day );

  if ( $page =~ m!SRC=\"(http://[\w\.]+\w${image})\"!i ) {
    if ($opt_debug) {
      print STDERR "IMAGE - $1\n";
    }
    return $1;
  }

  if ( $page =~ m!SRC=\"(http://imgsrv\.[^\"]+)\"!i ) {
    if ($opt_debug) {
      print STDERR "IMAGE - $1\n";
    }
    return $1;
  }
}

sub getFlash {
  my $url = getArchive( @_ );
  my $page = get( $url ); 
  if ( $page =~ m!embed src=\"(.*?)\" width=\"(\d+)\" height=\"(\d+)\"!i ) {
    return ( $1, $2, $3 );
  }
}
