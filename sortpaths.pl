# Used to make sure the deepest paths are
# listed first.
sub compareFunc {
  @ad = split( '/', $a );
  @bd = split( '/', $b );
  if ( $ad[0] eq $bd[0] ) {
    if ( $#ad > 1 && $#bd > 1 ) {
      if ( $ad[1] eq $bd[1] ) {
	$ac = ( $a =~ s|/|/|g );
	$bc = ( $b =~ s|/|/|g );
	return $bc cmp $ac;
      }
      return $ad[1] cmp $bd[1];
    }
  }
  return $ad[0] cmp $bd[0];
}

@paths = <>;
@paths = sort compareFunc @paths;
print join( "", @paths );

