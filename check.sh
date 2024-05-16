constraints=$(basename $1)

old="/data/emilio/FunTaxIS-lite-main/output/${constraints}"
new="/data/emilio/FunTaxIS-lite-develop/outputs/${constraints}"

cut -f1 $old |sort |uniq > old.txt
cut -f1 $new |sort |uniq > new.txt

comm -12 old.txt new.txt > common.txt
comm -23 old.txt new.txt > only_old.txt
comm -13 old.txt new.txt > only_new.txt

old_count=$(wc -l $old |cut -f1 -d" ")
new_count=$(wc -l $new |cut -f1 -d" ")
common_count=$(wc -l common.txt |cut -f1 -d" ")

echo $constraints
echo "OLD: " $old_count "NEW: " $new_count "COMMON: " $common_count
echo 'ONLY IN OLD'
for go in $(cat only_old.txt)
do
    grep $go $old
done

echo 'ONLY IN NEW'
for go in $(cat only_new.txt)
do
    grep $go $new
done

echo ""

