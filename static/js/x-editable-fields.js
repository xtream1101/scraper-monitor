$(function(){
    //
    // DEFAULTS
    //
    $.fn.editable.defaults.mode = 'inline';  // Toggle `popup` / `inline` mode
    $.fn.editable.defaults.success = function( response, newValue ){
        // Return error message if success is false
        if( !response.success ) return response.message;
    };
    $.fn.editable.defaults.error = function( response, newValue ){
        if( response.status === 500 ){
            return 'Service unavailable. Please try later.';
        }else{
            return response.message;
        }
    };

    //
    // Manage Groups
    //
    $('body').on( 'dblclick', '#tbl-manage-groups .group-name', function( event ){
        var $target = $(event.currentTarget);

        $target.editable({
            type: 'text',
            validate: function( value ){
                if($.trim(value) === '') return 'Cannot be empty';
            },
            name: 'name',
            pk: function(){
                // Get the id of the row
                return $target.parent()[0].id;
            },
            url: '/manage/groups/edit'
        })
        .on('hidden', function( e, reason ){
            $target.editable('destroy');
        });
        // Now that the element is editable, click to go into edit mode
        $target.click();
    });

    //
    // Manage Apikeys
    //
    $('body').on( 'dblclick', '#tbl-manage-apikeys .apikey-name', function( event ){
        var $target = $(event.currentTarget);

        $target.editable({
            type: 'text',
            validate: function( value ){
                if($.trim(value) === '') return 'Cannot be empty';
            },
            name: 'name',
            pk: function(){
                // Get the id of the row
                return $target.parent()[0].id;
            },
            url: '/manage/apikeys/edit'
        })
        .on('hidden', function( e, reason ){
            $target.editable('destroy');
        });
        // Now that the element is editable, click to go into edit mode
        $target.click();
    });

    //
    // Manage Scrapers
    //
    $('body').on( 'dblclick', '#tbl-manage-scrapers .scraper-name', function( event ){
        var $target = $(event.currentTarget);
        var scraper_id = $target.parent()[0].id;

        $target.editable({
            type: 'text',
            validate: function( value ){
                if($.trim(value) === '') return 'Cannot be empty';
            },
            name: 'name',
            pk: scraper_id,
            url: '/manage/scrapers/edit'
        })
        .on('hidden', function( e, reason ){
            $target.editable('destroy');
        });
        // Now that the element is editable, click to go into edit mode
        $target.click();
    });

    $('body').on( 'dblclick', '#tbl-manage-scrapers .scraper-group', function( event ){
        var $target = $(event.currentTarget);
        var scraper_id = $target.parent()[0].id;

        // Get the list of group options
        $.getJSON(baseUrl + '/manage/api/edit_field/grouplist/?scraper_id=' + scraper_id, function( data ){
            var groupList = [];
            $.each( data.groupList, function( i, group ){
                groupList.push({value: group.id, text: group.name});
            });

            $target.editable({
                type: 'select',
                validate: function( value ){
                    if($.trim(value) === '') return 'Cannot be empty';
                },
                name: 'group',
                value: data.currentGroupId,
                source: groupList,
                pk: scraper_id,
                url: '/manage/scrapers/edit'
            })
            .on('hidden', function( e, reason ){
                $target.editable('destroy');
            });
            // Now that the element is editable, click to go into edit mode
            $target.click();
        });
    });

    $('body').on( 'dblclick', '#tbl-manage-scrapers .scraper-owner', function( event ){
        var $target = $(event.currentTarget);
        var scraper_id = $target.parent()[0].id;

        // Get the list of user options
        $.getJSON(baseUrl + '/manage/api/edit_field/userlist/?scraper_id=' + scraper_id, function( data ){
            var userList = [''];
            $.each( data.userList, function( i, user ){
                userList.push({value: user.id, text: user.name});
            });

            $target.editable({
                type: 'select',
                validate: function( value ){
                },
                name: 'owner',
                value: data.currentUserId,
                source: userList,
                pk: scraper_id,
                url: '/manage/scrapers/edit'
            })
            .on('hidden', function( e, reason ){
                $target.editable('destroy');
            });
            // Now that the element is editable, click to go into edit mode
            $target.click();
        });
    });

   

});
