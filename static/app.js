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

    function showToast(message, duration) {
        favPanel.removeClass('hidden');
        favPanel.find('.panel-fav-inner').text(message);
        var timerId = favPanel.data('hideTimerId');
        if (timerId)
            window.clearTimeout(timerId);
        timerId = window.setTimeout(function() {
            favPanel.data('hideTimerId', null)
                .addClass('hidden');
        }, duration);
        favPanel.data('hideTimerId', timerId);
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
            showToast(fav ? '관심 체크!' : '관심 체크 해제', 1000);
        }, function() {
            // Rollback on failure
            $el.toggleClass('state-fav', !fav).trigger('stateChange');
            showToast('오류 발생! 잠시 후에 다시 시도해주세요.', 5000);
        });
        $el.data('activeRequest', req).trigger('stateChange');
    });

    function updateSettings(key, value) {
        AppState.settings[key] = value;
    }

    $('.only-fav').on('stateChange', function() {
        $(this).find('a').removeClass('active');
        var state = Boolean(AppState.settings.onlyFav);
        $(this).find(state ? '.on' : '.off').addClass('active');
        items.toggleClass('show-if-fav', state);
        window.scrollTo(0, 0);
        window.blazy && window.blazy.revalidate();
    }).on('click', '.on', function(event) {
        updateSettings('onlyFav', true);
        $(event.delegateTarget).trigger('stateChange');
        return false;
    }).on('click', '.off', function(event) {
        updateSettings('onlyFav', false);
        $(event.delegateTarget).trigger('stateChange');
        return false;
    }).trigger('stateChange');

    $(function() {
        $.each(AppState.flashes, function(i, message) {
            showToast(message, 5000);
        });
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

    // reset button state on load
    var saveButton = favPanel.find('.btn-save');
    saveButton.prop('disabled', false);
    $('.save-form').submit(function() {
        saveButton.prop('disabled', true)
            .text('로그인 중...');
    });

    // reconcile checkbox state on load
    items.each(function() {
        var $el = $(this);
        var state = $el.find('input:checkbox').prop('checked');
        $el.toggleClass('state-fav', state).trigger('stateChange');
    });
}
