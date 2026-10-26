"""Open Web discovery and set coverage for final musical assertions.
Coverage is NOT proof; this module never claims or finishes a LAB job.
"""
import argparse
from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
from urllib.parse import parse_qs, quote, unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
from runtime.musical_contract import normalize

MAX_BYTES = 600000

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.links, self.skip = [], [], 0
        self.href, self.anchor = None, []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in ('script', 'style', 'noscript'):
            self.skip += 1
        elif tag == 'a' and not self.skip:
            self.href, self.anchor = attrs.get('href'), []

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self.skip = max(0, self.skip - 1)
        elif tag == 'a' and self.href:
            self.links.append((self.href, ' '.join(self.anchor)))
            self.href, self.anchor = None, []

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())
            if self.href:
                self.anchor.append(data.strip())

    @property
    def text(self):
        return ' '.join(self.parts)

def public_https(url):
    try:
        p = urlsplit(url)
        host = p.hostname
        if p.scheme != 'https' or not host or p.username or p.password or p.port not in (None, 443):
            return False
        if host.lower() == 'localhost' or host.lower().endswith(('.localhost', '.local', '.internal')):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return '.' in host
    except ValueError:
        return False

def fetch_public(url):
    if not public_https(url):
        raise ValueError('non_public_https_url')
    host = urlsplit(url).hostname
    # Strict isolation additionally requires network egress policy against DNS rebinding.
    for addr in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(addr[4][0]).is_global:
            raise ValueError('private_dns_address')
    request = Request(url, headers={'User-Agent':'EZStudioLabAssistant/1.6 (open-web-research)',
                                     'Accept':'text/html'})
    with urlopen(request, timeout=9) as response:
        if not public_https(response.geturl()):
            raise ValueError('non_public_redirect')
        if 'html' not in response.headers.get('Content-Type','').lower():
            raise ValueError('non_html_resource')
        raw = response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise ValueError('resource_too_large')
    return raw.decode('utf-8',errors='replace')

def query_for(recording, assertion=None):
    query = '"' + recording['title'] + '" "' + recording['artist'] + '"'
    if recording.get('version'):
        query += ' "' + recording['version'] + '"'
    return query + (' ' + assertion['characteristic'] if assertion else ' music recording')

def search_web(query, *, get=fetch_public, limit=12):
    """Open discovery via general Web search. No music-site allowlist."""
    document = Document()
    document.feed(get('https://html.duckduckgo.com/html/?q='+quote(query)))
    result, seen = [], set()
    for href, title in document.links:
        if href.startswith('//'):
            href='https:'+href
        elif href.startswith('/'):
            href=urljoin('https://html.duckduckgo.com',href)
        parsed=urlsplit(href)
        if parsed.hostname and parsed.hostname.endswith('duckduckgo.com'):
            wrapped=parse_qs(parsed.query).get('uddg',[])
            if not wrapped:
                continue
            href=unquote(wrapped[0])
        if public_https(href) and href not in seen:
            seen.add(href)
            result.append({'url':href,'label':title[:180]})
            if len(result)>=limit:break
    return result

def analyze(payload, *, search=search_web, fetch=fetch_public, max_pages=18):
    # Strict projection: do not send or echo scientific data from LAB.
    data=normalize({'recording':payload['recording'], 'assertions':payload['assertions']})
    recording, assertions=data['recording'], data['assertions']
    found, events, errors={}, [], []
    for query in [query_for(recording)]+[query_for(recording,a) for a in assertions]:
        try:
            candidates=search(query)
            events.append({'phase':'discovery','query':query,'candidate_count':len(candidates)})
            for candidate in candidates:
                url=candidate.get('url','') if isinstance(candidate,dict) else ''
                if public_https(url):
                    found.setdefault(url,candidate.get('label','')[:180])
        except Exception as exc:
            errors.append({'phase':'discovery','query':query,'reason':type(exc).__name__})
    sets={a['id']:set() for a in assertions}
    pages=[]
    for url,title in list(found.items())[:max_pages]:
        try:
            page=Document()
            page.feed(fetch(url))
            content=page.text[:90000]
            words=set(re.findall(r'\w+',content.casefold(),flags=re.UNICODE))
            hits=[]
            for a in assertions:
                needle=set(re.findall(r'\w+',a['characteristic'].casefold(),flags=re.UNICODE))
                if needle and needle.issubset(words):
                    sets[a['id']].add(url)
                    hits.append(a['id'])
            pages.append({'url':url,'title':title,'candidate_assertions':hits,
                          'identity_verified':False,'evidence_verified':False,
                          'excerpt':content[:250]})
            events.append({'phase':'page_read','url':url,'candidate_assertions':hits})
        except Exception as exc:
            errors.append({'phase':'page_read','url':url,'reason':type(exc).__name__})
    intersections=[]
    for i,a in enumerate(assertions):
        for b in assertions[i+1:]:
            urls=sorted(sets[a['id']] & sets[b['id']])
            if urls:
                intersections.append({'assertions':[a['id'],b['id']],'urls':urls})
    return {'schema':'ezs.open-web-sets.v1','job_id':payload.get('job_id'),
            'run_id':payload.get('run_id'),'song_id':payload.get('song_id'),
            'recording':recording,'assertions':assertions,
            'status':'candidate_coverage_only_no_musical_verdict',
            's_total':[p['url'] for p in pages],
            'discovered_count':len(found),'read_count':len(pages),
            'sets':{k:sorted(v) for k,v in sets.items()},
            'intersections':intersections,'pages':pages,
            'events':events,'errors':errors,'verdicts':[],
            'persisted_to_lab':False}

def main():
    parser=argparse.ArgumentParser(description='Read-only open Web source set discovery')
    parser.add_argument('--input',required=True,help='JSON job context without token')
    parser.add_argument('--output',help='JSON output path outside repository')
    args=parser.parse_args()
    with open(args.input,encoding='utf-8-sig') as stream:
        payload=json.load(stream)
    result=analyze(payload)
    output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        with open(args.output,'w',encoding='utf-8') as stream:stream.write(output)
    else:print(output)
    return 0 if result['read_count'] else 2

if __name__=='__main__':
    raise SystemExit(main())
