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

});
