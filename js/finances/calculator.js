// Determine if the browser is a blackberry browser.
var blackberry = ( navigator.userAgent.match( /^Blackberry/i ) !== null );

// Date formats.
var dateFormat = '%Y-%m-%d';
var dateTimeFormat = dateFormat + ' %H:%i:%S';

// The mapping between the numbers and the alphanumeric characters on the blackberry keyboard 
// * The numbers correspond to the array index.
var keyMapping = false;
if ( blackberry === true ) {
  keyMapping = new Array();
  // First row
  keyMapping['#'] = 113;
  keyMapping['1'] = 119;
  keyMapping['2'] = 101;
  keyMapping['3'] = 114;
  keyMapping['('] = 116;
  keyMapping[')'] = 121;
  keyMapping['_'] = 117;
  keyMapping['-'] = 105;  
  keyMapping['+'] = 111;  
  keyMapping['@'] = 112; 
  // Second row
  keyMapping['*'] = 97;
  keyMapping['4'] = 115;
  keyMapping['5'] = 100;
  keyMapping['6'] = 102;
  keyMapping['/'] = 103;  
  keyMapping[':'] = 104;
  keyMapping[';'] = 106;
  keyMapping['\''] = 107;
  keyMapping['"'] = 108;  
  // Third row 
  keyMapping['7'] = 122;
  keyMapping['8'] = 120;
  keyMapping['9'] = 99;
  keyMapping['?'] = 118;  
  keyMapping['!'] = 98;
  keyMapping[','] = 110;
  keyMapping['.'] = 109;
  // Last row.
  keyMapping['0'] = 48;
}

function toSymbol( code ) {
  if ( code >= 65 && code <= 90 ) {
    return toSymbol( code + 32 );
  }

  // Find the appropriate key from the ASCII 
  // character given. If the device is a Blackberry
  // map between the keys and the corresponding numbers
  // NOTE: The input should have already been defined
  // to only accept numbers, but the alphanumeric 
  // character is still given.
  if ( keyMapping !== false ) {
    for ( var symbol in keyMapping ) {
      if ( keyMapping[symbol] == code ) {
	return symbol;	
      }
    }
  }

  return String.fromCharCode( code );
}

//%FUNCTION: removeChar
//%DESCRIPTION: Used to remove a single character from the given
// string. In the case of multiple occurances, only the last
// one is removed.
//%ARGUMENTS:
// string -- The string to modify.
// char -- The character to remove.
//%RETURNS:
// The final string.
function removeChar( string, char ) {
  // Remove the last occurance of the given character.
  var result = -1;
  var index = result;
  do {
    result = string.indexOf( char, result+1 ); 
    if ( result != -1 ) {
      index = result;
    }
  } while ( result !== -1 );
  
  if ( index === -1 ) {
    return string;
  }

  var a = '';
  if ( index > 0 ) {
    a = string.substring(0,index);
  }
  var b = '';
  if ( index < ( string.length - 1 ) ) {
    b = string.substring(index+1,string.length-1);
  }

  return a+b;
}

