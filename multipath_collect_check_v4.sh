#!/bin/bash
#######################################
####此脚本是针对多路径清理脚本
#######################################

set -x

UNUSED_PATH_FILE="/root/unused_path_uuid_`eval /usr/bin/date +%Y%m%d`.txt"
UNUSED_SINGLE_FILE="/tmp/unused_single_`eval /usr/bin/date +%Y%m%d`.txt"
OPERAT_LOG="/tmp/operat_log_`eval /usr/bin/date +%Y%m%d`.log"
UNUSED_MULTIPATH_FILE="/tmp/unused_multipath_`eval /usr/bin/date +%Y%m%d`.txt"
DELETE_SCRIPT_TXT="/tmp/delete_script_`eval /usr/bin/date +%Y%m%d`.txt"
DELETE_SINGLE_SCRIPT_TXT="/tmp/delete_single_script_`eval /usr/bin/date +%Y%m%d`.txt"

#判断容器是否可以exec进入
docker exec -u root multipathd ls >/dev/null
id1=`echo $?`

docker exec -u root nova_libvirt ls >/dev/null
id2=`echo $?`

if [ $id1 != 0 ]; then
   echo '请确保multipathd容器可以使用exec方式进入'
   exit 1
elif [ $id2 != 0 ]; then
   echo '请确保nova_libvirt容器可以使用exec方式进入' 
   exit 1
fi

#检查xml文件和virsh命令查到的vm个数对比
xml_num=`docker exec -u root nova_libvirt /bin/bash -c "ls /etc/libvirt/qemu/*.xml|wc -l"`
virsh_vm_num=`docker exec -u root nova_libvirt /bin/bash -c "virsh list --all|grep instance|wc -l"`
if [ $xml_num != $virsh_vm_num ]; then
   echo 'xml ${xml_num}与virsh ${virsh_vm_num}命令查到的vm 个数不一致'
   exit 1
fi

# 获取所有的路径wwn
get_all_path_uuid(){
    docker exec -u root multipathd /bin/bash -c "multipath -ll | grep dm-" |awk '{print $1}' > /root/mpath_total_uuid.txt
    ls /dev/disk/by-id/scsi-3* |grep -v 'part'|awk -F "scsi-" '{print $2}' > /root/scsi_uuid.txt
    cat /root/mpath_total_uuid.txt /root/scsi_uuid.txt | sort | uniq > /root/total_uuid.txt
}

# 获取正在使用的多路径wwn
get_used_mpath_uuid(){
    docker exec -u root nova_libvirt /bin/bash -c "grep -ri 'dm-uuid-mpath-' /etc/libvirt/qemu/*.xml"|awk -F "'" '{print $2}'|awk -F "dm-uuid-mpath-" '{print $2}'  > /root/mpath_used_uuid.txt
}

# 获取正在使用的单路径wwn
get_used_onepath_uuid(){
    docker exec -u root nova_libvirt /bin/bash -c "grep -ri 'by-path' /etc/libvirt/qemu/*.xml"  > /tmp/onepath_total_uuid1.txt
    for i in `grep by-path /tmp/onepath_total_uuid1.txt | awk -F "'" '{print $2}'`;do /lib/udev/scsi_id --page 0x83 --whitelisted $i; done > /root/onepath_total_uuid.txt
}

#系统路径
get_sys_uuid(){
    >/root/sys_path.txt
    for system_disk in `df -l |grep -v "Filesystem"|grep ^/dev/mapper |cut -d " " -f 1`; do
        /lib/udev/scsi_id  -g -u ${system_disk} >> /root/sys_path.txt
    done
}

# 合并单路径多路径wwn和系统path
get_save_all_used_uuid(){
    cat /root/mpath_used_uuid.txt /root/sys_path.txt /root/onepath_total_uuid.txt | sort | uniq > /root/all_used_uuid.txt
}

# 获取无效的多路径uuid
get_unused_path_uuid(){
    > ${UNUSED_PATH_FILE}
    cat /root/total_uuid.txt | while read line; do 
        if [ `grep -ic  $line /root/all_used_uuid.txt` -eq '0' ];then
             echo $line >> ${UNUSED_PATH_FILE}
        	fi
     done
}

