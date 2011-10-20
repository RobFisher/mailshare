function get_email_body_element(email_id) {
    element_selector = "#body_" + email_id;
    return $(element_selector)
}

function scroll_to_position(position) {
    /* http://twigstechtips.blogspot.com/2010/02/jquery-animated-scroll-to-element.html */
    $('html,body').animate({ scrollTop: position },
        { duration: 'slow', easing: 'swing'});
}

function scroll_to_row(element) {
    body_row = element.parent();
    hidden_height = body_row.offset().top + body_row.height() -
        ($(window).scrollTop() + $(window).height());
    if(hidden_height > 0) {
        header_row = body_row.prev();
        if((body_row.height() + header_row.height()) < $(window).height()) {
            scroll_to_position($(window).scrollTop() + hidden_height);
        }
        else {
            scroll_to_position(header_row.offset().top);
        }
    }
}

function toggle_email_body(email_id) {
    element = get_email_body_element(email_id);
    if(element.hasClass("empty")) {
        element.toggleClass("empty showing");
        fetch_email(email_id, $(element));
    }
    else if(element.hasClass("shown")) {
        element.toggleClass("shown hidden");
    }
    else if(element.hasClass("hidden")) {
        element.toggleClass("hidden shown");
        scroll_to_row(element);
    }
}

function fetch_email(email_id) {
    Dajaxice.mailshare.mailshareapp.expand_email(Dajax.process,{'email_id':email_id})
}

function set_email_body(data) {
    element = get_email_body_element(data.email_id);
    element.html(data.email_body);
    element.toggleClass("showing shown");
    scroll_to_row(element);
}

tag_response_callback = null;
function fetch_tag_completion(request, response) {
    tag_response_callback = response;
    Dajaxice.mailshare.mailshareapp.tag_completion(Dajax.process,{'text':request.term});
}

function set_tag_completion(data) {
    if(tag_response_callback) {
        tag_response_callback(data.tags);
    }
}

function add_tag(email_id) {
    $("#tagbutton_" + email_id).toggleClass("shown hidden");
    tagbox=$("#tagbox_" + email_id);
    tagbox.toggleClass("hidden shown");
    tagbox.autocomplete({source: fetch_tag_completion,
                         select: tag_select_callback(email_id)});
    tagbox.focus();
}

function add_tag_to_email(email_id, text) {
    Dajaxice.mailshare.mailshareapp.add_tag(Dajax.process,{'email_id':email_id,'tag':text});
}

function tag_key(event, email_id) {
    if(event.keyCode == 13) {
        tagbox=$("#tagbox_" + email_id);
        add_tag_to_email(email_id, tagbox.val());
    }
}

/* for explanation see http://stackoverflow.com/questions/939032/jquery-pass-more-parameters-into-callback */
var tag_select_callback=function tag_selected(email_id) {
    return function(event, ui) {
        add_tag_to_email(email_id, ui.item.value);
    }
}

function update_tags(data) {
    $("#taglist_" + data.email_id).html(data.tags_html);
    $("#tagbox_" + data.email_id).val('');
}

function tagbox_blur(email_id) {
    $("#tagbox_" + email_id).toggleClass("shown hidden");
    $("#tagbutton_" + email_id).toggleClass("shown hidden");
}