//%FUNCTION: validate
//%DESCRIPTION: Used to validate the event of a numeric entry
// to make sure that only valid keys (numbers and periods)
// are input to the text boxes.
//%ARGUMENTS:
// event -- The object corresponding to the event
// type -- The type of verification to perform.
//%RETURNS:
// TRUE if the input is valid, FALSE otherwise.
function validate( event, entry, type ) {
  var value = entry.value;
  var original = value;

  var result = 0;

  if ( navigate( event, entry ) === false ) {
    result = false;
  }

  var event = event || window.event;
  var char = event.keyCode || event.which;
  if ( char == 8 ) { // DELETE
    return true;
  }
  
  var pattern = '^\S$';
  if ( type == 'integer' ) {
    pattern = '^[0-9]$';
  } else if ( type == 'currency' ||
	      type == 'quantity' ) {
    pattern = '^[0-9\.]$';
  }
  
  var regex = new RegExp( pattern );
  var key = toSymbol( char );

  //alert( type + " " + char + " " + key + " " + pattern + " " + regex.test( key ) );
  if ( result === 0 && regex.test( key ) === false ) {
    result = false;
  }

  if ( blackberry === false ) {
    value += key;
  }

  if ( result === 0 ) {
    // Only 3 decimal points allowed for quantity
    if ( type == 'quantity' ) {      
      if ( value.match( /^\d*(\.\d{0,3})?$/ ) === null ) {
	result = false;
      }
    }
    // Only 2 decimal points allowed for currency.
    else if ( type == 'currency' ) {
      if ( value.match( /^\d*(\.\d{0,2})?$/ ) === null ) {
	result = false;
      }
    } else {
      // Only 1 decimal point
      if ( value.match( /^\d*(\.\d*)?$/ ) === null ) {
	result = false;
      }
    }
  }

  if ( result === false ) {   
    if ( blackberry === true || 1 ) {
      original = removeChar( original + key, key ); 
      entry.value = original;
    }
    return false;
  }

  return true;
}

function cleanup( entry, zeros ) {
  var value = entry.value;
  var result = value.match( /^0([^0]+.*)$/ );
  if ( result !== null ) {
    value = result[1];
  }
  if ( zeros > 0 ) {
    value = parseFloat( value ).toFixed(zeros);
  }
  entry.value = value;
}

// The array of entries added to the page to allow for each
// traversal.
var items = new Array();

//%FUNCTION: addItem
//%DESCRIPTION: Used to add an item to the array for a specific
// table, row and column combination.
//%ARGUMENTS:
// table -- The table number
// row -- The row number
// column -- The column number
// entry -- The entry to add.
//%RETURNS:
// Nothing.
function addItem( table, row, column, entry ) {
  if ( items.length <= table ) {
    items[table] = new Array();
  }
  if ( items[table].length <= row ) {
    items[table][row] = new Array();
  }
  items[table][row][column] = entry;
}

//%FUNCTION: targetItem
//%DESCRIPTION: Used to retrieve the entry corresponding to
// the given a starting table, row, column and direction.
//%ARGUMENTS:
// table -- The table number
// row -- The row number
// column -- The column number
// direction -- The direction to the next available entry.
//%RETURNS:
// The entry in the given direction, if one exists.
function targetItem( table, row, column, direction ) {
  var tIndex = 0;
  var rIndex = 0;
  var cIndex = 0;

  var prev = null;
  var up = null;
  var found = 0;

  for( tIndex = 1; tIndex <= items.length; tIndex++ ) {
    if ( items[tIndex].length == 0 ) {
      continue;
    }
    for( rIndex = 1; rIndex <= items[tIndex].length; rIndex++ ) {
      if ( items[tIndex][rIndex] === undefined ) {
	continue;
      }     
      for ( cIndex = 0; cIndex <= items[tIndex][rIndex].length; cIndex++ ) {
	item = items[tIndex][rIndex][cIndex];
	if ( tIndex == table &&
	     rIndex == row &&
	     cIndex == column ) {
	  if ( direction == 'prev' ) {
	    return prev;
	  }
	  found = 1;
	} else if ( found ) {
	  if ( direction == 'next' ) {
	    return item;
	  }
	}

	if ( tIndex <= table &&
	     rIndex <= row &&
	     cIndex == column ) {
	  if ( direction == 'up' &&
	       found == 1 ) {
	    return up;
	  }
	  up = item;
	} else if ( tIndex >= table &&
		    rIndex >= row &&
		    cIndex == column ) {
	  if ( direction == 'down' &&
	       found == 1 ) {
	    return item;
	  }
	}

	prev = item;
      }
    }
  }

  return null;
}

