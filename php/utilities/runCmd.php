<?php

function cmd_output($cmd) {
    if ($_GET[debug]) {
		print "<pre><b>$cmd</b></pre>\n";
	}
	return trim(shell_exec($cmd));
}

function resolve($dir) 
{
    if (is_dir($dir)) {
        $cmd .= "pushd $dir >/dev/null 2>&1;";
        $cmd .= "pwd;";
        $result = cmd_output($cmd);
    } else (is_file($dir) && preg_match('|^(.*/)([^/]+)$|', $dir, $matches)) {
        return resolve($matches[1]) . $matches[2];
    }
    
    if ($result == '') {
        $cmd = "bash;eval t=$dir;echo \$t";
        $result = cmd_output($cmd);
    } else if (preg_match('|/$|', $dir, $matches)) {
        $result .= '/';
    }

    if ($result == $dir && preg_match('|^\~([^/]+)(/.*)*|', $dir, $matches)) {
        $user = $matches[1];
        $cmd = "ypcat -k passwd | egrep \"^${user} \" | cut -f6 -d:";
        $result = cmd_output($cmd) . $matches[2];
        if (file_exists($result) == false) {
            $result = '';
        }
    }

    return $result;
}

function unresolve($dir, $paths) 
{
    if (preg_match('|^\~([^/]+)(/.*)*|', $dir, $matches)) {
        $user = $matches[1];
        return preg_replace("|^.*?/${user}(/.*)*|", "~${user}\${1}", $paths);
    }   
    return $paths;
}

$results = array();
$dir = $_GET[dir];

switch ($_GET[type]) {
        case "sub":
                $dir = resolve($dir);            
		array_push($results, cmd_output("ls $dir 2>/dev/null"));
		break;
        case "complete":
                $rdir = resolve($dir);
                $paths = explode("\n", cmd_output("ls -d $rdir* 2>/dev/null"));
                if (count($paths) == 1 && $paths[0] == '' && file_exists($rdir)) {
                    array_push($paths, $rdir);
                } else if (count($paths) == 1 && is_dir($paths[0])) {
                    $paths[0] .= "/";
                }
                $results = unresolve($dir, $paths);
		break;
	case "space":
	        $paths = array();
	        foreach (explode(":", $dir) as $path) {
		        array_push($paths, resolve($path));
		}
		$shorts = array();
		$sizes = array();
		foreach ($paths as $path) {
                        $path = resolve($path);                    
			cmd_output("cd $path 2>/dev/null");
			if (preg_match('|^(/[^/]+/[^/]+)|', $path, $matches)) {
				$shorts[$path] = $matches[1];
				if (file_exists($shorts[$path]) == false) {
					$sizes[$path] = 'N/A';
				}	
			} else {
				$shorts[$path] = $path;
				$sizes[$path] = 'N/A';
			}
		}
		foreach (explode("\n", cmd_output("df -h")) as $row) {
			$info = preg_split('/\s+/', $row);
			foreach ($paths as $path) {
				if ($sizes[$path] == '' && $shorts[$path] == $info[5]) {
					$sizes[$path] = $info[4];
				}
			}
		}
		foreach ($paths as $path) {
		    array_push($results, $shorts[$path] . " [" . $sizes[$path] . "]");
		}	
		break;
    case "resolve":
		array_push($results, resolve($dir));
		break;
	default:	
		print "UNKNOWN TYPE: " . $_GET[type];
		break;
}
if ($_GET[format]) {
	print "<pre>" . implode("\n", $results) . "</pre>\n";
} else {
	print implode("\n", $results);
}	
?>
