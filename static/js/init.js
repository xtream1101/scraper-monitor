$(function(){
    $('.table-list').dataTable();
    $('.scraper-list').dataTable({
        "aaSorting": [ [0, 'asc'], [1, 'asc'] ]
    });
});
