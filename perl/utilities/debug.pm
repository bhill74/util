#********************************************************************************
#%PACKAGE: Debug
#%DESCRIPTION: Provides functions that can be used when debugging a script.
#********************************************************************************
package Debug;

#********************************************************************************
#%FUNCTION: print_r
#%DESCRIPTION: Prints the information in the given data structure (recursively).
#%ARGUMENTS
# ref -- The reference or value to output.
#%RETURNS:
# Nothing but the text is displayed to STDOUT.
#********************************************************************************
sub print_r {
  my $ref = shift;
  print parse( $ref );
}

#********************************************************************************
#%FUNCTION: parse
#%DESCRIPTION: Recursively parses the information in the given reference and
# combines it to output to the screen.
#%ARGUMENTS
# ref -- The reference or value to output.
# indent -- The amount to indent.
#%RETURNS:
# The combined data to output to the screen.
#********************************************************************************
sub parse {
  my ( $ref, $indent ) = @_;

  my @items = ();
  my $output;

  if ( ref( $ref ) eq 'HASH' ) {
    foreach $key ( keys %{$ref} ) {
      my $count = length( $key );
      $count += 1 + 2 + 1 + 2;
      my $spacer = ' 'x${count};
      push( @items, "$key => " . parse( $ref->{$key}, $indent . $spacer ) );
    }
    $output .= '{ ' . join( ",\n$indent  ", @items ) . ' }';
  } elsif ( ref( $ref ) eq 'ARRAY' ) {
    my $length = 0;
    my $complex = 0;
    foreach $item ( @{$ref} ) {
      $length += length( $item );
      $complex = ( ref( $item ) ne '' ) ? 1 : $complex;
    }
    $complex = ( $complex || $length > 15 ) ? 1 : 0;


    my $new_indent = ( $complex ) ? "$indent  " : '';
    foreach $item ( @{$ref} ) {
      push( @items, parse( $item, $new_indent ) );
    }

    $new_indent = ( $complex ) ? ",\n$new_indent" : ', ';
    $output .= '( ' . join( $new_indent, @items ) . ' )';
  } else {
    if ( $ref != 0 || $ref eq '0' ) {
      $output .= $ref;
    } else {
      $output .= "'$ref'";
    }
  }
    return $output;
}

return 1;