// The array of navigation keys. A representation
// of all keys that correspond to a direction.
var navigationKeys = new Array();
navigationKeys['37'] = 'prev'; // BACK arrow
navigationKeys['38'] = 'up';   // UP arrow
navigationKeys['9']  = 'next'; // <tab>
navigationKeys['39'] = 'next'; // FORWARD arrow
navigationKeys['40'] = 'down'; // DOWN arrow
if ( blackberry === true ) {
  navigationKeys['64'] = 'next';  // @
  navigationKeys['80'] = 'next';  // P
  navigationKeys['112'] = 'next'; // p
  navigationKeys['35'] = 'prev';  // #
  navigationKeys['81'] = 'prev';  // Q
  navigationKeys['113'] = 'prev'; // q
  navigationKeys['42'] = 'up';    // *
  navigationKeys['65'] = 'up';    // A
  navigationKeys['97'] = 'up';    // a
  navigationKeys['43'] = 'down';  // +
  navigationKeys['79'] = 'down';  // O
  navigationKeys['111'] = 'down'; // o
}

//%FUNCTION: navigate
//%DESCRIPTION: Used to transition between entries on the
// page if the appropriate direction key is pressed.
//%ARGUMENTS:
// event -- The key event that may trigger a move.
// entry -- The entry the cursor is currently in.
//%RETURNS:
// TRUE if the navigation was successful, FALSE 
// otherwise.
function navigate( event, entry ) {
  if ( entry == null ) {
    return false;
  }

  var event = event || window.event;
  var char = event.keyCode || event.which;
  var direction = navigationKeys[char];
  if ( direction === undefined ) {
    return true;
  }

  var name = entry.name;
  var results = name.match( /^receipt(\d+)(\w+)(\d+)/ );
  if ( results.length == 0 ) {
    return false;
  }

  var table = results[1];
  var type = results[2];
  var column = 0;
  if ( type == 'quantity' ) {
    column = 1;
  } else if ( type == 'unit_price' ) {
    column = 2;
  } else if ( type == 'tax' ) {
    column = 3;
  }
  row = results[3];

  target = targetItem( table, row, column, direction );
  if ( target != null ) {
    target.focus();
    target.click();
    var value = target.value;
    target.value = '';
    target.value = value;
  } 
  
  return false;
}

//%FUNCTION: getType
//%DESCRIPTION: Used to retrieve the name/type of the 
// given object.
//%ARGUMENTS:
// object -- The object to analyze.
//%RETURNS:
// The resulting name string or NULL if none could be
// found.
function getType( object ) {
  var type = typeof( object );
  if ( type !== 'object' ) {
    return type;
  } else if ( type == 'object' ) {
    var object_type = Object.prototype.toString.call(object);
    return object_type.substring(8,object_type.length-1);
  }
  return null;
}

//%FUNCTION: getRowItem
//%DESCRIPTION: Used to retrieve the corresponding element
// from the given table.
//%ARGUMENTS:
// tableName -- The name of the table.
// row -- The number of the row.
// name -- The name of the property.
// cell -- The column/cell on the given row.
// item -- The item number within the cell.
// type -- The type of object desired.
//%RETURNS:
// The resulting object if it could be found, otherwise
// NULL.
function getRowItem( tableName, row, name, cell, item, type ) {
  var element = document.getElementById( tableName + name + row );
  if ( element === null ) {      
    var table = document.getElementById( tableName );
    if ( table.rows.length < row || row < 0 ) {
      return null;
    }
    row = table.rows[row];
    if ( row.cells.length < (cell+1) ||
	 row.cells[cell].childNodes.length < (item+1) ) {
      return null;
    }
    element = row.cells[cell].childNodes[item];
  }

  var element_type = getType( element );
  if ( element_type != type ) {
    return null;
  }

  return element;
}

// To find the 'date' entry in the table row.
function getDate( tableName, row ) {
  return getRowItem( tableName, row, 'date', 0, 0, 'HTMLInputElement' );
}

// To find the 'product' entry in the table row.
function getProduct( tableName, row ) {
  return getRowItem( tableName, row, 'product', 1, 0, 'HTMLSelectElement' );
}

