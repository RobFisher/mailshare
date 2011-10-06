# Code copied from http://djangosnippets.org/snippets/19/

# License information from http://djangosnippets.org/about/tos/ :

# I hate legal-speak as much as anybody, but on a site which is geared
# toward sharing code there has to be at least a little bit of it, so
# here goes:
#
# By creating an account here you agree to three things:
#
# 1. That you will only post code which you wrote yourself and that
# you have the legal right to release under these terms.
#
# 2. That you grant any third party who sees the code you post a
# royalty-free, non-exclusive license to copy and distribute that code
# and to make and distribute derivative works based on that code. You
# may include license terms in snippets you post, if you wish to use a
# particular license (such as the BSD license or GNU GPL), but that
# license must permit royalty-free copying, distribution and
# modification of the code to which it is applied.
#
# 3. That if you post code of which you are not the author or for
# which you do not have the legal right to distribute according to
# these terms, you will indemnify and hold harmless the operators of
# this site and any third parties who are exposed to liability as a
# result of your actions.  If you can't legally agree to these terms,
# or don't want to, you cannot create an account here.

import re
import cgi

re_string = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \t]+)|(?P<lineend>\r\n|\r|\n)|(?P<protocal>(^|\s)((http|ftp)://.*?))(\s|$)', re.S|re.M|re.I)
def plaintext2html(text, tabstop=4):
    def do_sub(m):
        c = m.groupdict()
        if c['htmlchars']:
            return cgi.escape(c['htmlchars'])
        if c['lineend']:
            return '<br>'
        elif c['space']:
            t = m.group().replace('\t', '&nbsp;'*tabstop)
            t = t.replace(' ', '&nbsp;')
            return t
        elif c['space'] == '\t':
            return ' '*tabstop;
        else:
            url = m.group('protocal')
            if url.startswith(' '):
                prefix = ' '
                url = url[1:]
            else:
                prefix = ''
            last = m.groups()[-1]
            if last in ['\n', '\r', '\r\n']:
                last = '<br>'
            return '%s<a href="%s">%s</a>%s' % (prefix, url, url, last)
    return re.sub(re_string, do_sub, text)
