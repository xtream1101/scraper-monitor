$(document).ready(function(){
    $('#tbl-manage-apikeys').DataTable({
        aaSorting: [ [1, 'asc']],
        columnDefs: [
            { "visible": false, "targets": 0 }  // Hide the id column
        ],
        columns: [
            { data: 'id' },
            { data: 'name' },
            { data: 'key' },
            { data: 'host' },
            { data: 'time_added' },
            { data: 'action' },
        ],
        fnRowCallback: function( nRow, aData, iDisplayIndex, iDisplayIndexFull ){
            // Add the apikey id as an id for the row
            $(nRow).attr('id', 'jdt-' + aData.id);
        },
    });
    $('#tbl-manage-scrapers').DataTable({
        aaSorting: [ [1, 'asc'], [2, 'asc'] ],
        columnDefs: [
            { "visible": false, "targets": 0 }  // Hide the id column
        ],
        columns: [
            { data: 'id' },
            { data: 'group' },
            { data: 'name' },
            { data: 'owner' },
            { data: 'key' },
            { data: 'time_added' },
            { data: 'action' },
        ],
        fnRowCallback: function( nRow, aData, iDisplayIndex, iDisplayIndexFull ){
            // Add the apikey id as an id for the row
            $(nRow).attr('id', 'jdt-' + aData.id);
        },
    });
    $('#tbl-manage-groups').DataTable({
        aaSorting: [ [1, 'asc']],
        columnDefs: [
            { "visible": false, "targets": 0 }  // Hide the id column
        ],
        columns: [
            { data: 'id' },
            { data: 'name' },
            { data: 'action' },
        ],
        fnRowCallback: function( nRow, aData, iDisplayIndex, iDisplayIndexFull ){
            // Add the apikey id as an id for the row
            $(nRow).attr('id', 'jdt-' + aData.id);
        },
    });
    $('#tbl-data-scrapers').DataTable({
        aaSorting: [ [1, 'asc'], [2, 'asc'] ],
        columnDefs: [
            { "visible": false, "targets": 0 }  // Hide the id column
        ],
        columns: [
            { data: 'id' },
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
            $(nRow).attr('id', 'jdt-' + aData.id);
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
                addToTable(data);
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

function addToTable( response ){
    var table = $('#tbl-' + socket_listen).DataTable();
    var action = response.action;
    var rows = response.data;
    $.each( rows, function( i, rowData ){
        var rowId = table.row('[id=jdt-' + rowData.id + ']').index();
        if( action === 'update' || action === 'add'){
            rowData.action = '<button class="btn-del" data-id="' + rowData.id + '">Delete</button>'
            rowData.time_added = moment(rowData.time_added).format("YYYY-MM-DD HH:mm")
            rowData.startTime = moment(rowData.startTime).format("YYYY-MM-DD HH:mm:ss")
            rowData.stopTime = moment(rowData.stopTime).format("YYYY-MM-DD HH:mm:ss")
            if( rowId >= 0 ){
                table.row(rowId).data(rowData).draw();
            }else{
                table.row.add(rowData).draw();
            }
        }else if( action === 'delete' ){
            if( rowId >= 0 ){
                table.row(rowId).remove().draw();
            }
        }
    });
}
