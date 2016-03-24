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
    organization: _.template(
        '<div id="{{rowId}}" class="organization">' +
            '<b><span class="name">{{name}}</span> | ' +
            '<b><span class="owner">{{owner}}</span> | ' +
            '<b><span class="is_owner">{{isOwner}}</span> | ' +
            '<button class="btn-del" data-id="{{rowId}}">Delete</button>' +
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
        $.getJSON(url + '/delete/' + id, function( data ){
            console.log("Delete Action response: ", data);
        });
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
        $('#add-apikey').on( "submit", submitForm);
    }else if( page === '/manage/scrapers' ){
        socketListen = 'manage-scrapers';
        $('#add-scraper').on( "submit", submitForm);
    }else if( page === '/manage/groups' ){
        socketListen = 'manage-groups';
        $('#add-group').on( "submit", submitForm);
    }else if( page === '/manage/organizations' ){
        socketListen = 'manage-organizations';
        $('#add-organization').on( "submit", submitForm);
        $('#add-organization-user').on( "submit", submitForm);
    }else if( page === '/data/scrapers' ){
        socketListen = 'data-scrapers';
    }

    if( socketListen !== null ){
        socket.on(socketListen, function( data ){
            console.log("WebSocket: ", data);
            if( page === '/data/scrapers' ){
                addScraperRunning(data)
            }else if( page === '/manage/organizations' ){
                addOrganizations(data)
            }else{
                addToTable(data, socketListen);
            }
        });
    }
}

function submitForm( event ){
    event.preventDefault();
    var $form = $(event.currentTarget);
    var datastring = $form.serialize();
    $.ajax({
        type: "POST",
        url: $form.context.action,
        data: datastring,
        success: function( data ){
            $form.trigger("reset");
            console.log("Action response: ", data);
        }
    });
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
                    // Get the current value and add to it
                    var currVal = parseInt($field.text());
                    value = currVal + value;
                }
                $field.html(value);
            });

            // Check if stopTime exists, if so move out of $running
            if( typeof scraper.stopTime !== 'undefined'){
                if( $scraperRun.siblings().length === 0 ){
                    // Remove scraper parent since the last one just finished
                    $scraperRun.parent().parent().remove();
                }
                addScraperFinished($scraperRun, scraper);
            }
        }
    });
}

function addOrganizations( response ){
    var action = response.action;
    var data = response.data;
    var $owner = $('#owner');
    var $member = $('#member');

    $.each( data, function( i, organization ){
        if( action === 'add' ){
            if( $member.find('#'+organization.rowId).length === 0 ){
                $member.append(_template.organization(organization));
            }
        }else if( action === 'delete' ){
            $member.find('#'+organization.rowId).remove();
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
