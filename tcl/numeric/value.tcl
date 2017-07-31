namespace eval value {

    proc min {A B} {
	if { $A < $B } {
	    return $A
	}
	return $B
    }

    proc max {A B} {
	if { $A > $B } {
	    return $A
	}
	return $B
    }

    proc equal {A B} {
	set a [concat "v" $A]
	set b [concat "v" $B]
	if { $a == $b } {
	    return 1
	}
	return 0
    }

    proc isNumeric {V} {
	if {![catch {expr {abs($V)}}]} {
	    return 1
	}
	set V [string trimleft $V 0]
	if {![catch {expr {abs($V)}}]} {
	    return 1
	}
	return 0
    }
}