// To find the 'quantity' entry in the table row.
function getQuantity( tableName, row ) {
  return getRowItem( tableName, row, 'quantity', 2, 0, 'HTMLInputElement' );
}
 
// To find the 'unit_price' entry in the table row.
function getUnitPrice( tableName, row ) {
  return getRowItem( tableName, row, 'unit_price', 3, 1, 'HTMLInputElement' );
}

// To find the 'sub_total' entry in the table row.
function getSubTotal( tableName, row ) {
  return getRowItem( tableName, row, 'sub_total', 4, 1, 'HTMLSpanElement' );
}

// To find the 'tax' entry in the table row.
function getTax( tableName, row ) {
  return getRowItem( tableName, row, 'tax', 5, 0, 'HTMLSelectElement' );
}

// To find the 'tax_total' entry in the table row.
function getTaxTotal( tableName, row ) {
  return getRowItem( tableName, row, 'tax_total', 6, 1, 'HTMLSpanElement' );
}

//%FUNCTION: isRow
//%DESCRIPTION: Used to determine if the given row in the
// table is an itemized row.
//%ARGUMENTS:
// tableName -- The name of the table.
// row -- The number of the row.
//%RETURNS:
// TRUE if the given row exists as a itemized row in the
// given table, FALSE otherwise.
function isRow( tableName, row ) {
  if ( getTaxTotal( tableName, row ) === null ) {
    return false;
  }
  return true;
}  

//%FUNCTION: getCountryCode
//%DESCRIPTION: Used to retrieve the entry used to store the
// exchange rate amount in the table.
//%ARGUMENTS:
// tableName -- The name of the table.
//%RETURNS:
// The input if it exists, and NULL otherwise.
function getCountryCode( tableName ) {
  var element = document.getElementById( tableName + '-currency' );
  if ( element === null ) {
    var elements = document.getElementsByName( tableName + '-currency' );
    if ( elements.length == 0 ) {
      element = elements[0];
    }
  }
  
  var element_type = getType( element );
  if ( element_type != 'HTMLSelectElement' ) {
    return null;
  }

  var code = element.options[element.selectedIndex];
  if ( code === undefined ) {
    return null;
  }

  return code.value;
}

//%FUNCTION: getExchange
//%DESCRIPTION: Used to retrieve the entry used to store the
// exchange rate amount in the table.
//%ARGUMENTS:
// tableName -- The name of the table.
//%RETURNS:
// The input if it exists, and NULL otherwise.
function getExchange( tableName ) {
  var element = document.getElementById( tableName + '-exchange' );
  if ( element === null ) {
    var elements = document.getElementsByName( tableName + '-exchange' );
    if ( elements.length == 0 ) {
      element = elements[0];
    }
  }

  var element_type = getType( element );
  if ( element_type != 'HTMLInputElement' ) {
    return null;
  }

  return element;
}

//%FUNCTION: getAmount
//%DESCRIPTION: Used to retrieve the entry used to store the
// receipt amount in the table.
//%ARGUMENTS:
// tableName -- The name of the table.
//%RETURNS:
// The input if it exists, and NULL otherwise.
function getAmount( tableName ) {
  var element = document.getElementById( tableName + '-amount' );
  if ( element === null ) {
    var elements = document.getElementsByName( tableName + '-amount' );
    if ( elements.length == 0 ) {
      element = elements[0];
    }
  }

  var element_type = getType( element );
  if ( element_type != 'HTMLInputElement' ) {
    return null;
  }

  return element;
}

