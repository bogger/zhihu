import os
import sys
period= sys.argv[1]
block_list = []
for idx in range(4):
    filename = "ip_block_list_%s_%d.txt" % (period, idx)
    with open(filename) as f:
        block_list += [line.strip() for line in f]
block_list = list(set(block_list))
# remove recovered ips
recovered_file = "ip_recovered_list.txt"
if os.path.exists(recovered_file):
    with open(recovered_file) as f:
	recovered_list = [line.strip() for line in f]
    for ip in recovered_list:
	block_list.remove(ip)
with open("ip_block_list.txt",'w') as f:
    f.write("\n".join(block_list))
