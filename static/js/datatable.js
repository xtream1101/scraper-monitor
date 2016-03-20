$(function(){
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
});
