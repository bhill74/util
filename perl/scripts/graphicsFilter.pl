while( <> ) {
  if ( /pixels/ ) {
    $pixels = 1;
    next;
  } elsif ( !$pixels ) {
    next;
  }
  
  if ( !/\"/ ) {
    next;
  }
  
  s/\#/ /g;
  s/^\"//;
  s/\",?$//;
  s/\S/\*/g;
  
  print $_;
}
