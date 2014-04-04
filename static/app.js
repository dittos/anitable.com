var items = $('.item');
var favPanel = $('.panel-fav');

items.on('stateChange', function() {
    var $el = $(this);
    var fav = $el.is('.state-fav');
    var favButton = $el.find('.btn-fav');
    var icon = favButton.find('.fa');
    var checkbox = favButton.find('input:checkbox');
    var activeRequest = $el.data('activeRequest');
    if (activeRequest)
        activeRequest = activeRequest.state() == 'pending';

    favButton.toggleClass('active', fav)
        .toggleClass('loading', Boolean(activeRequest));
    icon.removeClass().addClass('fa')
        .addClass(activeRequest ? 'fa-spinner fa-spin' : 'fa-check');
    checkbox.prop('checked', fav);
});

if ($('body').is('.logged-in')) {
    function requestFavStateUpdate(id, state) {
        var url = state ? '/fav' : '/fav/remove';
        return $.post(url, {id: id});
    }

    items.each(function() {
        var $el = $(this);
        var id = $el.data('id');
        var fav = $.inArray(id, AppState.favIds) != -1;
        $el.toggleClass('state-fav', fav).trigger('stateChange');
    });

    items.on('change', 'input:checkbox', function(event) {
        var $el = $(event.delegateTarget);
        var req = $el.data('activeRequest');
        // Allow only one request
        if (req && req.state() == 'pending')
            return;

        var id = $el.data('id');
        var fav = !$el.is('.state-fav');
        req = requestFavStateUpdate(id, fav);
        $el.toggleClass('state-fav', fav).trigger('stateChange');
        req.then(function() {
            $el.trigger('stateChange');
            // TODO: alert to user
        }, function() {
            // Rollback on failure
            $el.toggleClass('state-fav', !fav).trigger('stateChange');
            // TODO: alert to user
        });
        $el.data('activeRequest', req).trigger('stateChange');
    });
} else {
    items.on('change', 'input:checkbox', function(event) {
        $(event.delegateTarget)
            .toggleClass('state-fav', this.checked)
            .trigger('stateChange');
    });

    items.on('stateChange', function() {
        favPanel.trigger('favCountChange');
    });

    favPanel.on('favCountChange', function() {
        var count = items.filter('.state-fav').length;
        favPanel.find('.count').text(count);
        favPanel.toggleClass('hidden', count == 0);
    });

    favPanel.find('.btn-save')
        .prop('disabled', false) // reset button state on load
        .on('click', function() {
            $(this).prop('disabled', true)
                .text('로그인 중...');
        });
}
