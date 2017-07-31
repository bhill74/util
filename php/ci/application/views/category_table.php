<?php if ( $edit !== false ) form_open( "category" ); ?>

<table border=1 cellpadding=0 cellspacing=0>
<tr>
<?php

$buttonWidth = 15;
$cellWidth = 150;
$directions = array( 'T' => 'Up', 'B' => 'Down', 
                     'L' => 'Left', 'R' => 'Right' );

/*****************************************
 *%FUNCTION: shiftButton()
 *%DESCRIPTION:
 * Used to create a link that will shift a category in a given direction
 *%ARGUMENTS:
 * url -- The url to with (minus the direction parameter).
 * direction -- The direction to account for. 
 *%RETURNS:
 * The HTML code for the option. 
 */
function shiftButton( $url, $direction ) {
    global $directions, $buttonWidth;
    $string = $directions[$direction];
    $image = img( array( 'src' => 'images/buttons/' . strtolower( $string ) . '.png',
                         'alt' => "[${string}]",
                         'width' => $buttonWidth,
                         'align' => 'right' ) );
    return "<a href=\"${url}&direction=" . strtolower($string) . "\">$image</a>\n";    
    //return HTML::wrap( 'a', $image, array( 'href' => "${url}&direction=" . strtolower( $string ) ) );
}

/*****************************************
 *%FUNCTION: shiftButtons()
 *%DESCRIPTION:
 * Used to create a series of links that 
 * will shift the category in the given directions.
 *%ARGUMENTS:
 * url -- The url to with (minus the direction parameter).
 * directions -- The directions to account for. 
 *%RETURNS:
 * The HTML code for the options. 
 */
function shiftButtons( $url, $directions ) {
    $buttons = array();
    foreach ( preg_split( '//', $directions ) as $direction ) {
        if ( $direction == '' ) {
            continue;
        }
        array_push( $buttons, shiftButton( $url, $direction ) );
    }
    return implode( '<br/>', $buttons );
}  

function add( $category ) {   
    $settings = $category;
    if (!is_array($settings)) {
        $settings['value'] = $category;
    }
    $settings['name'] = 'names';
    return form_input( $settings, $settings['value'] );
}

function color( $name, $value = '', $settings = array() ) {
    $settings['class'] = 'color';
    if ( !isset( $settings['size'] ) ) {
        $settings['size'] = 6;
    }
    return form_input($settings, $value);
}

function nickname( $category, $nickname = '' ) {   
    $settings = array( 'size' => 3, 
                       'name' => 'nickname' );
    return form_input( $settings, $nickname );
} 

function cell( $category, $info, $directions, $url ) {
    global $cellWidth, $buttonWidth;
    $html = "<table cellpadding=0 cellspacing=0 width=" . $cellWidth . ">\n";
    $html .= "<tr><td width=" . ( $cellWidth - $buttonWidth ) . ">\n";
    $html .= "<font size=+2><b>$category</b></font><br>\n";
    $html .='<font size=-2><i>[' . $info['left'] . ', ' . $info['right'] . ' - ' . $info['depth'] . ']</i></font>';
    $html .= "</td><td valign=top align=right rowspan=3 width=" . $buttonWidth . ">&nbsp;";
    if ( $url !== false ) {
        $html .= shiftButtons( $url, $directions );
    }
    $html .= "</td></tr>\n";

    if ( $url !== false ) {
        $html .= "<td>Color: ";
        $html .= color( $category, $info );
        $html .= "</td></tr>\n<td>Nickname: ";
        $html .= nickname( $category, $info );	 
        $html .= "</td></tr>\n";
    }
   
    $html .= "</table>\n";
    return $html;
}

/*****************************************
 *%FUNCTION: makeRow()
 *%DESCRIPTION:
 * Used to create a recursive construction
 * of a row representing a hierarchy of categories.
 *%ARGUMENTS:
 * tree -- The tree to build for.
 * url -- The url for editing these categories.
 * count -- The referenced counter to populate with the
 * the total number of rows in the tree.
 * level -- The current level being processed in the
 * tree, by default is 1.
 *%RETURNS:
 * The HTML code for the options.
 */
function makeRow( $tree, $url = false, &$count = 0, $level = 1 ) {
    $html = '';
    $categories = array_keys( $tree );
    $category_first = $categories[0];
    $category_last = end( $categories );
    $category_num = sizeof( $categories );
    global $cellWidth, $all_info;

    foreach ( $categories as $category ) {
        $items = $tree[$category];
        
        $info = $all_info[$category];
        print_r($info);
        return $html;

        /* Determine which directions this category can move */
        $directions = '';
        if ( $category_num > 1 ) {
            if ( $category != $category_first ) {
                $directions .= 'L';
                $directions .= 'B';
            }
            if ( $category != $category_last ) {
                $directions .= 'R';
            }
        }
        /* Only sub level categories can move up */
        if ( $level != 1 ) {
            $directions .= 'T';
        }
        
        /* Determine the content of the cell */
        $moveUrl = "${url}?name=${category}";
        
        /* If there are more items below this one */
        $sub_count = 1;
        $sub_html = '';
        if ( sizeof( $items ) > 0 ) {
            $sub_count = 0;
            $sub_html = makeRow( $items, $url, $sub_count, $level + 1 );
            if ( $url !== false ) {
                $sub_html .= "<td>New: " . add( $category ) . "</td></tr>\n<tr>";
                $sub_count += 1;
            }
            $count += $sub_count;
        } else {
            $count += 1;
        }
        
        $html .= "<td valign=middle width=" . $cellWidth . " bgcolor=\"#$info[color]\" rowspan=${sub_count}>";
        $html .= cell( $category, $info, $directions, $moveUrl );
        $html .= "</td>";
        
        if ( $sub_html != '' ) {
            $html .= $sub_html;
        } else {
            $html .= "</tr>\n<tr>";
        }
    }
    
    return $html;
}

echo makeRow($tree, $url);

?>

</table>
<?php if ( $edit !== false ) form_close(); ?>

?>
