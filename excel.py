#coding=utf-8
import xlsxwriter as xw
import openstack

#写入数据
def write_excel(filename):
     f = xw.Workbook(filename)

     #设置表格样式
     bold = f.add_format({
        'bold':  True,  # 字体加粗
        'border': 1,  # 单元格边框宽度
        'align': 'left',  # 水平对齐方式
        'valign': 'vcenter',  # 垂直对齐方式
        'fg_color': '#F4B084',  # 单元格背景颜色
        'text_wrap': True,  # 是否自动换行
    })
     #创建sheet1
     sheet1 = f.add_worksheet("sheet1")
     sheet1.activate()
     #import pdb;pdb.set_trace()
     row0 = [u'名称',u'镜像',u'内网ip',u'浮动ip',u'配置',u'cpu(核)',u'内存(G)',u'硬盘(G)',u'状态',u'锁定',u'计费方式',u'创建于']
     sheet1.write_row('A1', row0, bold)

     servers = openstack.Server()
     data = servers.server_mata()

     i = 2  # 从第二行开始写入数据
     for j in range(len(data)):
         
         data[j]['address']=str(data[j]['address']).strip("[]")
         if not data[j]['floating_ip']:
             data[j]['floating_ip']="NUll"
         else:
             data[j]['floating_ip']=str(data[j]['floating_ip']).strip("[]")

         insertdata = [data[j]['name'],data[j]['image'],data[j]['address'],data[j]['floating_ip'],data[j]['flavor'],data[j]['cpus'],data[j]['ram'],data[j]['volume'],data[j]['status'],u'false',u'按量计费',data[j]['created']]


         row = 'A' + str(i)
         #import pdb;pdb.set_trace()
         sheet1.write_row(row, insertdata)
         i += 1

     f.close()  # 关闭表

write_excel(filename="server.xlsx")

