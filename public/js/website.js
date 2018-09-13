$(document).ready(function() {
	function get_data_collection(data) {
    	return $.ajax({
        	url: "get_data_collection",
	        async: false,
    	    data: { data }
	    }).responseText
	}

	function testbed_name() {
    	return $.ajax({
        	url: "get_active_testbed_name",
	        async: false,
    	    data: { }
	    }).responseText
	}

    var tb_name = testbed_name();
     if (tb_name != '') {
       tb_name = tb_name + ' '
     }
	$('#page-title').html(tb_name + page_name);
	$('#main-title').html('<h4>' + tb_name + '</h4>');
	//$('#info-title').html(page_name);
	$('#nav-title').html(tb_name);
	//$('#table-title').html(page_name);

    $.ajax({
        url: "get_testbed_links",
        data: { }
    }).done(function (data) {
    	var data = JSON.parse(data);
        $.each(data, function(i, obj) {
        	$('#testbed-links').append(  function() {
        		return $('<li/>').html($('<a>')
        			.attr('href', obj['href'])
        			.attr('target', obj['target'])
        			.html(obj['name']))
        	});
        });
    });


});
