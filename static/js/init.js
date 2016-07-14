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
};

$(function(){
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
    }

    if( socketListen !== null ){
        socket.on(socketListen, function( data ){
            console.log("WebSocket: ", data);
            if( page === '/data/scrapers/dev' || page === '/data/scrapers/prod' ){
                addScraper(data);
            }else if( page === '/manage/organizations' ){
                addOrganizations(data);
            }else{
                addToTable(data, socketListen);
            }
        });
    }
}

function displayAlert( title, message, type ){
    var uid = ID();  // Create a unique id for the alert element
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

        $.each( data.user_list, function( i, user ){
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
    var $running = $('#running');
    var $finished = $('#finished');

    $.each( data, function( i, scraper ){
        if( typeof scraper.runtime === 'undefined' ){
            scraper.runtime = null;
        }
        if( action === 'add' ){
            scraper.startTime = _utils.formatTime(scraper.startTime)
            if( scraper.stopTime !== null ){
                scraper.stopTime = _utils.formatTime(scraper.stopTime)
                // Check if scraper is not in finished
                var scraperParentIdent = '#finished-' + scraper.scraperKey;
                if( $(scraperParentIdent).length === 0 ){
                    scraper.runClass = 'finished';
                    $finished.append(_template.scraperWrapper(scraper))
                }else{
                    var $scraperParent = $(scraperParentIdent).find('.runs');
                    // Add scraper run to parent in $running
                    $scraperParent.append(_template.scraperRun(scraper));
                }
            }else{
                // Not in running list so add it
                // Check if scraper run has a scraper parent in $running
                var scraperParentIdent = '#running-' + scraper.scraperKey;
                if( $(scraperParentIdent).length === 0 ){
                    scraper.runClass = 'running';
                    $running.append(_template.scraperWrapper(scraper));
                }else{
                    var $scraperParent = $(scraperParentIdent).find('.runs');
                    // Add scraper run to parent in $running
                    $scraperParent.append(_template.scraperRun(scraper));
                }
            }
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
            if( typeof scraper.stopTime !== 'undefined' ){
                if( $scraperRun.siblings().length === 0 ){
                    // Remove scraper parent since the last one just finished
                    $scraperRun.parent().parent().remove();
                }
                moveScraperFinished($scraperRun, scraper);
            }
        }
    });

    // Display the headers for the first table in the list
    $('#running').find('thead').first().removeClass('invisible');
    $('#finished').find('thead').first().removeClass('invisible');
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

function addToTable( response, tableName ){
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

var ID = function(){
  // Math.random should be unique because of its seeding algorithm.
  // Convert it to base 36 (numbers + letters), and grab the first 9 characters after the decimal.
  return '_' + Math.random().toString(36).substr(2, 9);
}