//%FUNCTION: getHomeAmount
//%DESCRIPTION: Used to retrieve the element used to represent the
// amount of the receipt in the HOME currency.
//%ARGUMENTS:
// tableName -- The name of the table.
//%RETURNS:
// The span if it exists, and NULL otherwise.
function getHomeAmount( tableName ) {
  var element = document.getElementById( tableName + '-amount-home' );
  if ( element === null ) {
    var elements = document.getElementsByName( tableName + '-amount-home' );
    if ( elements.length == 0 ) {
      element = elements[0];
    }
  }

  var element_type = getType( element );
  if ( element_type != 'HTMLSpanElement' ) {
    return null;
  }

  return element;
}
//%FUNCTION: getFullSubTotal
//%DESCRIPTION: Used to retrieve the span used to store the
// sub total value for this table/receipt.
//%ARGUMENTS:
// tableName -- The name of the table.
//%RETURNS:
// The span if it exists, and NULL otherwise.
function getFullSubTotal( tableName ) {
  var element = document.getElementById( tableName + '-sub_total' );
  if ( element === null ) {
    var table = document.getElementById( tableName ); 
    var lastRow = table.rows.length;
    element = getRowItem( tableName, lastRow-3, '-sub_total', 1, 2, 'HTMLSpanElement' );
  }

  var element_type = getType( element );
  if ( element_type != 'HTMLSpanElement' ) {
    return null;
  }

  return element;
}

//%FUNCTION: getFullTaxTotal
//%DESCRIPTION: Used to retrieve the span used to store the
// tax total value for this table/receipt.
//%ARGUMENTS:
// tableName -- The name of the table.
//%RETURNS:
// The span if it exists, and NULL otherwise.
function getFullTaxTotal( tableName ) {
  var element = document.getElementById( tableName + '-tax_total' );
  if ( element === null ) {
    var table = document.getElementById( tableName ); 
    var lastRow = table.rows.length;
    if ( lastRow >= 3 ) {      
      var row = table.rows[lastRow-3];
      element = getRowItem( tableName, lastRow-3, '-tax_total', 3, 2, 'HTMLSpanElement' ); 
    }
  }

  var element_type = getType( element );
  if ( element_type != 'HTMLSpanElement' ) {
    return null;
  }

  return element;
}

//%FUNCTION: getFullTotal
//%DESCRIPTION: Used to retrieve the span used to store the
// total value for this table/receipt.
//%ARGUMENTS:
// tableName -- The name of the table.
//%RETURNS:
// The span if it exists, and NULL otherwise.
function getFullTotal( tableName ) {
  var element = document.getElementById( tableName + '-full_total' );
  if ( element === null ) {
    var table = document.getElementById( tableName ); 
    var lastRow = table.rows.length;
    element = getRowItem( tableName, lastRow-2, '-full_total', 1, 2, 'HTMLSpanElement' );
  }

  var element_type = getType( element );
  if ( element_type != 'HTMLSpanElement' ) {
    return null;
  }

  return element;
}

//%FUNCTION: getRemainder
//%DESCRIPTION: Used to retrieve the span used to store the
// remainder of value left for this table/receipt.
//%ARGUMENTS:
// tableName -- The name of the table.
//%RETURNS:
// The span if it exists, and NULL otherwise.
function getRemainder( tableName ) {
  var element = document.getElementById( tableName + '-remainder' );
  if ( element === null ) {
    var table = document.getElementById( tableName ); 
    var lastRow = table.rows.length;
    element = getRowItem( tableName, lastRow-2, '-remainder', 2, 2, 'HTMLSpanElement' );
  }

  var element_type = getType( element );
  if ( element_type != 'HTMLSpanElement' ) {
    return null;
  }

  return element;
}

//%FUNCTION: calculateRow
//%DESCRIPTION: Used to caculate the sub total and tax total
// for a specified row.
//%ARGUMENTS:
// tableName -- The name of the table.
// row -- The number of the row being calculated.
// total -- Whether to calculate the total for the entire table.
//%RETURNS:
// Nothing.
function calculateRow( tableName, row, total ) {
   var quantity = getQuantity( tableName, row );
   var unit_price = getUnitPrice( tableName, row );  
   var sub_total = getSubTotal( tableName, row );
   if ( quantity === null || 
	unit_price === null || 
	sub_total === null ) {
     return false;
   }

   var sub_total_value = quantity.value * unit_price.value;

   // Calculate the total in tax.
   var tax_select = getTax( tableName, row );
   var tax_total = getTaxTotal( tableName, row );
   if ( tax_select === null || 
	tax_total === null ) {
     return false;
   }
   var tax = tax_select.options[tax_select.selectedIndex];
   var tax_total_value = tax.value * sub_total_value;   

   sub_total.innerHTML = sub_total_value.toFixed(2);
   tax_total.innerHTML = tax_total_value.toFixed(2);
   if ( total == 1 ) {
     calculateTotal( tableName, 0 );
   }

   return true;
}

