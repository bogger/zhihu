import os
import logging
import sys
import json
import csv
logger = logging.getLogger(__name__)
proxy_dict = {"HTTP": "1000", "HTTPS":"0100", "SOCKS4":"0010", "SOCKS5":"0001"}
def get_proxies(output_file, proxy_source, maxtime=500, anno=34):
    #logger.info("get proxies file")
    """
        Get proxies from http://incloak.com/ (updated every 2 hours)
    """
    #mycode = "185613621911033" 
    if proxy_source == 'cloak':
        mycode = "144368111202493"
        url =  "curl 'https://hidemy.name/api/proxylist.txt?maxtime=%d&anno=%d&out=csv&code=%s' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Connection: keep-alive' --compressed -o %s" % (maxtime, anno, mycode, output_file) 
        os.system(url)
        all_proxies = {}
        with open(output_file, 'rb') as f:
            csv_reader = csv.reader(f, delimiter=';')
            next(csv_reader, None)
            for row in csv_reader:
                proc_type = ''.join(row[-4:])
                all_proxies[row[1]+':'+row[2]] = proc_type
    elif proxy_source=='nord':
        web_url = 'https://nordvpn.com/wp-admin/admin-ajax.php?searchParameters%5B0%5D%5Bname%5D=proxy-country&searchParameters%5B0%5D%5Bvalue%5D=united+states&searchParameters%5B1%5D%5Bname%5D=proxy-ports&searchParameters%5B1%5D%5Bvalue%5D=&searchParameters%5B2%5D%5Bname%5D=http&searchParameters%5B2%5D%5Bvalue%5D=on&searchParameters%5B3%5D%5Bname%5D=https&searchParameters%5B3%5D%5Bvalue%5D=on&searchParameters%5B4%5D%5Bname%5D=socks4&searchParameters%5B4%5D%5Bvalue%5D=on&searchParameters%5B5%5D%5Bname%5D=socks5&searchParameters%5B5%5D%5Bvalue%5D=on&offset=0&limit=200&action=getProxies'
        url = "curl '%s' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Connection: keep-alive' --compressed -o %s" % (web_url, output_file)

        os.system(url)
        all_proxy_json = json.load(open(output_file))
        all_proxies = {}
        for prox in all_proxy_json:

            all_proxies[prox['ip'] +':'+ prox['port']] = proxy_dict[prox['type']]
    elif proxy_source=='zhima':
        web_url='http://webapi.http.zhimacangku.com/getip?num=4&type=1&pro=0&city=0&yys=0&port=11&pack=21928&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions='
        url = "curl '%s' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Connection: keep-alive' --compressed -o %s" % (web_url, output_file)
        os.system(url)
        all_proxies = {}
        with open(output_file) as f:
            for line in f:
                ip = line.strip()
                all_proxies[ip] = "0100"
    elif proxy_source=='plain':
        all_proxies = {}
        with open('plain_proxies.txt') as f:
            for line in f:
                items = line.strip().split(':')
                all_proxies[items[0]+':'+items[1]] = "0100"
    else:
        raise Exception("proxy source unknown!")
    return all_proxies

def check_file(filename, filename_bak):
    with open(filename, 'r') as p:
        lines = p.readlines()
        if len(lines) < 10:
            logger.info("File len is only %d" % len(lines))
            # use backup file 
            os.system("cp %s %s" %(filename, filename_bak))
        else:
            logger.info("File name %s has %s lines" % (filename, len(lines)))


def update_proxyfile(f1, f2):
    """
        Append content of f2 to f1
    """
    os.system("cat %s >> %s " % (f2,f1))

if __name__ == "__main__":
    filename = sys.argv[1]
    proxy_source = sys.argv[2]
    print get_proxies(filename, proxy_source)

