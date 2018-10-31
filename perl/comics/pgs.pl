# Comic Downloader from PatheticGeekStories 
use LWP::Simple;

my $site = "http://patheticgeekstories.com";

sub getArchive {
  my $path = "/randomizer.html";
  return sprintf( "%s%s", $site, $path );
}

sub getImage {
  return sprintf( "%s/archives/archiveimages/rotate.php", $site );
}

sub getFlash {
  return "";
}
