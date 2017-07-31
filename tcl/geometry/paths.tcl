namespace eval paths {

    proc is_paths {test} {
	if { $test == {} } {
	    return 0
	}

	foreach sub_test $test {
	    if { ![path::is_path $sub_test] } {
		return 0
	    }
	}

	return 1
    }

    proc display {paths} {
	foreach path $paths {
	    puts "   $path"
	}
    }

    proc sort {order paths} {
	set new_paths {}
	for { set i 0} { $i < [llength $order] } { incr i } {
	    set A [lindex $order $i]
	    set tmp_paths {}
	    foreach path $paths {
		if { [point::is_point $path] } {
		    continue
		} elseif { $A == [lindex $path 0] } {
		    lappend new_paths $path
		} else {
		    lappend tmp_paths $path
		}
	    }
	    set paths $tmp_paths
	}

	foreach path $paths {
	    lappend new_paths $path
	}

	return $new_paths
    }

    proc merge {paths {avoid {}}} {
	set modified 1
	while { $modified != 0 } {
	    set modified 0
	    set new_paths {}

	    for { set i 0 } { $i < [llength $paths] } { incr i } {
		set pathA [lindex $paths $i]
		for { set j [expr $i + 1] } { $j < [llength $paths] } { incr j } {
		    set pathB [lindex $paths $j]
		    set result [path::merge $pathA $pathB $avoid]
		    if { $result != {} } {
			set pathA $result
			set paths [lreplace $paths $j $j]
			set modified 1
		    }
		}

		if { [lsearch $new_paths $pathA] == -1 } {
		    lappend new_paths [path::simplify $pathA]
		}
	    }

	    set paths $new_paths
	}
	return $paths
    }
}
