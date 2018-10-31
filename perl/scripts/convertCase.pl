# Case sensitivity argument. By default use
# 'lowercase'.
$case = 'lowercase';
$case = lc $ARGV[0] if ( $ARGV[0] =~ /^(lowercase|uppercase)$/i );

while( <STDIN> ) {
  # Get the location of the file and remove any whitespace
  # from the beginning or end of the filename.
  $location = $_;  
  $location =~ s/^\s+//g;
  $location =~ s/\s+$//g;

  # If the given filename does NOT exist or is a 
  # directory then skip to the next filename.
  if ( !-e $location || -d $location ) {
     next;
  }

  # Extract the filename.
  ( $path, $filename ) = ( $location =~ m|^(.*/)?([^/]+)$| );

  # As a safety step make sure that this perl script
  # is not being modified.
  if ( $filename eq $0 ) {
     next;
  }
 
  # Convert the case.
  $newFilename = $filename;
  if ( $case eq 'uppercase' ) {
     $newFilename =~ tr/a-z/A-Z/;
  } elsif ( $case eq 'lowercase' ) {
     $newFilename =~ tr/A-Z/a-z/;
  }

  # Replace the filename location.
  $newLocation = "$path$newFilename"; 

  # Display the opertation that will be performed.
  print "$location --> $newLocation\n";

  # Add escape characters to the file locations for 
  # all whitespace characters.
  $location =~ s/(\s)/\\$1/g;
  $newLocation =~ s/(\s)/\\$1/g;

  # Perform the move if not in 'test' mode.
  system( "mv $location $newLocation" ) if ( $ARGV[1] ne 'test' );
}
