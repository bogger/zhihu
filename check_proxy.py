import os
import csv
block_list = []
with open("ip_block_list.txt") as f:
    block_list = [line.strip() for line in f]
all_proxies = []
with open("current_proxies_61_3.txt", 'rb') as f:
    csv_reader = csv.reader(f, delimiter=';')
    next(csv_reader, None)
    for row in csv_reader:
        all_proxies.append(row[1]+':'+row[2])
good_ips = [x for x in all_proxies if x not in block_list]
print "there are %d good ips" % len(good_ips)
