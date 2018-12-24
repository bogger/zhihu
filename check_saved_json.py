import json
import glob
import os
import sys
period = sys.argv[1]
task_id = sys.argv[2]
if len(sys.argv) > 3:
    delete = True
else:
    delete = False
f = open("ego_urls_nonorganization.txt")
start_urls = []
user_id_dict = {}
for x in f.readlines():
    item = x.strip().split()
    user_id_dict[item[1]] = item[0]
    start_urls.append(item[1])
f.close()
save_path = "ego_nodes_period" +str(period)+"_"+str(task_id)
unfinished_ids = []
nofile_ids=[]
dup_ids = []
del_files = []
good_files = []
json_files = {}
for i in range(len(start_urls)):
    url=start_urls[i]
    user_id = user_id_dict[url]
    json_file = glob.glob(save_path+'/*'+user_id+'.json')
    if not json_file:
        nofile_ids.append(user_id)
    else:
        if len(json_file) > 1:
            dup_ids.append(user_id)
        first_valid_json = None
        for jf in json_file:
            
            user_info = json.load(open(jf))
            # note the previous results does not have to_do_list
            if 'to_do_list' in user_info and len(user_info['to_do_list']) > 0:
                #unfinished_ids.append((jf,user_id))
                del_files.append(jf)
            else:
                if not first_valid_json:
                    first_valid_json = jf
                    good_files.append(jf)
                else:
                    del_files.append(jf)
        if not first_valid_json:
            unfinished_ids.append(user_id)
print 'nofile ids'
print nofile_ids
print 'unfinished_ids'
print unfinished_ids
print 'dup ids'
print dup_ids
print '#good files', len(good_files)
print '#del files', len(del_files)
if delete and len(good_files) == 1984 and not nofile_ids and not unfinished_ids:
    for jf in del_files:
        os.remove(jf)
        print jf, 'removed'
