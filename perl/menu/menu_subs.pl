sub init_choices() {
    my @choices = ();
    if (! -t STDIN) {
        my @c = <STDIN>;
        map { chomp; } @c;
        push(@choices, @c);
    }
    return @choices;
}

sub output() {
    my $menu = shift;
    my $delim = shift;
    my $file = shift;

    my $output = join( $delim, $menu->prompt );
    $output .= $delim if ( $delim eq "\n" );
    if ( $file ) {
        `echo '$output' > $file`;
    } else {
        print $output;
    }
}

return 1;
