'use strict';

_.templateSettings = {interpolate: /\{\{(.+?)\}\}/g};

var page = window.location.pathname;
var baseUrl = window.location.origin;
var url = baseUrl + page;


var _template = {
    scraperWrapper: _.template(
        '<table id={{runClass}}-{{scraperKey}} class="table">' +
            '<thead class="invisible">' +
                '<tr>' +
                    '<th class="scraper-name">Name</th>' +
                    '<th>Start Time</th>' +
                    '<th>Stop Time</th>' +
                    '<th>Runtime</th>' +
                    '<th>Log Criticals</th>' +
                    '<th>Log Errors</th>' +
                    '<th>Log Warnings</th>' +
                    '<th>URL Errors</th>' +
                '</tr>' +
            '</thead>' +
            '<tbody class="panel-heading" data-toggle="collapse" href="#collapse-{{runClass}}-{{scraperKey}}">' +
                '<tr id="{{uuid}}">' +
                    '<td class="scraper-name">{{name}}</td>' +
                    '<td>{{startTime}}</td>' +
                    '<td>{{stopTime}}</td>' +
                    '<td>{{runtime}}</td>' +
                    '<td>{{criticalCount}}</td>' +
                    '<td>{{errorCount}}</td>' +
                    '<td>{{warningCount}}</td>' +
                    '<td>{{urlErrorCount}}</td>' +
                '</tr>' +
            '</tbody>' +
            '<tbody id="collapse-{{runClass}}-{{scraperKey}}" class="collapse runs">' +
            '</tbody>' +
        '</table>'
    ),
    scraperRun: _.template(
        '<tr id="{{uuid}}">' +
            '<td class="scraper-name"></td>' +
            '<td>{{startTime}}</td>' +
            '<td>{{stopTime}}</td>' +
            '<td>{{runtime}}</td>' +
            '<td>{{criticalCount}}</td>' +
            '<td>{{errorCount}}</td>' +
            '<td>{{warningCount}}</td>' +
            '<td>{{urlErrorCount}}</td>' +
        '</tr>'
    ),
    organization: _.template(
        '<div id="{{rowId}}" class="organization">' +
            '<b><span class="name">{{name}}</span> | ' +
            '<b><span class="owner">{{owner}}</span> | ' +
            '<b><span class="is_owner">{{isOwner}}</span> | ' +
            '<button class="btn-del" data-id="{{rowId}}">Delete</button>' +
        '</div>'
    ),
    // Manage tables
    manageScrapersRow: _.template(
        '<tr id="{{rowId}}">' +
            '<td class="scraper-group">{{organization}}.{{group}}</td>' +
            '<td class="scraper-name">{{name}}</td>' +
            '<td class="scraper-owner">{{owner}}</td>' +
            '<td class="scraper-key">{{key}}</td>' +
            '<td class="scraper-date">{{timeAdded}}</td>' +
            '<td class="scraper-actions">{{actions}}</td>' +
        '</tr>'
    ),
    manageGroupsRow: _.template(
        '<tr id="{{rowId}}" class="manageGroupsRow">' +
            '<td class="group-organization">{{organization}}</td>' +
            '<td class="group-name">{{name}}</td>' +
            '<td class="group-actions">{{actions}}</td>' +
        '</tr>'
    ),
    manageApikeysRow: _.template(
        '<tr id="{{rowId}}">' +
            '<td class="apikey-organization">{{organization}}</td>' +
            '<td class="apikey-name">{{name}}</td>' +
            '<td class="apikey-key">{{key}}</td>' +
            '<td class="apikey-date">{{timeAdded}}</td>' +
            '<td class="apikey-actions">{{actions}}</td>' +
        '</tr>'
    ),
    dataScraperRow: _.template(
        '<tr id="{{status}}-{{scraperKey}}">' +
            '<td class="scraper-organization">{{organization}}</td>' +
            '<td class="scraper-name"><a href="{{scraperKey}}">{{name}}</a></td>' +
            '<td class="scraper-startTime">{{startTime}}</td>' +
            '<td class="scraper-stopTime">{{stopTime}}</td>' +
            '<td class="scraper-runtime">{{runtime}}</td>' +
            '<td class="scraper-criticalCount">{{criticalCount}}</td>' +
            '<td class="scraper-errorCount">{{errorCount}}</td>' +
            '<td class="scraper-warningCount">{{warningCount}}</td>' +
            '<td class="scraper-urlErrorCount">{{urlErrorCount}}</td>' +
        '</tr>'
    ),
    dataScraperRunRow: _.template(
        '<tr id="{{rowId}}">' +
            '<td class="scraper-uuid"><a href="#">{{uuid}}</a></td>' +
            '<td class="scraper-startTime">{{startTime}}</td>' +
            '<td class="scraper-stopTime">{{stopTime}}</td>' +
            '<td class="scraper-runtime">{{runtime}}</td>' +
            '<td class="scraper-criticalCount">{{criticalCount}}</td>' +
            '<td class="scraper-errorCount">{{errorCount}}</td>' +
            '<td class="scraper-warningCount">{{warningCount}}</td>' +
            '<td class="scraper-urlErrorCount">{{urlErrorCount}}</td>' +
        '</tr>'
    ),
    dataScraperLogRow: _.template(
        '<tr id="{{rowId}}">' +
            '<td class="scraper-time_collected">{{time_collected}}</td>' +
            '<td class="scraper-filename">{{filename}}</td>' +
            '<td class="scraper-module">{{module}}</td>' +
            '<td class="scraper-func_name">{{func_name}}</td>' +
            '<td class="scraper-line_no">{{line_no}}</td>' +
            '<td class="scraper-level_name">{{level_name}}</td>' +
            '<td class="scraper-thread_name">{{thread_name}}</td>' +
            '<td class="scraper-message" title="{{message}}"><div class="hover-data">{{message}}</div></td>' +
            '<td class="scraper-exc_text" title="{{exc_text}}"><div class="hover-data">{{exc_text}}</div></td>' +
        '</tr>'
    ),

    deleteBtn: _.template('<button class="btn-del" data-id="{{rowId}}">Delete</button>'),
    alert: _.template('<div class="alert alert-{{type}}" id="{{uid}}">' +
                        '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>' +
                        '<strong>{{title}}</strong> {{message}}' +
                      '</div>'),
}