function getAmountValue( tableName ) {
  var total = getAmount( tableName );
  if ( total === null ) {
    return 0;
  }
  return total.value;
}



//%FUNCTION: calculateTotal
//%DESCRIPTION: Used to calculate the total for an entire table.
//%ARGUMENTS:
// tableName -- The name of the table
// all -- Whether to calculate the total for each row.
//%RETURNS:
// Nothing.
function calculateTotal( tableName, all ) {
   var table = document.getElementById( tableName ); 
   var lastRow = table.rows.length;
   var lastItem = lastRow - 3;

   var sub_total = new Number(0.00);
   var tax_total = new Number(0.00);

   var index = 0;
   for ( index = 1; index < lastItem; index++ ) {
      if ( all == 1 ) {
	if ( calculateRow( tableName, index, 0 ) === false ) {
	  continue;
	}
      } else if ( isRow( tableName, index ) === false ) {
	continue;
      }

      var row = table.rows[index];
      
      // Add the sub-totals and tax_totals.
      sub_total += parseFloat( getSubTotal( tableName, index ).innerHTML );
      tax_total += parseFloat( getTaxTotal( tableName, index ).innerHTML );
   }

   // Add the sub totals.
   var full_sub_total = getFullSubTotal( tableName );
   var full_tax_total = getFullTaxTotal( tableName );
   if ( full_sub_total ) {
     full_sub_total.innerHTML = sub_total.toFixed(2);
   }
   if ( full_tax_total ) {
     full_tax_total.innerHTML = tax_total.toFixed(2);
   }

   // Add the total.
   var total = sub_total + tax_total;
   row = table.rows[lastRow-2];
   row.cells[1].childNodes[2].innerHTML = total.toFixed(2);

   // Calculate the remainder (if needed).
   var remainderElement = getRemainder( tableName );
   var totalInput = getAmount( tableName );
   if ( remainderElement !== null &&
	totalInput !== null ) {    
     var remainder = totalInput.value - total;
     var html = remainder.toFixed(2);
     if ( remainder < 0 ) {
       html = '<font color="#AA0000"><b>' + html + '</b></font>';
     } else if ( remainder == 0 ) {
       html = '<font color="#00AA00">' + html + '</font>';
     }
     remainderElement.innerHTML = html;
   }

   var exchangeInput = getExchange( tableName );
   var homeAmountElement = getHomeAmount( tableName ); 
   if ( exchangeInput !== null &&
	totalInput !== null &&
	homeAmountElement !== null ) {
     var amount = totalInput.value * exchangeInput.value;
     homeAmountElement.innerHTML = parseFloat( amount ).toFixed(2);
   }

   updateSymbols( tableName, false );
}

function addSymbol( tableName, container, element ) {
  var code = getCountryCode( tableName );
  var symbol = ex_symbols[code];

  var P = symbol + ' ';
  var S = '&nbsp;';
  if ( ex_prefix[code] === false ) {
    S = ' ' + symbol;
    P = '&nbsp;';
  }

  prefix = document.createElement( 'span' );
  prefix.setAttribute( 'class', 'currency' );
  prefix.setAttribute( 'name', tableName + 'symbolP' );
  prefix.innerHTML = P;
  container.appendChild( prefix );

  container.appendChild( element );

  suffix = document.createElement( 'span' );   
  suffix.setAttribute( 'class', 'currency' );
  suffix.setAttribute( 'name', tableName + 'symbolS' );
  suffix.innerHTML = S;
  container.appendChild( suffix );
}

