_.templateSettings = {interpolate: /\{\{(.+?)\}\}/g};

$(document).ready(function(){
    $('#tbl-manage-apikeys').DataTable({
        aaSorting: [ [1, 'asc']],
        columnDefs: [
            { "visible": false, "targets": 0 }  // Hide the rowId column
        ],
        columns: [
            { data: 'rowId' },
            { data: 'name' },
            { data: 'key' },
            { data: 'host' },
            { data: 'timeAdded' },
            { data: 'action' },
        ],
        fnRowCallback: function( nRow, aData, iDisplayIndex, iDisplayIndexFull ){
            // Add the apikey id as an id for the row
            $(nRow).attr('id', 'jdt-' + aData.rowId);
        },
    });
    $('#tbl-manage-scrapers').DataTable({
        aaSorting: [ [1, 'asc'], [2, 'asc'] ],
        columnDefs: [
            { "visible": false, "targets": 0 }  // Hide the rowId column
        ],
        columns: [
            { data: 'rowId' },
            { data: 'group' },
            { data: 'name' },
            { data: 'owner' },
            { data: 'key' },
            { data: 'timeAdded' },
            { data: 'action' },
        ],
        fnRowCallback: function( nRow, aData, iDisplayIndex, iDisplayIndexFull ){
            // Add the apikey id as an id for the row
            $(nRow).attr('id', 'jdt-' + aData.rowId);
        },
    });
    $('#tbl-manage-groups').DataTable({
        aaSorting: [ [1, 'asc']],
        columnDefs: [
            { "visible": false, "targets": 0 }  // Hide the rowId column
        ],
        columns: [
            { data: 'rowId' },
            { data: 'name' },
            { data: 'action' },
        ],
        fnRowCallback: function( nRow, aData, iDisplayIndex, iDisplayIndexFull ){
            // Add the apikey id as an id for the row
            $(nRow).attr('id', 'jdt-' + aData.rowId);
        },
    });
    $('#tbl-data-scrapers').DataTable({
        aaSorting: [ [3, 'asc'] ],
        columnDefs: [
            { "visible": false, "targets": 0 }  // Hide the rowId column
        ],
        columns: [
            { data: 'rowId' },
            { data: 'uuid' },
            { data: 'name' },
            { data: 'startTime' },
            { data: 'stopTime' },
            { data: 'runtime' },
            { data: 'criticalCount' },
            { data: 'errorCount' },
            { data: 'warningCount' },
        ],
        fnRowCallback: function( nRow, aData, iDisplayIndex, iDisplayIndexFull ){
            // Add the apikey id as an id for the row
            $(nRow).attr('id', 'jdt-' + aData.rowId);
        },
    });

    var page = window.location.pathname;
    var url = window.location.origin + page;
    var socket = io.connect( url );

    if( page === '/manage/apikeys' ){
        socket_listen = 'manage-apikeys';
        $form = $('#add-apikey');
    }else if( page === '/manage/scrapers' ){
        socket_listen = 'manage-scrapers';
        $form = $('#add-scraper');
    }else if( page === '/manage/groups' ){
        socket_listen = 'manage-groups';
        $form = $('#add-group');
    }else if( page === '/data/scrapers' ){
        socket_listen = 'data-scrapers';
    }
    $('body').on( 'click', '.btn-del', function( event ){
        var id = event.target.dataset.id;
        $.getJSON(url + '/delete/' + id)
    });

    if( socket_listen !== null ){
        socket.on(socket_listen, function( data ){
                console.log("WebSocket: ", data);
                if( page === '/data/scrapers' ){
                    addToScraperList(data)
                }else{
                    addToTable(data);
                }
        })
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
});

var socket_listen = null;
var $form = null;
var cb = null;

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
                console.log("Move bitch");
                $scraperRun.appendTo($finished);
            }
        }
    });
}

function addToTable( response ){
    var table = $('#tbl-' + socket_listen).DataTable();
    var action = response.action;
    var rows = response.data;
    $.each( rows, function( i, rowData ){
        var dtRowId = table.row('[id=jdt-' + rowData.rowId + ']').index();
        if( action === 'update' || action === 'add' || action === 'increment'){
            rowData.action = '<button class="btn-del" data-id="' + rowData.rowId + '">Delete</button>'
            rowData.timeAdded = moment(rowData.timeAdded).format("YYYY-MM-DD HH:mm")
            rowData.startTime = moment(rowData.startTime).format("YYYY-MM-DD HH:mm:ss")
            rowData.stopTime = moment(rowData.stopTime).format("YYYY-MM-DD HH:mm:ss")
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