var _utils = {
    formatTime: function( time ){
        if( time === null ) return '';

        return moment(time).format("YYYY-MM-DD HH:mm")
    },
    formatTimestamp: function( time ){
        if( time === null ) return '';

        return moment(time).format("YYYY-MM-DD HH:mm:ss")
    },
    formatRuntime: function( seconds ){
        function pad(num) {
            return ("0" + num).slice(-2);
        }
        var minutes = Math.floor(seconds / 60);
        seconds = seconds % 60;
        var hours = Math.floor(minutes / 60);
        minutes = minutes % 60;
        return pad(hours) + ":" + pad(minutes) + ":" + pad(seconds);
    },
    generateId: function(){
      // Math.random should be unique because of its seeding algorithm.
      // Convert it to base 36 (numbers + letters), and grab the first 9 characters after the decimal.
      return '_' + Math.random().toString(36).substr(2, 9);
    }
};

$(function(){
    $(document).tooltip();
    initPage();

    // Opens/selects correct menu item
    setActiveMenuItem();

    $('body').on( 'click', '.btn-del', function( event ){
        var id = event.target.dataset.id;
        $.getJSON(url + '/delete/' + id, function( data ){
            console.log("Delete Action response: ", data);
            displayAlert("", data.message, data.status);
        });
    });

    $('body').on( 'click', '#tbl-data-scraper-runs tr', function( event ){
        var runUuid = event.currentTarget.id;
        $.getJSON('/data/api/scraper/logs/' + runUuid, function( data ){
            console.log("Run Logs response: ", data);
            addToScraperLogsTable(data);
        });
    });

    // When adding a new scraper, this will dynamically populate what users can be owners
    $('body').on( 'change', '#scraper-group', function( event ){
        var id = $('#scraper-group').val();
        populateUserDropdown(id);
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

    }else if( page === '/data/scrapers/dev' || page === '/data/scrapers/prod' ){
        socketListen = 'data-scrapers';
    }else{
        var path = page.split('/');
        if( path[1] === 'data' && path[2] === 'scrapers' ){
            populateScraperRuns(path[4], path[3]);
        }
    }

    if( socketListen !== null ){
        socket.on(socketListen, function( data ){
            console.log("WebSocket: ", data);
            if( page === '/data/scrapers/dev' || page === '/data/scrapers/prod' ){
                addToScraperTable(data);
            }else if( page === '/manage/organizations' ){
                addOrganizations(data);
            }else{
                addToManageTable(data, socketListen);
            }
        });
    }
}

function displayAlert( title, message, type ){
    var uid = _utils.generateId();  // Create a unique id for the alert element
    if (type == 'error'){
        type = 'danger';
    }

    var alertData = {'title': title,
                     'message': message,
                     'type': type,
                     'uid': uid
                     };
    // Display on page
    $('#alert-container').append(_template.alert(alertData));
    // Auto clear alert
    $('#'+uid).fadeTo(3000, 500)
              .slideUp(500, function(){
                  $('#'+uid).alert('close');
              });
}

function populateUserDropdown( organizationGroupId ){
    var $options = $('#scraper-owner');

    $options.empty(); // Remove current options
    // Always have None as an option
    $options.append($('<option value="">None</option>'));

    // Get the other users that can be assigned as owner
    $.getJSON(baseUrl + '/manage/api/userlist/' + organizationGroupId, function( data ){

        $.each( data.userList, function( i, user ){
            var is_selected = '';
            if( user.selected === true ){
                is_selected = 'selected="selected"';
            }
            $options.append($('<option value="' + user.id + '" ' + is_selected + '>' +
                                user.username + '</option>'));
        });

        $options.css('box-shadow', '0px 0px 20px 0px blue');
        setTimeout(function(){ $options.css('box-shadow', ''); }, 1500);
        $options.trigger("chosen:updated");
    });
}

function populateScraperRuns(scraperKey, env){
    $.getJSON(baseUrl + '/data/api/scraper/' + scraperKey + '/' + env, function( data ){
        $('#scraper-name').html(data.data[0].organization + '.' + data.data[0].name);
        addToScraperRunTable(data);
    });
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
            displayAlert("", data.message, data.status);
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

function addScraper( response ){
    var action = response.action;
    var data = response.data;
    // var $running = $('#running');
    // var $finished = $('#finished');

    $.each( data, function( i, scraper ){
        var tableName = 'tbl-data-finished-scrapers';
        if( typeof scraper.runtime === 'undefined' ){
            tableName = 'tbl-data-running-scrapers';
        }

        addToScraperTable(scraper, tableName);
    });

}

function moveScraperFinished( $scraperRun, scraper ){
    var $finished = $('#finished');
    var scraperParentIdent = '#finished-' + scraper.scraperKey;

    if( $(scraperParentIdent).length === 0 ){
        scraper.runClass = 'finished';
        $finished.append(_template.scraperParent(scraper));
    }

    var $scraperParent = $(scraperParentIdent).find('.runs');
    // Add scraper run to parent in $finished
    $scraperParent.prepend($scraperRun);
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

function addToManageTable( response, tableName ){
    var $table = $('#tbl-' + tableName);
    var action = response.action;
    var rows = response.data;

    $.each( rows, function( i, rowData ){
        var $row = $('#' + rowData.rowId);

        if( action === 'update' || action === 'add' || action === 'increment'){
            rowData.timeAdded = _utils.formatTime(rowData.timeAdded)
            rowData.actions = _template.deleteBtn(rowData);

            if( $row.length ){
                // Update the row
                console.log("Update scraper: " + rowData.rowId);
            }else{
                // Add the row to the table
                var newRow = null;
                if( page === '/manage/apikeys' ){
                    newRow = _template.manageApikeysRow(rowData);
                }else if( page === '/manage/scrapers' ){
                    newRow = _template.manageScrapersRow(rowData);
                }else if( page === '/manage/groups' ){
                    newRow = _template.manageGroupsRow(rowData);
                }else if( page === '/manage/organizations' ){
                    newRow = _template.manageOrganizationsRow(rowData);
                }else if( page === '/data/scrapers/dev' || page === '/data/scrapers/prod' ){
                    newRow = _template.dataScraperRow(rowData);
                }
                $table.append(newRow);
            }

        }else if( action === 'delete' ){
            $row.remove();
        }
    });
    // $table.find('a').editable({url: '/manage/api/stuff'});
    // $('#tbl-' + tableName + ' a').editable();
    $table.trigger("update");
}

function addToScraperTable( response ){
    var action = response.action;
    var rows = response.data;

    $.each( rows, function( i, scraper ){
        scraper.status = 'running';
        if( scraper.stopTime != null ){
            scraper.status = 'finished';
        }

        var $table = $('#tbl-data-' + scraper.status + '-scrapers');
        var $row = $('#' + scraper.status + '-' + scraper.scraperKey);

        if( typeof scraper.runtime === 'undefined' ){
            scraper.runtime = '';
        }

        if( action === 'add' || action === 'start' || action === 'stop'){
            scraper.startTime = _utils.formatTime(scraper.startTime)
            scraper.stopTime = _utils.formatTime(scraper.stopTime)
            scraper.runtime = _utils.formatRuntime(scraper.runtime)

            if( action === 'stop' ){
                var $oldRow = $('#running-' + scraper.scraperKey);
                $oldRow.remove();
            }

            if( !$row.length ){
                // Add the row
                var newRow = _template.dataScraperRow(scraper);
                $table.append(newRow);
            }else{
                // Update the row
                $.each( scraper, function( field, value ){
                    $row.find('.scraper-' + field).html(value);
                });
            }
        }
        if( action === 'increment' || action === 'update' ){
            $.each( scraper, function( field, value ){
                var fieldsToIncrement = ['criticalCount', 'errorCount', 'warningCount', 'urlErrorCount']
                var $field = $row.find('.scraper-' + field);

                if( fieldsToIncrement.indexOf(field) != -1){
                    // Get the current value and add to it
                    value = parseInt($field.text()) + value;
                }

                $field.html(value);
            });

        }else if( action === 'stop' ){
            console.log("stoppiong scraper")
        }else if( action === 'delete' ){
            $row.remove();
        }
    });

    // Update all tables on page
    $('#tbl-data-running-scrapers').trigger("update");
    $('#tbl-data-finished-scrapers').trigger("update");
}


function addToScraperRunTable( response ){
    var rows = response.data;

    $.each( rows, function( i, run ){
        run.status = 'running';
        if( run.stopTime != null ){
            run.status = 'finished';
        }

        var $table = $('#tbl-data-scraper-runs');
        var $row = $('#scraper-run-' + run.rowId);

        if( typeof run.runtime === 'undefined' ){
            run.runtime = '';
        }

        run.startTime = _utils.formatTime(run.startTime)
        run.stopTime = _utils.formatTime(run.stopTime)

        run.runtime = _utils.formatRuntime(run.runtime)

        if( !$row.length ){
            // Add the row
            var newRow = _template.dataScraperRunRow(run);
            $table.append(newRow);
        }else{
            // Update the row
            $.each( run, function( field, value ){
                $row.find('.scraper-run-' + field).html(value);
            });
        }
    });

    // Update all tables on page
    $('#tbl-data-scraper-runs').trigger("update");
}

function addToScraperLogsTable( response ){
    var $table = $('#tbl-data-scraper-logs');
    $.tablesorter.clearTableBody( $table );
    var rows = response.data;

    $.each( rows, function( i, log ){
        var $row = $('#scraper-log-' + log.rowId);

        log.time_collected = _utils.formatTimestamp(log.time_collected)

        if( !$row.length ){
            // Add the row
            var newRow = _template.dataScraperLogRow(log);
            $table.append(newRow);
        }else{
            // Update the row
            $.each( log, function( field, value ){
                $row.find('.scraper-log-' + field).html(value);
            });
        }
    });

    // Update all tables on page
    $table.trigger("update");
}
