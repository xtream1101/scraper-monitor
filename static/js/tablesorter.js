$(function(){
    // Generic default table
    var $table = $('.simple-table').tablesorter({
        widgets: ["filter"],
        widgetOptions : {
            // filter_anyMatch replaced! Instead use the filter_external option
            // Set to use a jQuery selector (or jQuery object) pointing to the
            // external filter (column specific or any match)
            filter_external : '.search',
            // add a default type search to the first name column
            filter_defaultFilter: { 1 : '~{query}' },
            filter_columnFilters: false,
            filter_placeholder: { search : 'Search...' },
            filter_saveFilters : true,
            filter_reset: '.reset'
        }
    });
    $('body').on('click', 'button[data-column]', function(){
        var $this = $(this),
            totalColumns = $table[0].config.columns,
            col = $this.data('column'), // zero-based index or "all"
            filter = [];

        // text to add to filter
        filter[ col === 'all' ? totalColumns : col ] = $this.text();
        $table.trigger('search', [ filter ]);
        return false;
    });

    // Custom table sorters
    var $logsTable = $('#tbl-data-scraper-logs').tablesorter({
        widgets: ["filter"],
        widgetOptions : {
            // filter_anyMatch replaced! Instead use the filter_external option
            // Set to use a jQuery selector (or jQuery object) pointing to the
            // external filter (column specific or any match)
            filter_external : '.log-search',
            // add a default type search to the first name column
            filter_defaultFilter: { 1 : '~{query}' },
            filter_columnFilters: true,
            filter_placeholder: { search : 'Search...' },
            filter_saveFilters : true,
            filter_reset: '.log-reset'
        }
    });

});
