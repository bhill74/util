sub getPrefix {
  my @fileNames = @_;
  my $prefix = $fileNames[0];
  
  my $fileName;
  foreach $fileName ( @fileNames ) {
    while( $fileName !~ /^$prefix/ &&
	   length( $prefix ) > 0 ) {
      chop( $prefix );        
    }    
  }
  return $prefix;
}

sub getSuffix {
  my @fileNames = @_;
  my $suffix = $fileNames[0];

  my $fileName;
  foreach $fileName ( @fileNames ) {
    while( $fileName !~ /$suffix$/ &&
	   length( $suffix ) > 0 ) {
      ( $suffix ) = ( $suffix =~ /.(.*)/ );	
    }    
  }
  return $suffix;
}

1; # return true
