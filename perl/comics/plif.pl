use LWP::Simple;

$site = "http://www.plif.com";
$path = "/archive";
$dateShift = $ARGV[0] + 0;

# Define the yearly constants.

@months = ( 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' );
$currentYear = ( localtime )[5] + 1900;
@years = ( 1994 .. $currentYear );

$time = time + $dateShift*24*60*60;
$weekday = ( localtime( $time ) )[6];
print "Week %d\n", $weekday;
if ( $weekday < 5 ) {
  $time -= ($weekday+2)*24*60*60;
} else {
  $time -= ($weekday-5)*24*60*60;
}
( $day, $month, $year ) = ( localtime( $time ) )[3,4,5];
$year += 1900;

&getDates( $year );

sub getDates {
  my $year = shift;
  $url = sprintf( "%s%s/arch%04d.html", $site, $path, $year );
  my $archive = get( $url );
  
  # Strip off excess info.
  $archive =~ s|[^\0]+?<td|<td|;
  $archive =~ s|</td>\s*</tr>\s*</table>[^\0]+||;
  $archive =~ s|</td>\s*</tr>\s*<tr>|</td>|g;
  
  # Get the cells.
  @cells = split( /\s*<\/td>\s*/i, $archive );
  
  # Process the cells.
  foreach $cell ( @cells ) {
    if ( $cell =~ />\s*([^<>]+\S)\s*$/ ) {
      $date = $1;
      if ( $cell =~ /HREF=\"([\w+_\.]+)\"/ ) {
	$image = $1;
	print "$date = IMG $image\n";
	push( @DATES, $date );
	$IMAGES{$date};
      }
    }
  }
}

sub getPreviousDate {
   my $day = shift;
   my $month = shift;
   
   my $nextMonth;
   if ( $month

   my $date;
   foreach $date ( @DATES ) {
     if ( $date

