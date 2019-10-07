$(function () {

    var flash = null;
    var hover_time = null;
    var default_error_message = 'Server error, please try again later.';

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrf_token);
            }
        }
    });

    $(document).ajaxError(function (event, request, settings) {
        var message= null;
        if (request.responseJSON && request.responseJSON.hasOwnProperty('message')) {
            message = request.responseJSON.message;
        } else if (request.responseText) {
            var IS_JSON = true;
            try {
                var data = JSON.parse(request.responseText);
            }
            catch (err) {
                IS_JSON = false;
            }
            if (IS_JSON && data !== undefined && data.hasOwnProperty('message')) {
                message = JSON.parse(request.responseText).message;
            } else {
                message = default_error_message;
            }
        } else {
            message = default_error_message;
        }
        toast(message, 'error');
    });

    function toast(body, category) {
        clearTimeout(flash);
        var $toast = $('#toast');
        if (category === 'error') {
            $toast.css('background-color', 'red');
        } else {
            $toast.css('background-color', '#333');
        }
        $toast.text(body).fadeIn();
        flash = setTimeout(function() {
            $toast.fadeOut();
        }, 3000);
    }

    function show_profile_popover(e) {
        var $el = $(e.target);

        hover_timer = setTimeout(function() {
            hover_timer = null;
            $.ajax({
                type: 'GET',
                url: $el.data('href'),
                success: function(data) {
                    $el.popover({
                    html: true,
                    content: data,
                    trigger: 'manual',
                    animation: false
                    });
                    $el.popover('show');
                    $('.popover').on('mouseleave', function() {
                        setTimeout(function() {
                            $el.popover('hide');
                        }, 200);
                    });
                },
                error: function(error) {
                    toast('Server error, please try again later.');
                }
            });
        }, 500);
    }

    function hide_profile_over(e) {
        var $el = $(e.target);

        if (hover_timer) {
            clearTimeout(hover_timer);
            hover_timer = null;
        } else {
            setTimeout(function() {
                if (!$('.popover:hover').length) {
                    $el.popover('hide');
                };
            }, 200);
        }
    }

    function update_followers_count(id) {
        var $el = $('#followers-count-' + id);
        $.ajax({
            type: 'GET',
            url: $el.data('href'),
            success: function (data) {
                $el.text(data.count);
            }
        });
    }

    function follow(e) {
        var $el = $(e.target);
        var id = $el.data('id');

        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.prev().show();
                $el.hide();
                update_followers_count(id);
                if (request.responseJSON && request.responseJSON.hasOwnProperty('message')) {
                    toast(data.message);
                }
            }
        });
    }

    function unfollow(e) {
        var $el = $(e.target);
        var id = $el.data('id');

        $.ajax({
            type: 'POST',
            url: $el.data('href'),
            success: function (data) {
                $el.next().show();
                $el.hide();
                update_followers_count(id);
                if (request.responseJSON && request.responseJSON.hasOwnProperty('message')) {
                    toast(data.message);
                }
            }
        });
    }

    function update_notification_count() {
        var $el = $('#notification-badge');
        $.ajax({
            type: 'GET',
            url: $el.data('href'),
            success: function (data) {
                if (data.count === 0) {
                    $('#notification-badge').hide();
                } else {
                    $el.show();
                    $el.text(data.count)
                }
            }
        });
    }


    $('.profile-popover').hover(show_profile_popover.bind(this), hide_profile_over.bind(this));
    $(document).on('click', '.follow-btn', follow.bind(this));
    $(document).on('click', '.unfollow-btn', unfollow.bind(this));

    $('#confirm-delete').on('show.bs.modal', function(e) {
        $('.delete-form').attr('action', $(e.relatedTarget).data('href'));
    });

    $('#set-comment').on('click', function(e) {
        e.preventDefault();
        $el = $(e.target);
        $.ajax({
            type: 'POST',
            url: $el.data('href')
        });
    });

    $('#description-btn').click(function() {
        $('#description').hide();
        $('#description-form').show();
    });

    $('#cancel-description').click(function() {
        $('#description-form').hide();
        $('#description').show();
    });

    if (is_authenticated) {
        setInterval(update_notification_count, 30000);
    }
});
