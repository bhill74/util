package MySQL;

use Spreadsheet::WriteExcel;
use Date::Calc;

sub date_now() {
  return sprintf( "%04d-%02d-%02d", Date::Calc::Today_and_Now() );
}

sub date_time_now() {
  return sprintf( "%04d-%02d-%2d %02d:%02d:%02d", Date::Calc::Today_and_Now() );
}

sub create_spacer {
  my( $length ) = shift;
  return ' 'x${length};
}

#********************************************************************************
#%FUNCTION: insert_query
#%DESCRIPTION: Used to create an insert query in MySQL. If provided the unique
# fields will be compared and duplicates will be avoided (updated instead).
#%ARGUMENTS
# table -- The name of the table to adjust.
# data_ref -- The reference to the array of data to add.
# [unique_ref] -- The reference to the list of unique fields, the first should be
# tagged as 'unique' in the database.
#%RETURNS:
# The formed query.
#********************************************************************************
sub insert_query {
  my %args = @_;

  # Process the arguments.
  my ( $table, $data_ref, $unique_ref, $indent );
  if ( defined $args{table} ) {
    $table = $args{table};
  } else {
    warn "select_query(): The table name must be provided";
    return;
  }

  if ( defined $args{data_ref} ) {
    $data_ref = $args{data_ref};
  } else {
    warn "select_query(): The data to insert must be provided";
    return;
  }

  my @fields = sort keys %{$data_ref};
  my @values = @{$data_ref}{@fields};

  my $unique_query;
  my $unique_id;
  my @non_unique_fields = @fields;
  if ( defined $args{unique_ref} ) {
    my @unique_fields;
    my %non_unique;
    @non_unique{@fields} = ();

    $unique_ref = $args{unique_ref};
    ( $unique_id, @unique_fields ) = @{$unique_ref};

    my %sub_data;
    @sub_data{@unique_fields} = @{$data_ref}{@unique_fields};
    my @output = ( $unique_id );
    #$unique_query = select_query( table => $table,
#				  data_ref => \%sub_data,
#				  output_ref => \@output );

    grep( $non_unique{$_}++, @unique_fields );
    @non_unique_fields = grep( $non_unique{$_} eq '', sort keys %non_unique );
  }

  my $indent;
  if ( defined $args{indent} ) {
    $indent = "\n";
    if ( $args{indent} != 1 ) {
      $indent = "\n" . $args{indent};
    }
  }

  my $field;

  # Insert fields
  my $query = "INSERT INTO ${table} ( ";
  my $spacer = create_spacer( length($query) );

  my $delim = ( defined $indent ) ? "`,${indent}${spacer}`" : "`, `";
  #push( @fields, $unique_id ) if ( defined $unique_id );
  $query .= "`" . join( $delim, @fields ) . "`";
  $query .= " ) ";
  $query .= $indent if ( defined $indent );

  # Insert values
  my $cmd = " VALUES( ";
  $spacer = create_spacer( length($cmd) );
  $delim = ( defined $indent ) ? "',${indent}${spacer}'" : "', '";
  $query .= $cmd . "'" . join( $delim, @values ) . "'";
  #if ( defined $unique_id ) {
  #  $query .= "${indent}${spacer}" if ( defined $indent );
  #  $query .= "( ${unique_query} )";
  #}
  $query .= " ) ";
  $query .= $indent if ( defined $indent );

  # On duplicate modify.
  if ( defined $unique_id ) {
    $cmd = " ON DUPLICATE KEY UPDATE ";
    $spacer = create_spacer( length($cmd) );
    $query .= $cmd;
    foreach $field ( @non_unique_fields ) {
      $query .= "`${field}` = VALUES( ${field} )"; #'" . $data_ref->{$field} . "'";
      if ( $field ne $non_unique_fields[$#non_unique_fields] ) {
	$query .= ",";
	$query .= "${indent}${spacer}" if ( defined $indent );
      }
    }
  }

  return $query;
}

#********************************************************************************
#%FUNCTION: select_query
#%DESCRIPTION: Used to create an select query in MySQL.
#%ARGUMENTS
# table -- The name of the table to adjust.
# data_ref -- The reference to the array of data to query. Any set fields will
# qualify as the search criteria.
# [output_ref] -- The reference to the list of fields to retrieve.
#%RETURNS:
# The formed query.
#********************************************************************************
sub select_query {
  my %args = @_;

  # Process the arguments.
  my ( $table, $data_ref, $output_ref, $indent );
  if ( defined $args{table} ) {
    $table = $args{table};
  } else {
    warn "select_query(): The table name must be provided";
    return;
  }

  if ( defined $args{data_ref} ) {
    $data_ref = $args{data_ref};
  } else {
    warn "select_query(): The data to select on must be provided";
    return;
  }

  my @fields = sort keys %{$data_ref};

  my @output;
  if ( defined $args{output_ref} ) {
    $output_ref = $args{output_ref};
    @output = @{$output_ref};
  } elsif ( defined $data_ref ) {
    @output = @fields;
  }

  my $indent;
  if ( defined $args{indent} ) {
    $indent = "\n";
    if ( $args{indent} != 1 ) {
      $indent = "\n" . $args{indent};
    }
  }

  my $query = "SELECT ";
  my $spacer = create_spacer( length($query) );
  my $delim;
  if ( defined @output && scalar(@output) > 0 ) {
    $delim = ( defined $indent ) ? "`,${indent}${spacer}`" : "`, `";
    $query .= "`" . join( $delim, @output ) . "`";
  } else {
    $query .= '*';
  }
  $query .= " FROM ${table}";
  $query .= $indent if ( defined $indent );

  my $cmd = " WHERE ";
  $spacer = create_spacer( length($cmd) );
  $query .= $cmd;

  my $field;
  my $first = 0;
  foreach $field ( @fields ) {
    if ( $data_ref->{$field} eq '' ) {
      next;
    }

    if ( $first ) {
      $query .= ",";
      $query .= "${indent}${spacer}" if ( defined $indent );
    }

    $query .= "`${field}` = '" . $data_ref->{$field} . "'";
    $first = 1;
  }

  return $query;
}



return 1;
