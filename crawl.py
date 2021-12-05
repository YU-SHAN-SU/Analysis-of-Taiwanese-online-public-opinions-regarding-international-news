import requests
import urllib
from bs4 import BeautifulSoup
from tqdm import tqdm
import sys

import pickle as pk
from joblib import Parallel, delayed
import numpy as np
import argparse
def get_article(rs, url):
    res = rs.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    meta = soup.find_all('div', 'article-metaline')

    author = meta[0].find('span', 'article-meta-value').text
    title = meta[1].find('span', 'article-meta-value').text
    date = meta[2].find('span', 'article-meta-value').text

    author = author.split('(')[0].strip()

    '''
    content = soup.find('div', id='main-content').text
    end = soup.find('span', 'f2').text

    for s in soup.find_all('span', 'f2'):
        if '發信站' in s.text:
            ip_addr = s.text.split('來自: ')[1]
            break
    ip, country = ip_addr.split()
    country = country[1:-1]
    good = 0
    boo = 0
    arr = 0

    cmts_list = soup.find_all('div', 'push')
    cmts = []
    if cmts_list:
        for c in cmts_list:
            if 'warning-box' in c.get('class'):
                continue
            ctype = c.find('span', 'push-tag').text.strip()
            if ctype == '→':
                arr += 1
            elif ctype == '推':
                good += 1
            elif ctype == '噓':
                boo += 1
#             cid = c.find('span', 'push-userid').text
#             ccontent = c.find('span', 'push-content').text[2:].strip()
    '''
    info = ['author', 'title', 'date']
    
    scope = locals()
    
    info_dict = dict((k, scope[k]) for k in info)
    return info_dict

def get_all_articles(base, all_idx):
    session = requests.session()
    res = session.post('https://www.ptt.cc/ask/over18', data={'yes':'yes'})

    # all_idx = [30000, 30001, ..., 30010]
    info_dicts = {}
    for idx in all_idx:
        # cur_url = 'https://www.ptt.cc/bbs/Gossiping/index30000.html'
        cur_url = base + str(idx) + '.html'
        res = session.get(cur_url)
        soup = BeautifulSoup(res.text, 'html.parser')

        title_list = soup.find_all('div', 'r-ent')

        for title in title_list:
            link = title.find('a')
            if link:
                link = link.get('href')
                url = urllib.parse.urljoin(cur_url, link)
                try:
                    info_dicts[url] = get_article(session, url)
                except:
                    print(url, file=sys.stderr)
    print(len(info_dicts))
    return info_dicts

def main(url, base, num_pages, n_jobs):
    session = requests.session()
    res = session.post('https://www.ptt.cc/ask/over18', data={'yes':'yes'})
    res = session.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    prev = soup.find_all('a', 'btn wide')[1].get('href')
    cur_idx = int(prev[prev.find('index')+5:prev.find('.html')]) + 1
    start_idx = cur_idx - num_pages + 1
    all_idx = np.array([i for i in range(start_idx, start_idx+num_pages)])
    segmented_idx = np.array_split(all_idx, n_jobs)

    info_dicts_list = Parallel(n_jobs=n_jobs)(delayed(get_all_articles)(base, idx) for idx in (segmented_idx))

    info_dicts = {}
    for dic in info_dicts_list:
        info_dicts.update(dic)
    print(len(info_dicts))

    with open('info.pkl', 'wb') as f:
        pk.dump(info_dicts, f)


if __name__ == '__main__':
    # Config
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', '--n_jobs', type=int, default=8)
    parser.add_argument('-n', '--num_pages', type=int, default=100)

    args = parser.parse_args()

    url = 'https://www.ptt.cc/bbs/Gossiping/index.html'
    base = 'https://www.ptt.cc/bbs/Gossiping/index'

    main(url, base, args.num_pages, args.n_jobs)