#检查获取的多路径有无虚机使用
>${OPERAT_LOG}
check_vm_used(){
	cat ${UNUSED_PATH_FILE} |while read line;do
	    echo "#判断${line}有无虚机使用？" >>${OPERAT_LOG}
		docker exec -u root nova_libvirt /bin/bash -c "grep -rin $line /etc/libvirt/qemu/*.xml" >>${OPERAT_LOG} 2>&1
		#将再用的uuid从文件里删除
		if [ $? == 0 ];then
		    echo "#${line}有虚机使用,将${line}从${UNUSED_PATH_FILE}中删除" >>${OPERAT_LOG}
			sed -i '/'$line'/d' ${UNUSED_PATH_FILE}
		else
			echo "#${line}无虚机使用" >>${OPERAT_LOG}
		fi
	done
}

#检查路径uuid
check_multipath(){
	>${UNUSED_SINGLE_FILE}
	>${UNUSED_MULTIPATH_FILE}
	cat ${UNUSED_PATH_FILE} |while read line;do
		echo "#判断${line}是多路径还是单路径？" >>${OPERAT_LOG}
		docker exec -u root multipathd multipath -ll $line |grep dm >>${OPERAT_LOG} 2>&1
		#判断是否为多路径，若没有输出为但路径
		if [ $? == 0 ];then
			echo "#${line}是多路径,保存到多路径临时文件" >>${OPERAT_LOG}
			echo $line >> ${UNUSED_MULTIPATH_FILE}
		else
			echo "#${line}是单路径,保存到单路径临时文件" >>${OPERAT_LOG}
			echo $line >> ${UNUSED_SINGLE_FILE}
		fi
	done
}

#收集残留多路径dev并生成执行删除脚本
get_path_dev(){
	>${DELETE_SCRIPT_TXT}
	if [ -s ${UNUSED_MULTIPATH_FILE} ];then
		echo "#生成删除块设备执行命令,见${DLETE_SCRIPT_TXT}文件" >>${OPERAT_LOG}
		echo "set -x" >>${DELETE_SCRIPT_TXT}
		cat ${UNUSED_MULTIPATH_FILE}|while read line;do
			echo "#####删除${line}下的块设备##########" >>${DELETE_SCRIPT_TXT}
			if [ -n "$line" ];then
				devs=$(docker exec -u root multipathd multipath -ll $line |awk '{print $3}' |grep ^sd)
				for i in $devs;do
					echo "echo 1 >/sys/block/${i}/device/delete" >>${DELETE_SCRIPT_TXT}
				done
			fi
		done
	fi
}

#生成multipath删除多路径命令
get_multipath_command(){
	if [ -s ${UNUSED_MULTIPATH_FILE} ];then
		echo "#生成多路径删除执行命令,见${DLETE_SCRIPT_TXT}文件" >>${OPERAT_LOG}
		cat ${UNUSED_MULTIPATH_FILE}|while read line;do
			echo "#######删除多路径########" >>${DELETE_SCRIPT_TXT}
			if [ -n "$line" ];then
				echo "sleep 2" >>${DELETE_SCRIPT_TXT}
				echo "docker exec -u root multipathd multipath -f ${line}" >>${DELETE_SCRIPT_TXT}
				echo "if [ \$? != 0 ];then" >>${DELETE_SCRIPT_TXT}
				echo "   docker exec -u root multipathd multipath -f ${line}" >>${DELETE_SCRIPT_TXT}
				echo "fi" >>${DELETE_SCRIPT_TXT}
			fi
		done
	fi
}

#生成单路径删除命令
get_single_dev_command(){
	>${DELETE_SINGLE_SCRIPT_TXT}
	if [ -s ${UNUSED_SINGLE_FILE} ];then
		echo "#生成单路径删除执行命令,见${DELETE_SINGLE_SCRIPT_TXT}文件" >> ${OPERAT_LOG}
		echo "set -x" >> ${DELETE_SINGLE_SCRIPT_TXT}
		cat ${UNUSED_SINGLE_FILE}|while read line;do
			cat << EOF >> ${DELETE_SINGLE_SCRIPT_TXT}
while true;do 
	ls -l /dev/disk/by-id/scsi-${line} |awk -F '/' '{print \$NF}' >/tmp/single_dev.txt
	if [  -s /tmp/single_dev.txt ];then
		dev=\$(cat /tmp/single_dev.txt)
		lsblk|grep \$dev
		if [ \$? == 0 ];then
			echo "删除\${dev}"
			echo 1 >/sys/block/\$dev/device/delete
        else
			rm -rf /dev/disk/by-id/scsi-${line}
			break
	    fi
	else
		break
	fi
done
EOF
		done
	fi
}

# 执行获取函数
get_all_path_uuid
get_used_mpath_uuid
get_used_onepath_uuid
get_sys_uuid
get_save_all_used_uuid
get_unused_path_uuid

#执行检查函数
check_vm_used
check_multipath
get_path_dev
get_multipath_command
get_single_dev_command


