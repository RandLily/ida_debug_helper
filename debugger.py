from sqlalchemy import true
import threading
import idaapi
import subprocess

def adb_connect(ip,port=None):
    if port!=None:
        cmd="adb connect "+ip+":"+str(port)
    else:
        cmd="adb connect "+ip
    subprocess.run(cmd,shell=True)

def adb_input(string):
	cmd="adb shell input text "+str(string)
	subprocess.run(cmd,shell=True)
        
def start_server(name):
    cmd='start adb shell "su -c \'./data/local/tmp/'+name+"'"
    subprocess.Popen(cmd,shell=True)
    
def jdb_connect():
    subprocess.Popen("jdb -connect com.sun.jdi.SocketAttach:hostname=localhost,port=17788",shell=True)

def cat_maps(name,pid):
    cmd="adb shell "
    cmd+='"su -c '+"'cat /proc/" + str(pid) + "/maps | grep " + name + "'\""
    return subprocess.getoutput(cmd)

#mode：0为attach模式(默认)，1为spawn模式(按需)
#port：ida端口，默认为23976
def start_debug(package_name,mode=0,port=23946,brk=0):
    so_name = idaapi.get_root_filename()
    print("------------target is "+so_name+"------------")
    subprocess.run("adb forward tcp:"+str(port)+" tcp:"+str(port),shell=True)
    #spawn模式可能会出现获取不到基地址情况，按需使用
    if mode==1:
        subprocess.run("adb shell am set-debug-app -w " + package_name,shell=True)
        print("[*]spwan mode")
    else:
        print("[*]attach mode")
    print("[*]plz click " + package_name)   
    cmd="ps -A | grep " + package_name
    while True:
        tmp=subprocess.getoutput("adb shell "+'"'+cmd+'"')
        if(package_name in tmp):
            break
    tmp = tmp.split()
    pid = int(tmp[1])
    print("[*]"+package_name + " pid :" + str(pid))
    subprocess.run("adb forward tcp:17788"+" jdwp:"+str(pid),shell=True)
    ida_dbg.set_remote_debugger("localhost",None)
    attach_process(pid,1)
    set_debugger_options(DOPT_LIB_BPT | DOPT_THREAD_BPT)
    t1 = threading.Thread(target = jdb_connect)
    t1.start()
    #某些SO在IDA中不以文件名显示，而在apk中
    r=cat_maps(so_name,pid)
    if r=='':
    	r=cat_maps(package_name,pid)
    tmp=r.split()
    base=0
    for i in range(len(tmp)):
        if tmp[i] == "r-xp":
            base = tmp[i-1]
            base = base.split("-")[0]
            base = int(base, 16)
            break
    print('[*]found so base:'+hex(base))
    if brk!=0 and base!=0:
        idaapi.add_bpt(base+brk)
        print('[*]set breakpoint at:'+hex(base+brk))
