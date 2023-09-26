#!/usr/bin/perl
use strict;
use warnings;

package MultiSched;

use File::Spec;
my $SERVE_PID = -1;

sub startup() {
    my ($vol, $path, $file) = File::Spec->splitpath(__FILE__);
    $path = File::Spec->rel2abs($path);
    $path = File::Spec->catfile($path, '..', 'utils');
    my $d = $^O eq 'win32' ? ";" : ":";
    my $PATH = join($d, $path, File::Spec->path());
    $ENV{PATH} = $PATH;
    $ENV{SCHED_PORT} = `sched_port`;
    chomp $ENV{SCHED_PORT};
    $SERVE_PID = fork;
    if ($SERVE_PID == 0) {
        system('sched_serve');
        exit();
    } else {
        sleep(1);
        END { mshutdown(); }
    }
}

sub set_param() {
    my ($key, $value) = @_;
    $ENV{MULTISCHEDCONFIG} = `sched_set_param $key $value`;
}

sub remove_param() {
    my ($key) = @_;
    $ENV{MULTISCHEDCONFIG} = `sched_remove_param $key`;
}

sub bins() {
    my ($num) = @_;
    system("sched_bins $num");
}

sub distribute() {
    system('sched_distribute');
}

sub mshutdown() {
    # For some reason the callback is called twice from END, this check distinguishes it.
    return if ($SERVE_PID == 0);
    system('sched_shutdown');
    waitpid($SERVE_PID, 0);
    $SERVE_PID = 0;
}

sub submit() {
    my $cmd = join(' ', @_);
    my $id = `sched_submit $cmd`;
    chomp $id;
    return $id;
}

sub wait() {
    my $ids = join(' ', @_);
    system("sched_wait $ids");
}

sub wait_attrib() {
    my $attrib = shift;
    my $values = join(' ', @_);
    system("sched_wait --attrib $attrib $values");
}

sub status() {
    my $ids = join(' ', @_);
    my $status = `sched_status $ids`;
    chomp $status;
    return $status;
}

1;
