# Comic Downloader from SLagoon
use LWP::Simple;

my $site = "http://www.slagoon.com";
my $path = "/dailies";

sub getArchive {
  my $url = "$site/path";
  if ($opt_debug) {
    print STDERR "URL - $url\n";
  }
  return $url;
}

sub getImage {
  my $yearShift = shift;
  $yearShift = 0 if ( $yearShift < 0 );

  my $dayShift = shift;
  $dayShift = 0 if ( $dayShift < 0 );

  my ( $day, $month, $year ) = ( localtime(time - $dayShift*24*60*60) )[3,4,5];
  $month++; 
  $year += 1900;
  $year -= $yearShift;
  $year %= 100;

  $url = sprintf( "%s%s/SL%02d%02d%02d.gif", $site, $path, $year, $month, $day );
  if ($opt_debug) {
    print STDERR "IMAGE - $url\n";
  }

  return $url;
}