function updateSymbols( tableName, home ) {
  var code = getCountryCode( tableName );
  var name = tableName + 'symbol';
  if ( home !== false ) {
    code = 'CAD';
    name = tableName + 'symbolHome';
  }
  var symbol = ex_symbols[code];

  var P = symbol + ' ';
  var S = '&nbsp;';
  if ( ex_prefix[code] === false ) {
    S = ' ' + symbol;
    P = '&nbsp;';
  }

  var elements = document.getElementsByName( name+'P' );
  for( var i = 0; i < elements.length; i++ ) {
    elements[i].innerHTML = P;
  }

  elements = document.getElementsByName( name+'S' );
  for( i = 0; i < elements.length; i++ ) {
    elements[i].innerHTML = S;
  }
}

//%FUNCTION: populateSelect
//%DESCRIPTION: To insert the array of options into the
// select dropdown.
//%ARGUMENTS:
// select -- The select dropdown.
// values -- The values to add.
//%RETURNS:
// Nothing.
function populateSelect( select, values ) {
  for (var key in values) {
    var option = document.createElement( 'option' );
    option.text = values[key];
    option.value = key;
    option.setAttribute( 'style', '{width: 400px}' );  
    select.add( option, null );
  }
}

//%FUNCTION: findIndex
//%DESCRIPTION: To find the index of the given value
// in the select dropdown.
//%ARGUMENTS:
// select -- The select dropdown to analyze.
// value -- The value to search for.
//%RETURNS:
// The index of the value.
function findIndex( select, value ) {    
  var index = 0;
  var otherIndex = 0;
  for (var index=0;index < select.options.length;index++) {
    var element = select.options[index];
    if (element.value == value) {
      return index;
    } else if (element.text == value) {
      otherIndex = index;
    }
  }
  return otherIndex;
}

// The arrays that contain the default Product
// and Tax information. These should be populated
// by the page the uses this code.
var products = new Array();
var product_default = 0;
var taxes = new Array();
var taxes_default = 0;

