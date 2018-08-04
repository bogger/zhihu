set -e
period=$1 
period_new=$((period + 1))
mv ego_nodes_period${period}_1/* ego_nodes_period${period}_0/
mv ego_nodes_period${period}_2/* ego_nodes_period${period}_0/
mv ego_nodes_period${period}_3/* ego_nodes_period${period}_0/
num=$(find ego_nodes_period${period}_0/*|wc -l)
echo $num
if [ $num = "1984" ]; then
	rm -r ego_nodes_period${period}_1
	rm -r ego_nodes_period${period}_2
	rm -r ego_nodes_period${period}_3
    mv ego_nodes_period${period}_0 ego_nodes_period${period}
    mkdir ego_nodes_period${period_new}_3
    mkdir ego_nodes_period${period_new}_2
    mkdir ego_nodes_period${period_new}_1
    mkdir ego_nodes_period${period_new}_0
    python main_crawl_zhihu_period.py ${period_new} 0 0 450 zhima > scrape${period_new}_0.log 2>&1 &
    sleep 5
	python main_crawl_zhihu_period.py ${period_new} 1 450 950 zhima > scrape${period_new}_1.log 2>&1 &
    sleep 5
	python main_crawl_zhihu_period.py ${period_new} 2 950 1450 zhima > scrape${period_new}_2.log 2>&1 &
    sleep 5
	python main_crawl_zhihu_period.py ${period_new} 3 1450 1984 > scrape${period_new}_3.log 2>&1 &
else
    echo “file number not right”
 fi
