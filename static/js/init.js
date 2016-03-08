$(document).ready(function(){
    $('#tbl-apikeys').DataTable({
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
    $('#tbl-scrapers').DataTable({
        aaSorting: [ [0, 'asc'], [1, 'asc'] ],
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
    $('#tbl-groups').DataTable({
        aaSorting: [ [0, 'asc']],
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

    var page = window.location.pathname;

    var url = window.location.origin + page;
    var socket = io.connect( url );

    
    if( page === '/apikeys' ){
        socket_listen = 'apikeys';
        $form = $('#add-apikey');
    }else if( page === '/scrapers' ){
        socket_listen = 'scrapers';
        $form = $('#add-scraper');
    }else if( page === '/groups' ){
        socket_listen = 'groups';
        $form = $('#add-group');
    }
    $('body').on( 'click', '.btn-del', function( event ){
        var id = event.target.dataset.id;
        $.getJSON(url + '/delete/' + id)
    });

    if( socket_listen !== null && $form !== null ){

        socket.on(socket_listen, function( data ){
                console.log("WebSocket: ", data);
                addToTable(data);
        });
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
