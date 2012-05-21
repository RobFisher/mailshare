# License: https://github.com/RobFisher/mailshare/blob/master/LICENSE

import models
import search
from operator import itemgetter

def search_results_to_top_senders_html(query_set, current_search):
    senders_dict = {}
    for m in query_set:
        if m.sender in senders_dict:
            senders_dict[m.sender] = senders_dict[m.sender] + 1
        else:
            senders_dict[m.sender] = 1
    senders_list = sorted(senders_dict.iteritems(), key=itemgetter(1), reverse=True)
    top_senders = senders_list[:5]

    html = '<ol>'
    for sender, number in top_senders:
        sender_search = current_search.add_and(search.get_sender_id_search(sender.id))
        html += '<li><a href="' + sender_search.get_url_path()
        html += '" title="' + sender.address + '">'
        html += sender.name + '</a> : ' + str(number) + '</li>'
    html += '</ol>'
    return html
