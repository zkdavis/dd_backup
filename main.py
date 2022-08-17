import os
import time
import tkinter
from datetime import datetime
from tkinter import *
from crontab import CronTab
import keyring

class backup_info:
    def __init__(self):
        self.computer_name=None
        self.backup_location=None
        self.partition=None
        self.always_on=False
        self.email = None
        self.user = None

    def setup_cron(self):
        print("creating Cron Job")
        cron = CronTab('root')
        # cron = CronTab(user = 'root')
        directory = os.getcwd()
        command_name = 'python3 '+directory+'/main.py'
        ##check if cron is set
        exist_cron = cron.find_command(command_name)
        for cr in cron.crons:
            if(cr.command == command_name):
                print("cron exist already exiting program")
                exit(0)


        job = cron.new(command=command_name, comment='auto disk image creator job')
        job.hour.every(2)
        job.enable()

        cron.write()


    def loadConfig(self):
        if (os.path.exists('config.txt')):
            f = open('config.txt', 'r')
            ls = f.readlines()
            self.computer_name = ls[0].split("computer_name: ")[1].replace("\n", '')
            self.backup_location = ls[1].split("backup_location: ")[1].replace("\n", '')
            always_on_txt = ls[2].split("always_on: ")[1].replace("\n", '')
            if(always_on_txt.lower() == 'y'):
                self.always_on = True
            else:
                self.always_on = False
            self.partition = ls[3].split("partition: ")[1].replace("\n", '')
            self.email = ls[4].split("email: ")[1].replace("\n", '')
            self.user = ls[5].split("user: ")[1].replace("\n", '')
        else:
            self.setConfigFile()

    def setConfigFile(self):

        computer_name = input("What is this computer's name? \n")
        backup_location = input("Where do you wan't to store your backups? \n ex: /mnt/data/ \n")
        while (os.path.exists(backup_location) == False):
            print("back up location was invalid.")
            backup_location = input("Where do you wan't to store your backups? \n ex: /mnt/data/ \n")
        always_on_txt = input("Always on mode (y/N):")
        if (always_on_txt.lower() == 'y' or always_on_txt.lower() == 'n'):
            con_while = False
        else:
            con_while = True
        while(con_while):
            print("incorrect choice. Please try again entering 'y' or 'n' or press enter for 'n'")
            always_on_txt = input("Always on mode (y/N):")
            if(always_on_txt.lower() == 'y' or always_on_txt.lower() == 'n'):
                con_while=False
            else:
                con_while = True
        print("Warning! partition needs to be exact. If you are not sure quit here and check before continuing \n")
        print("Please write the partion or disk you wish to copy. \n")
        partition = input("ex: /dev/sda \n")
        print("Please enter your gmail password:\n")
        print("Note passwords are stored on the system keychain and not by this program.\n")
        pw = input("enter password: ")
        keyring.set_password('gmail_dd_email_pw',os.getlogin(), pw)
        email =input("Enter gmail: \n")
        user =input("Enter user: \n")
        f = open("config.txt", "w")
        f.write('computer_name: ' + computer_name)
        f.write('\n')
        f.write('backup_location: ' + backup_location)
        f.write('\n')
        f.write('always_on: ' + always_on_txt)
        f.write('\n')
        f.write('partition: ' + partition)
        f.write('\n')
        f.write('email: ' + email)
        f.write('\n')
        f.write('user: ' + user)
        f.write('\n')
        f.close()
        self.setup_cron()

gui_continue = False
lvtext = None
def continue_gui():
    global gui_continue
    global lvtext
    gui_continue = True
    timething = True
    count = 0
    while (timething):
        count += 10
        # if(gui_continue):
        #     break
        lvtext.set("Backup Started: " + str(count))
        time.sleep(1)

def gui_warning():
    global lvtext
    base_label = "Start backup warning do not disconnect"
    window = Tk()
    btn = Button(window, text=base_label, fg='blue',command=continue_gui)
    btn.place(x=80, y=100)
    lvtext = tkinter.StringVar()
    lvtext.set("Start Backup")
    lbl = Label(window, textvariable=lvtext, fg='red', font=("Helvetica", 16))
    lbl.place(x=60, y=50)
    lbl.pack()
    btn.pack()
    window.title('Backup warning')
    window.geometry("300x200+10+10")
    window.mainloop()


def send_email(bi: backup_info):
    import smtplib, ssl

    port = 465
    pw = keyring.get_password('gmail_dd_email_pw',bi.user)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(bi.email, pw)
        sender_email = bi.email
        receiver_email = bi.email
        message = " Subject: backup completed \nnotification that dd image was created for computer '"+bi.computer_name+"' \nThis message is sent from Python."
        server.sendmail(sender_email, receiver_email, message)


def start_backup(bi: backup_info):
    backup_file_base= 'backup_image'
    backup_base = bi.backup_location + bi.computer_name + "/"
    backup_file_init = backup_base + backup_file_base+'.img.gz'
    backup_file_monthly= backup_base + backup_file_base+'_monthly.img.gz'
    backup_file_command = backup_file_init
    if(os.path.exists(backup_file_init)):
        backup_file_command = backup_file_monthly
        if(os.path.exists(backup_file_monthly)):
            os.remove(backup_file_monthly)
    backup_command = 'sudo dd if=/dev/nvme0n1p4 conv=sync,noerror bs=64K | gzip -c  > ' + backup_file_command
    x_thread= None
    print("starting Backup do not shut off or disconnect the internet")

    if(bi.always_on==False):
        import threading
        x_thread = threading.Thread(target=gui_warning, daemon=True)
        x_thread.start()
    if(bi.always_on ==False):
        while(gui_continue == False):
            time.sleep(1)
        os.system(backup_command)
    else:
        os.system(backup_command)

    f = open(backup_base + "backup_info.txt", "w")

    now = datetime.now()
    year = now.strftime("%Y")
    f.write("year: " + year)
    f.write('\n')
    month = now.strftime("%m")
    f.write("month: " + month)
    f.write('\n')
    day = now.strftime("%d")
    f.write("day: " + day)
    f.write('\n')
    f.close()



    print("Backup finished")

    send_email(bi)





def compare_dates(bi: backup_info):
    backup_base = bi.backup_location + bi.computer_name + "/"

    f = open(backup_base+'backup_info.txt', 'r')
    ls = f.readlines()
    yr = ls[0].split("year: ")[1].replace("\n", '')
    month = ls[1].split("month: ")[1].replace("\n", '')
    day = ls[2].split("day: ")[1].replace("\n", '')
    datetime_object = datetime.strptime(month+'/'+day+'/'+yr, '%m/%d/%Y')

    timediff = datetime_object - datetime.now()
    if(abs(timediff.days) >30):
        start_backup(bi)

def check_for_backup(bi: backup_info):
    backup_base = bi.backup_location+bi.computer_name+"/"
    if(os.path.exists(backup_base)):
        compare_dates(bi)
    else:
        os.mkdir(backup_base)
        start_backup(bi)


def get_info():
    bi = backup_info()
    bi.loadConfig()
    # check_for_backup(bi)
    send_email(bi)



if __name__ == "__main__":
    get_info()
