'use strict';

_.templateSettings = {interpolate: /\{\{(.+?)\}\}/g};

var page = window.location.pathname;
var url = window.location.origin + page;

var _template = {
    scraperRun: _.template(
        '<div id="run-{{rowId}}" class="scraper-run">' +
            '<span class="uuid"><span class="value">{{uuid}}</span></span>  | ' +
            '<span class="startTime"><span class="value">{{startTime}}</span></span>  | ' +
            '<span class="stopTime"><span class="value">{{stopTime}}</span></span>  | ' +
            '<span class="runtime"><span class="value">{{runtime}}</span></span>  | ' +
            '<span class="criticalCount"><span class="value">{{criticalCount}}</span></span>  | ' +
            '<span class="errorCount"><span class="value">{{errorCount}}</span></span>  | ' +
            '<span class="warningCount"><span class="value">{{warningCount}}</span></span>' +
        '</div>'
    ),
    scraperParent: _.template(
        '<div id="{{scraperKey}}" class="scraper-parent {{runClass}}">' +
            '<b><span class="name">Scraper: <span class="value">{{name}}</span></span> | ' +
            '<span class="key">Key: <span class="value">{{scraperKey}}</span></span></b><br />' +
            '<div class="runs"></div>' +
            
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
                addScraperRunning(data)
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

function addScraperRunning( response ){
    var action = response.action;
    var data = response.data;
    var $running = $('#running');
    

    $.each( data, function( i, scraper ){
        if( action === 'add' ){
            // Not in running list so add it
            // Check if scraper run has a scraper parent in $running
            var scraperParentIdent = '#' + scraper.scraperKey + '.running';
            if( $(scraperParentIdent).length === 0 ){
                scraper.runClass = 'running';
                $running.append(_template.scraperParent(scraper));
            }
            var $scraperParent = $(scraperParentIdent).find('.runs');
            // Add scraper run to parent in $running
            $scraperParent.append(_template.scraperRun(scraper));

        }else if( action === 'update' || action === 'increment' ){
            var $scraperRun = $running.find('#run-' + scraper.rowId);
            // Update the values
            $.each( scraper, function( field, value ){
                var $field = $scraperRun.find('.' + field).find('.value');
                if( action === 'increment' ){
                    var currVal = parseInt($field.text());
                    value = currVal + value;
                }
                $field.html(value);
            });

            // Check if stopTime exists, if so move out of $running
            if( typeof scraper.stopTime !== 'undefined'){
                if( $scraperRun.siblings().length === 0 ){
                    console.log("Remove scraper parent")
                    // scraper parent is empty in $running
                }
                addScraperFinished($scraperRun, scraper);

            }
        }
    });
}

function addScraperFinished( $scraperRun, scraper ){
    var $finished = $('#finished');
    var scraperParentIdent = '#' + scraper.scraperKey + '.finished';
    if( $(scraperParentIdent).length === 0 ){
        scraper.runClass = 'finished';
        $finished.append(_template.scraperParent(scraper));
    }
    var $scraperParent = $(scraperParentIdent).find('.runs');
    // Add scraper run to parent in $finished
    $scraperParent.append($scraperRun);
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
