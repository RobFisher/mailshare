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
    Dajaxice.mailshare.mailshareapp.expand_email(Dajax.process,{'email_id':email_id,'url':location.href})
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
    if(email_id == -1) {
	Dajaxice.mailshare.mailshareapp.multi_add_tag(Dajax.process,{'selected_mails':selected_mails,'tag':text, 'url':location.href});
    }
    else {
	Dajaxice.mailshare.mailshareapp.add_tag(Dajax.process,{'email_id':email_id,'tag':text, 'url':location.href});
    }
}

function delete_tag(email_id, tag_id) {
    if(email_id == -1) {
	var answer = confirm("Deleting a tag from selected emails cannot be undone.");
        if(answer) {
	    Dajaxice.mailshare.mailshareapp.multi_delete_tag(Dajax.process,{'selected_mails':selected_mails,'tag_id':tag_id, 'url':location.href});
        }
    }
    else {
        Dajaxice.mailshare.mailshareapp.delete_tag(Dajax.process,{'email_id':email_id,'tag_id':tag_id, 'url':location.href});
    }
    return false;
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

function delete_mail(email_id) {
    var answer = confirm("This will permanently delete the email from the Mailshare database.");
    if(answer) {
	Dajaxice.mailshare.mailshareapp.delete_email(Dajax.process,{'email_id':email_id});
    }
}

function mail_deleted(success) {
    if(success) {
	window.location.reload();
    }
    else {
	alert("Unable to delete email.");
    }
}

var selected_mails = [];
function select_email(mail_id) {
    selected_mails.push(mail_id);
}

function unselect_email(mail_id) {
    selected_mails.splice(selected_mails.indexOf(mail_id), 1);
}

function get_multibar_update() {
    Dajaxice.mailshare.mailshareapp.get_multibar_tags(Dajax.process,{'selected_mails':selected_mails, 'url':location.href});
}

function update_multibar(data) {
    if(data.tags_html != '') {
        $("#multi_bar_tags").html(data.tags_html);
    }
    else {
        $("#multi_bar_tags").html("Select emails to view and edit their tags.");
    }
}

function checkbox_clicked(checkbox, mail_id) {
    if(checkbox.checked) {
	select_email(mail_id);
    }
    else {
	unselect_email(mail_id);
    }
    get_multibar_update();
}

function invert_selection() {
    $(".mailcheck").each(function(i) {
	var mail_id = parseInt(this.name.substr(6));
	if(this.checked) {
	    unselect_email(mail_id);
	    this.checked = false;
	}
	else {
	    select_email(mail_id);
	    this.checked = true;
	}
    });
    get_multibar_update();
}


function document_ready_function() {
    $(".mailcheck").each(function(i) {
	var mail_id = parseInt(this.name.substr(6));
        if(this.checked) {
            select_email(mail_id);
	}
    });
    if(selected_mails.length > 0) {
        get_multibar_update();
    }
}

$(document).ready(document_ready_function);
