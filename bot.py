#!/usr/bin/python
import sys
import xmpp
import threading
import getpass

commands={}
i18n={'ru':{},'en':{}}
########################### user handlers start ##################################
i18n['en']['HELP']="This is example jabber bot.\nAvailable commands: %s"
def helpHandler(user,command,args,mess):
    lst=commands.keys()
    lst.sort()
    return "HELP",', '.join(lst)

i18n['en']['EMPTY']="%s"
i18n['en']['HOOK1']='Responce 1: %s'
def hook1Handler(user,command,args,mess):
    return "HOOK1",'You requested: %s'%args

i18n['en']['HOOK2']='Responce 2: %s'
def hook2Handler(user,command,args,mess):
    return "HOOK2","hook2 called with %s"%(`(user,command,args,mess)`)

i18n['en']['HOOK3']='Responce 3: static string'
def hook3Handler(user,command,args,mess):
    return "HOOK3"*int(args)
########################### user handlers stop ###################################
############################ bot logic start #####################################
i18n['en']["UNKNOWN COMMAND"]='Unknown command "%s". Try "help"'
i18n['en']["UNKNOWN USER"]="I do not know you. Register first."

def messageCB(conn,mess):
    text=mess.getBody()
    user=mess.getFrom()
    userjid = xmpp.JID(user)
    user.lang='en'      # dup
    reply="Not now %s!" % userjid.getNode()
    conn.send(xmpp.Message(mess.getFrom(),reply))
    return

    if text.find(' ')+1: command,args=text.split(' ',1)
    else: command,args=text,''
    cmd=command.lower()

    if commands.has_key(cmd): reply=commands[cmd](user,command,args,mess)
    else: reply=("UNKNOWN COMMAND",cmd)

    if type(reply)==type(()):
        key,args=reply
        if i18n[user.lang].has_key(key): pat=i18n[user.lang][key]
        elif i18n['en'].has_key(key): pat=i18n['en'][key]
        else: pat="%s"
        if type(pat)==type(''): reply=pat%args
        else: reply=pat(**args)
    else:
        try: reply=i18n[user.lang][reply]
        except KeyError:
            try: reply=i18n['en'][reply]
            except KeyError: pass
    if reply: conn.send(xmpp.Message(mess.getFrom(),reply))

def presenceCB(conn,mess):
    prs_type=mess.getType()
    who=mess.getFrom()
    if prs_type == "subscribe":
        conn.send(xmpp.Presence(to=who, typ = 'subscribed'))
        conn.send(xmpp.Presence(to=who, typ = 'subscribe'))

for i in globals().keys():
    if i[-7:]=='Handler' and i[:-7].lower()==i[:-7]: commands[i[:-7]]=globals()[i]

############################# bot logic stop #####################################

### dispatcher thread ###

class DispatchThread(threading.Thread):

    def __init__(self, connection):
        self.conn = connection
        threading.Thread.__init__(self)

    def StepOn(self):
        try:
            self.conn.Process(1)
        except KeyboardInterrupt: return 0
        return 1

    def run(self):
        while self.StepOn():
            pass

### dispatcher thread end ###

try:
    account = raw_input('Enter your gmail address: ')
    password = getpass.getpass('Enter your password: ')

    jid=xmpp.JID(account)
    user,server=jid.getNode(),jid.getDomain()

    conn=xmpp.Client(server)#,debug=['socket','dispatcher','roster'])
    conres=conn.connect()
    if not conres:
        print "Unable to connect to server %s!"%server
        sys.exit(1)
    if conres<>'tls':
        print "Warning: unable to estabilish secure connection - TLS failed!"
    authres=conn.auth(user,password)
    if not authres:
        print "Unable to authorize on %s - check login/password."%server
        sys.exit(1)
    if authres<>'sasl':
        print "Warning: unable to perform SASL auth os %s. Old authentication method used!"%server
    conn.RegisterHandler('message',messageCB)
    conn.RegisterHandler('presence', presenceCB)

    #<c xmlns="http://jabber.org/protocol/caps"
    #node="http://mail.google.com/xmpp/client/caps"
    #ver="1.0"
    #ext="voice-v1 video-v1 camera-v1"/>

    caps = xmpp.simplexml.Node(tag='http://jabber.org/protocol/caps c',attrs={'node':'http://mail.google.com/xmpp/client/caps', 'ver':'1.0', 'ext':'camera-v1 video-v1 voice-v1'})
    conn.sendCustomPresence(node=caps)


    dispatch = DispatchThread(conn)
    dispatch.setDaemon(True)
    dispatch.start()

    while 1:
        
            reply = raw_input()
            if reply == '':
                print """Usage:
                            msg jid@hostname msg
                        """
                continue
            elif reply.find(' ')+1:
                command,args=reply.split(' ',1)
            else:
                command,args=reply,''

            if command == 'msg' and args.find(' ')+1:
                recipient,msg = args.split(' ', 1)
                conn.send(xmpp.Message(recipient,msg,'chat'))
            else:
                print "Sorry I don't know that command."
except KeyboardInterrupt:
    print "\nExiting."
    exit(0)
