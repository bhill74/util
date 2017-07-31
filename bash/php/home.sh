phpHome() {
   local php_home=/usr
   local version=$(ls -d /depot/php-*/bin | sed "s|/depot/||" | sed "s|/bin||" | sort -t. -k 2,2n -k 3,3n -k 4,4n | tail -1)
   if [ ! -z "$version" ]; then
      php_home=/depot/${version}
   fi
   echo $php_home
}
