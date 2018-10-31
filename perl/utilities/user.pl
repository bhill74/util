#**************************************************
#%FUNCTION: getName
#%DESCRIPTION: Gets the full name of the user
# associated with the given user ID.
#%ARGUMENTS:
# id -- The user ID to lookup.
#%RETURNS:
# The full name of the user, or the given user name
# if it could not be found.
#**************************************************
sub getName {
  my( $id ) = shift;
  my( $name ) = `ypcat passwd | grep '$id:' | cut -f5 -d':' | head -1`;
  $name = $id unless ( $name ne '' );
  chomp( $name );
  return $name;
}

sub getUserid {
  my( $name ) = shift;
  $name =~ s/^\s*//;
  $name =~ s/\s*$//;
  $name =~ s/\s+/ /g;
  my( $id ) = `ypcat passwd | grep ':${name}:' | cut -f1 -d':' | head -1`;
  chomp( $id );
  return $id;
}

#**************************************************
#%FUNCTION: getNames
#%DESCRIPTION: Gets the full names of the set of
# given user IDs (separated by spaces or commas).
#%ARGUMENTS:
# ids -- The user IDs to lookup.
#%RETURNS:
# The list of full names found for the user IDs.
#**************************************************
sub getNames {
  my %args = @_;
  my $ids = $args{userids};
  if ( scalar(@_) == 1 && $ids eq '') {
    $ids = $_[0];
  }

  my @ids = ();
  if ( ref( $ids ) ) {
    @ids = @{$ids};
  } else {
    @ids = split( /[ ,]+/, $ids );
  }

  my @names = ();
  foreach $id ( @ids ) {
    my( $name ) = getName( $id );
    if ( $args{html} == 1 ) {
      $name = sprintf( "<a href=mailto:%s\@synopsys.com>%s</a>",
		       $id, $name );
    }
    push( @names, $name );
  }
  return @names;
}

sub getUserids {
  my %args = @_;
  my $names = $args{names};
  if ( scalar(@_) == 1 && $ids eq '') {
    $names = $_[0];
  }

  $names =~ s/<[^>]+>//g;

  my @names = splitUserNames( $names );
  my @ids = ();
  foreach $name ( @names ) {
    my( $id ) = getUserid( $name );
    if ( $id eq '' ) {
      next;
    }
    push( @ids, $id );
  }
  return @ids;
}

sub joinUserNames {
  my @emails = @_;
  my $return = join( ", ", @emails );
  my $and = ", and";
  if ( scalar( @_ ) == 2 ) {
    $and = " and";
  }
  $return =~ s/(.*),/"${1}${and}"/e;
  return $return;
}

sub splitUserNames {
  my $names = shift;
  my @names = split( /\s*,\s*(and\s*)?/, $names );
  @names = grep( /\w/, @names );
  if ( scalar( @names ) == 1 ) {
    @names = split( /\s*and\s*/, $names );
    @names = grep( /\w/, @names );
  }
  return @names;
}

1;
