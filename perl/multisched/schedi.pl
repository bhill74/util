#!/usr/bin/perl
use strict;
use warnings;

use File::Spec;
my ($vol, $path, $file) = File::Spec->splitpath(__FILE__);
$path = File::Spec->rel2abs($path);
$path = File::Spec->catfile($path, '..', 'utils');
my $d = $^O eq 'win32' ? ";" : ":";
my $PATH = join($d, $path, File::Spec->path());
$ENV{PATH} = $PATH;
$ENV{SCHED_PORT} = `sched_port`;
my $pid = fork;
if ($pid == 0) {
    system('sched_serve');
    exit();
} else {
    sleep(1);
}

sub sched_bins() {
    my ($num) = @_;
    system("sched_bins $num");
}

sub sched_distribute() {
    system('sched_distribute');
}

sub sched_shutdown() {
    system('sched_shutdown');
    waitpid($pid, 0);
}

sub sched_submit() {
    my $cmd = @_;
    my $id = `sched_submit $cmd`;
    chomp $id;
    return $id;
}

sub sched_wait() {
    my $ids = @_;
    system("sched_wait $ids");
}

1;
