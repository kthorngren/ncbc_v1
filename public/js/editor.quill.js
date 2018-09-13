(function( factory ){
    if ( typeof define === 'function' && define.amd ) {
        // AMD
        define( ['jquery', 'datatables', 'datatables-editor'], factory );
    }
    else if ( typeof exports === 'object' ) {
        // Node / CommonJS
        module.exports = function ($, dt) {
            if ( ! $ ) { $ = require('jquery'); }
            factory( $, dt || $.fn.dataTable || require('datatables') );
        };
    }
    else if ( jQuery ) {
        // Browser standard
        factory( jQuery, jQuery.fn.dataTable );
    }
}(function( $, DataTable ) {
'use strict';
 
 
if ( ! DataTable.ext.editorFields ) {
    DataTable.ext.editorFields = {};
}
 
var _fieldTypes = DataTable.Editor ?
    DataTable.Editor.fieldTypes :
    DataTable.ext.editorFields;
 
 
// Default toolbar, as Quill doesn't provide one
var defaultToolbar =
    '<div id="toolbar-toolbar" class="toolbar">'+
        '<span class="ql-formats">'+
            '<select class="ql-font">'+
                '<option selected=""></option>'+
                '<option value="serif"></option>'+
                '<option value="monospace"></option>'+
            '</select>'+
            '<select class="ql-size">'+
                '<option value="small"></option>'+
                '<option selected=""></option>'+
                '<option value="large"></option>'+
                '<option value="huge"></option>'+
            '</select>'+
        '</span>'+
        '<span class="ql-formats">'+
        '<button class="ql-bold"></button>'+
        '<button class="ql-italic"></button>'+
        '<button class="ql-underline"></button>'+
        '<button class="ql-strike"></button>'+
        '</span>'+
        '<span class="ql-formats">'+
        '<select class="ql-color"></select>'+
        '<select class="ql-background"></select>'+
        '</span>'+
        '<span class="ql-formats">'+
            '<button class="ql-list" value="ordered"></button>'+
            '<button class="ql-list" value="bullet"></button>'+
            '<select class="ql-align">'+
                '<option selected=""></option>'+
                '<option value="center"></option>'+
                '<option value="right"></option>'+
                '<option value="justify"></option>'+
            '</select>'+
        '</span>'+
        '<span class="ql-formats">'+
        '<button class="ql-link"></button>'+
        '</span>'+
    '</div>';
 
 
_fieldTypes.quill = {
    create: function ( conf ) {
        var safeId = DataTable.Editor.safeId( conf.id );
        var input = $(
            '<div id="'+safeId+'" class="quill-wrapper">'+
                (conf.toolbarHtml || defaultToolbar)+
                '<div class="editor"></div>'+
            '</div>'
        );
 
        conf._quill = new Quill( input.find('.editor')[0], $.extend( true, {
            theme: 'snow',
            modules: {
                toolbar: {
                    container: $('div.toolbar', input)[0]
                }
            }
        }, conf.opts ) );
 
        return input;
    },
  
	get: function ( conf ) {
    	return conf._quill.root.innerHTML;
	},
 
	set: function ( conf, val ) {
    	conf._quill.root.innerHTML = val !== null ? val : '';
	},
  
    enable: function ( conf ) {}, // not supported by Quill
  
    disable: function ( conf ) {}, // not supported by Quill
  
    // Get the Quill instance
    quill: function ( conf ) {
        return conf._quill;
    }
};
 
 
}));