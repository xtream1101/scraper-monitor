'use strict';

_.templateSettings = {interpolate: /\{\{(.+?)\}\}/g};

var page = window.location.pathname;
var url = window.location.origin + page;

var _template = {
    runningScraper: _.template(
        '<div id="{{rowId}}" class="running scraper">' +
            '<span class="uuid">UUID: <span class="value">{{uuid}}</span></span><br />' +
            '<span class="name">Name: <span class="value">{{name}}</span></span><br />' +
            '<span class="startTime">Start: <span class="value">{{startTime}}</span></span><br />' +
            '<span class="stopTime">Stop: <span class="value">{{stopTime}}</span></span><br />' +
            '<span class="runtime">Runtime: <span class="value">{{runtime}}</span></span><br />' +
            '<span class="criticalCount">Crits: <span class="value">{{criticalCount}}</span></span><br />' +
            '<span class="errorCount">Err: <span class="value">{{errorCount}}</span></span><br />' +
            '<span class="warningCount">Warn: <span class="value">{{warningCount}}</span></span><br />' +
        '</div>'
    ),
    deleteBtn: _.template('<button class="btn-del" data-id="{{rowId}}">Delete</button>'),
}

$(function(){
    initPage();

    // Opens/selects correct menu item
    setActiveMenuItem();

    $('body').on( 'click', '.btn-del', function( event ){
        var id = event.target.dataset.id;
        $.getJSON(url + '/delete/' + id)
    });

    $('.sub-menu-item').on( 'click', function( event ){
        localStorage.setItem('sm-activeMenu', '#' + event.currentTarget.id);
    });    
});

function initPage(){
    var $form = null;
    var socketListen = null;
    var socket = io.connect( url );

    if( page === '/manage/apikeys' ){
        socketListen = 'manage-apikeys';
        $form = $('#add-apikey');
    }else if( page === '/manage/scrapers' ){
        socketListen = 'manage-scrapers';
        $form = $('#add-scraper');
    }else if( page === '/manage/groups' ){
        socketListen = 'manage-groups';
        $form = $('#add-group');
    }else if( page === '/data/scrapers' ){
        socketListen = 'data-scrapers';
    }

    if( socketListen !== null ){
        socket.on(socketListen, function( data ){
            console.log("WebSocket: ", data);
            if( page === '/data/scrapers' ){
                addToScraperList(data)
            }else{
                addToTable(data, socketListen);
            }
        });
    }
    if( $form !== null ){
        // Submit the form data to add a new item
        $form.on( "submit", function( event ){
            event.preventDefault();
            var datastring = $form.serialize();
            $.ajax({
                type: "POST",
                url: url,
                data: datastring,
                success: function( data ){
                    $form.trigger("reset");
                    console.log("Action response: ", data);
                }
            });
        });
    }
}

function setActiveMenuItem(){
    var itemId = localStorage.getItem('sm-activeMenu');
    var $item = $(itemId);
    var $parent = $item.parent();
    var $menuHeader = $parent.prev();
    $item.addClass('active');
    $parent.addClass('in');
    $menuHeader.addClass('active');
}

function addToScraperList( response ){
    var action = response.action;
    var data = response.data;
    var $running = $('#running');
    var $finished = $('#finished');

    $.each( data, function( i, scraper ){
        // Check to see if scraper run exists in $running
        var $scraperRun = $running.find('#'+scraper.rowId);

        // Not in running list so add it
        if( action === 'add' ){
            $running.append(_template.runningScraper(scraper));
        }else if( action === 'update' || action === 'increment' ){
            // Update the values
            $.each( scraper, function( field, value ){
                var $field = $scraperRun.find('.' + field).find('.value');
                if( action === 'increment' ){
                    var currVal = parseInt($field.text());
                    value = currVal + value;
                }
                $field.html(value);
            });

            // Check if stopTime is not null, if null move to $finished with updated content
            if( typeof scraper.stopTime !== 'undefined'){
                $scraperRun.appendTo($finished);
            }
        }
    });
}

function addToTable( response, tableName ){
    var table = $('#tbl-' + tableName).DataTable();
    var action = response.action;
    var rows = response.data;

    $.each( rows, function( i, rowData ){
        var dtRowId = table.row('[id=jdt-' + rowData.rowId + ']').index();
        if( action === 'update' || action === 'add' || action === 'increment'){
            rowData.action = _template.deleteBtn(rowData);
            rowData.timeAdded = moment(rowData.timeAdded).format("YYYY-MM-DD HH:mm")
            if( dtRowId >= 0 ){
                table.row(dtRowId).data(rowData).draw();
            }else{
                table.row.add(rowData).draw();
            }
        }else if( action === 'delete' ){
            if( dtRowId >= 0 ){
                table.row(dtRowId).remove().draw();
            }
        }
    });
}
