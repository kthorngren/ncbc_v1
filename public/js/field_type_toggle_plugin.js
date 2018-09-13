// toggle field type plug-in code
(function ($, DataTable) {
 //console.log('function ($, DataTable)');
if ( ! DataTable.ext.editorFields ) {
    DataTable.ext.editorFields = {};
}
 
var Editor = DataTable.Editor;
var _fieldTypes = DataTable.ext.editorFields;
 //console.log(' _fieldTypes',  _fieldTypes);
 
_fieldTypes.toggle = {
    create: function ( conf ) {
    	//console.log('create func');
        var that = this;
 
        conf._enabled = true;
        conf._input = $('<input/>').attr($.extend({
        	type: 'checkbox',
        	}, conf.attr || {}));
        return conf._input;
    },
 
    get: function ( conf ) {
    	//console.log('get func');
        return $(conf._input).prop( 'checked' ) ? 1 : 0;
    },
 
    set: function ( conf, val ) {
    	//console.log('set func');
        $(conf._input).bootstrapToggle({size: 'mini'});
        $(conf._input).prop( 'checked', val == 1 ).change();
    },
 
    enable: function ( conf ) {
    	//console.log('enable func');
        conf._enabled = true;
        $(conf._input).removeClass( 'disabled' );
    },
 
    disable: function ( conf ) {
    	//console.log('disable func');
        conf._enabled = false;
        $(conf._input).addClass( 'disabled' );
    }
};
 
})(jQuery, jQuery.fn.dataTable);