function addRow( tableName, settings, custom ) {
   var table = document.getElementById( tableName );
   var results = tableName.match( /(\d+)$/ );
   var tableNumber = results[1];

   var lastRow = table.rows.length - 3;

   var iteration = lastRow;
   var row = table.insertRow( lastRow );
   var element;
   var select;

   if ( !(settings instanceof Array) ) {
     settings = new Array();
     var date = '';
     var fullDate = document.getElementById( tableName + '.date' );
     var index = iteration;
     for ( index; index >= 0; index-- ) {
       var rowDate = getDate( tableName, index );
       if ( rowDate !== null ) {
	 date = rowDate.value;
       }
     }
     
     if ( date == '' && fullDate !== null ) {
       date = fullDate.value;      
     }

     if ( date.length >= 10 ) {
       date = date.substring(0,10);
     }

     settings['date'] = date;
     settings['product'] = product_default;
     settings['tax'] = taxes_default;
     settings['unit_price'] = 0.00;
     settings['quantity'] = 0;
   } else {
     var date = settings['date'];
     if ( date.length >= 10 ) {
       settings['date'] = date.substring(0,10);
     }
   }

   var itemizeDate = true;

   // Date cell
   var date = row.insertCell( 0 );
   if ( itemizeDate === false ) {
     element = document.createElement( 'span' );
     element.innerHTML = '&nbsp;';
     date.appendChild( element );
   } else {
     element = document.createElement( 'input' );
     element.setAttribute( 'value', settings['date'] );
     name = tableName + 'date' + iteration;
     element.name = name;
     element.id = name;
     element.setAttribute( 'type', 'text' );
     element.setAttribute( 'size', 9 );
     element.setAttribute( 'class', 'date' );
     date.appendChild( element );
     
     // Add the widget for selecting the date.
     AnyTime.picker( name,
		     { format: dateFormat,
			 hideInput: false,
			 placement: "popup" } );
   }
   
   // Product cell.
   var product = row.insertCell( 1 );
   var name = tableName + 'product' + iteration;
   if ( custom ) {
     element = document.createElement( 'input' );  
     element.setAttribute( 'type', 'text' );
   } else {
     element = document.createElement( 'select' );     
     jsselectmenu.attach( element, 'product',
			  jsselectmenu.bindMapping['product'] );
     jsselectmenu.set( element, settings['product'] );
   }
   element.setAttribute( 'class', 'product' );
   element.name = name;
   element.id = name;
   product.appendChild( element );
   addItem( tableNumber, iteration, 0, element );

   var calculate = 'calculateRow( \'' + tableName + '\', ' + iteration + ', 1 )';
   var keypressCurrency = 'return validate( event, this, \'currency\' )';
   var keypressQuantity = 'return validate( event, this, \'quantity\' )';

   // Quantity cell.
   var quantity = row.insertCell( 2 );
   element = document.createElement( 'input' );
   element.setAttribute( 'value', settings['quantity'] );
   name = tableName + 'quantity' + iteration;
   element.name = name;
   element.id = name;
   //element.setAttribute( 'input', 'number' );
   element.setAttribute( 'type', 'text' );
   element.setAttribute( 'size', 3 );
   element.setAttribute( 'class', 'quantity' );
   element.setAttribute( 'onkeypress', keypressQuantity );   
   element.setAttribute( 'onblur', 'cleanup( this, 0 );' + calculate );
   quantity.appendChild( element );
   addItem( tableNumber, iteration, 1, element );

   // Unit Price cell.
   var unit_price = row.insertCell( 3 );
   element = document.createElement( 'input' );
   element.setAttribute( 'value', settings['unit_price'].toFixed(2) );
   name = tableName + 'unit_price' + iteration;
   element.name = name;
   element.id = name;
   //element.setAttribute( 'input', 'number' );
   element.setAttribute( 'type', 'text' );
   element.setAttribute( 'size', 3 );
   element.setAttribute( 'class', 'currency' );
   element.setAttribute( 'onkeypress', keypressCurrency );
   element.setAttribute( 'onblur', 'cleanup( this, 2 );' + calculate );
   addSymbol( tableName, unit_price, element );
   addItem( tableNumber, iteration, 2, element );

   // Sub-Total cell.
   var sub_total = row.insertCell( 4 );
   element = document.createElement( 'span' );
   name = tableName + 'sub_total' + iteration;
   element.id = name;
   element.setAttribute( 'class', 'currency' );
   element.setAttribute( 'align', 'center' );
   element.style = '{text-align:right}';
   element.style.margin = '0px auto';
   element.innerHTML = '0.00';
   addSymbol( tableName, sub_total, element );

   // Tax cell.
   var tax = row.insertCell( 5 );
   select = document.createElement( 'select' );
   name = tableName + 'tax' + iteration;
   select.name = name;
   select.id = name;
   select.setAttribute( 'class', 'tax' );
   populateSelect( select, taxes );
   select.selectedIndex = findIndex( select, settings['tax'] );
   select.setAttribute( 'onchange', calculate );
   select.setAttribute( 'onkeypress', 'return navigate(event,this)' );
   select.setAttribute( 'onblur', calculate );
   tax.appendChild( select );
   addItem( tableNumber, iteration, 3, select );

   // Tax-Total cell.
   var tax_total = row.insertCell( 6 );
   element = document.createElement( 'span' );
   name = tableName + 'tax_total' + iteration;
   element.id = name;
   element.setAttribute( 'class', 'currency' );
   element.setAttribute( 'align', 'center' );
   element.style.margin = '0px auto';
   element.innerHTML = '0.00';
   addSymbol( tableName, tax_total, element );
}

$('input[name$="date"]').AnyTime_picker(
   { format: "%Y-%m-%d",
     hideInput: false,
     placement: "popup" } );
$('input[name$="datetime"]').AnyTime_picker(
   { format: "%Y-%m-%d %H:%i:%S",
     hideInput: false,
     placement: "popup" } );
