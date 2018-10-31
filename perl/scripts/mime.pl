sub encode {
   local( $string, $endOfLine ) = @_;
   local( $result ) = "";

   $endOfLine = "\n" unless defined $endOfLine;
  
   pos($string) = 0;
   while( $string =~ /(.{1,45})/gs ) {
      $result .= substr(pack('u',$1),1);
      chop($result);
   }
   $result =~ tr|` -_|AA-Za-z0-9+/|;
   
   # Fix padding at the end;
   local( $padding );
   $padding = (3 - length($string) % 3 ) % 3;

   $result =~ s/.{$padding}$/'=' x $padding/e if $padding;

   # Break encoded string into lines of no more than 76 characters each
   if ( length $endOfLine ) {
      $result =~ s/(.{1,76})/$1$endOfLine/g;
   }

   return $result;
}

sub decode {
   local( $string ) = @_;
   local( $result ) = "";

   # Remove non-base64 characters
   $string =~ tr|A-Za-z0-9+=/||cd;
 
   if ( length($string) % 4 ) {
      require Carp;
      Carp::carp("Length of base64 data not a multiple of 4");
   }

   $string =~ s/=+$//;
   $string =~ tr|A-Za-z0-9+/| -_|;
   while( $string =~ /(.{1,60})/gs ) {
      local( $length ) = chr( 32 + length($1)*3/4 );
      $result .= unpack('u', $len . $1 );
   }
  
   return $result;
}
undef $/;
$encoded = &encode( <STDIN> );
$decoded = &decode( $encoded );

print "$encoded\n";
print "$decoded\n";
