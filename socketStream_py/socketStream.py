#!/usr/bin/env python
"""
	developer: Iason Batzianoulis
	maintaner: Iason Batzianoulis
	email: iasonbatz@gmail.com
	description: 
	This scripts defines a class that handles a TCP/IP server for listening to inputs from a client
"""

# import standard modules 
import numpy as np
import argparse
import hashlib
import random
import string

# import modules for socket programming (TCP/IP connection)
import socket
import sys
import json

# import modules for theading programming
import threading
import time

class socketStream():
    def __init__ (self, IPaddress = 'localhost', port = 10352, bufferSize = 128):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the port
        self.server_address = (IPaddress, port)

        print('starting up on %s port %s' % self.server_address)

        self.sock.bind(self.server_address)

        # define buffer size
        self.BUFFER_SIZE = bufferSize

        # define a header size of the message
        self.HEADERSIZE = 8

        # define message identifier
        self.msg_idf = "!&?5"

        # end-of-message identifier
        self.endMSG = "!3tt"

        # end-connection identifier
        self.ec_id = "\ne@c"

        # listen for new connections
        self.sock.listen(1)

        self.bfrDigits = len(str(self.BUFFER_SIZE))
        self.msg_idf_len = len(self.msg_idf)

        self.serverRunnig = True

        self.connection_exist = False

        self.serverThread = threading.Thread(target = self.wait_connections, args = ())
        self.serverThread.daemon = True
        self.serverThread.start()

        self.hc_check=hashlib.md5()

        self.msg_data = {}

        # self.numberofConnections = 0
        # self.sConnections = []
        # self.clientAdresses = []
        # self.receiverThreads = []

        self.ReceiverThread = threading.Thread(target=self.runReceiver, args = ())
        self.ReceiverThread.daemon = True
        # self.thread.start()


        self.lock = threading.Lock()
        self.firstValueReceived = False

    def msgExtractor(self, msg):
        msgSize=int(msg[:self.HEADERSIZE])
        msgOverhead = int(msg[self.HEADERSIZE+1:self.HEADERSIZE+1+self.bfrDigits])
        tmp_msg=msg[self.HEADERSIZE+1+self.bfrDigits:self.HEADERSIZE+1+self.bfrDigits+msgSize]
        if(msg[self.HEADERSIZE+1]==1):
            hashcode=msg[self.HEADERSIZE+msgSize:-msgOverhead-len(self.endMSG)]
            self.hc_check.update(tmp_msg)
            if self.hc_check.hexdigest()==hashcode:
                return True, tmp_msg
            else:
                return False, ''
        else:
            return True, tmp_msg

    def randomString(self, strlength=10):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(strlength))

    def handShake(self,conn, strlength):
    
        ping_times=np.empty([10,1], dtype=np.float64)
        compute_times=np.empty([10,1], dtype=np.float64)
        validity_counter=np.empty([10,1], dtype=bool)
        HEADERSIZE=4
        t_time0=0.0

        # receive and send random msgs to the client 10 times
        for i in range(10):
            msg_full=''
            while (True):
                dataT=conn.recv(4)
                msg_full+=dataT
                if msg_full[-4:].decode('utf-8')==self.endMSG:
                    break

            if t_time0!=0.0:
                ping_times[i-1]=time.time()-t_time0
            t_time=time.time()
            msg_validity, tr_msg = self.msgExtractor(msg_full,HEADERSIZE,self.endMSG)
            validity_counter[i]=msg_validity

            dcdr=hashlib.md5()
            test_msg=self.randomString(strlength)
            dcdr.update(test_msg)
            chSum=dcdr.hexdigest()
            msg_len=('{:<'+str(HEADERSIZE)+'}').format(str(sys.getsizeof(test_msg)))
            compute_times[i]=time.time()-t_time
            conn.sendall(msg_len.encode('utf-8')+(test_msg).encode('utf-8')+chSum.encode('utf-8')+self.endMSG.encode('utf-8'))
            t_time0=time.time()

        if((1*(validity_counter)).mean()>0.8):
            print('[socketStream] Valid communication established')
            print('[socketStream] Compute times: %s %s %s s' %(compute_times.mean(), u'\u00b1', compute_times.std()))
            print('[socketStream] Ping times:  %s %s %s s' %(ping_times[:9].mean(), u'\u00b1', ping_times[:9].std()))
            return True
        else:
            print('[socketStream] Communication is not valid')
            return False

    def run(self):
        print('waiting for a connections ... ')
        counter = 0
        while(not self.connection_exist):
            # print(counter)
            counter +=1
            try:
                # check if any connection inquire exists and accept it

                self.connection, self.client_address = self.sock.accept()
                self.connection_exist = True
                print('[socketStream] Connection from ', self.client_address)

                counter = 0;
                while(True):
                # retrieve the message identifier. once it is received, compose the message
                    data=self.connection.recv(self.BUFFER_SIZE)
                    data_check = data[:self.msg_idf_len]
                    counter+=1
                    print("messages received",counter)
                    if data_check.decode('utf-8')==self.msg_idf:
                        # receive bytes until the full message is received
                        full_msg=data[self.msg_idf_len:].decode("utf-8")
                        while (True):
                            dataT=self.connection.recv(self.BUFFER_SIZE)
                            full_msg+=dataT.decode("utf-8") 
                            if full_msg[-4:]==self.endMSG:
                                break

                        # extract message
                        msg_validity, tr_msg = self.msgExtractor(full_msg)
                        if msg_validity:
                            self.msg_data=json.loads(tr_msg)
                            # print(self.msg_data.get("name"))

                    if  data_check.decode('utf-8')==self.ec_id:
                        # if end-of-communication identifier received, terminate the connection
                        print('[socketStream] Connection terminated by client ', self.client_address)
                        self.connection.close()
                        self.connection_exist = False
                        break

            # except socket.timeout as e:
            # 	print("socket timeout. retry")
            # 	pass
            except KeyboardInterrupt:
                # if Ctrl+C is pressed in the keyboard, close the connections (if any) and exit
                if self.connection_exist:
                    self.connection.close()
                    self.connection_exist = False
                break
            finally:
                pass
                # print('Waiting for new clients ....')
        print("exit")
        
    def close_communication(self):
        # close communications
        if self.connection_exist:
            self.connection.close()
            self.connection_exist = False
        self.sock.close()
        print('[socketStream] All connections killed')

    def runReceiver(self):
        counter=0
        while(self.connection_exist):
            try:
                # retrieve the message identifier. once it is received, compose the message
                data=self.connection.recv(self.BUFFER_SIZE)
                data_check = data[:self.msg_idf_len]
                counter+=1
                # print("messages received",counter)
                if data_check.decode('utf-8')==self.msg_idf:
                    # receive bytes until the full message is received
                    full_msg=data[self.msg_idf_len:].decode("utf-8")
                    while (True):
                        dataT=self.connection.recv(self.BUFFER_SIZE)
                        full_msg+=dataT.decode("utf-8") 
                        if full_msg[-4:]==self.endMSG:
                            break

                    # extract message
                    msg_validity, tr_msg = self.msgExtractor(full_msg)
                    if msg_validity:
                        self.msg_data=json.loads(tr_msg)
                        if not self.firstValueReceived:
                            self.firstValueReceived = True

                if  data_check.decode('utf-8')==self.ec_id:
                    # if end-of-communication identifier received, terminate the connection
                    print('[socketStream] Connection terminated by client ', self.client_address)
                    self.connection.close()
                    self.connection_exist = False
                    self.firstValueReceived = False
                    break
            except KeyboardInterrupt:
                if self.connection_exist:
                    self.connection.close()
                    self.connection_exist = False
                break
            

    def get_latest(self):
        self.lock.acquire()
        trace = self.msg_data
        self.lock.release()
        return trace

    def isClientConnected(self):
        return self.connection_exist

    def isFirstMsgReceived(self):
        return self.firstValueReceived

    def isServerRunning(self):
        return self.serverRunnig

    def sockectStream_ok(self):
        return (self.serverRunnig and self.connection_exist and self.firstValueReceived)

    def set_data(self, msg):
        self.msg_data = msg

    def start_receiveing(self):
        self.ReceiverThread.start()

    def wait_connections(self):
        print('[socketStream] Waiting for connections ... ')
        counter = 0
        while(self.serverRunnig):
            # check if any connection inquire exists and accept it
            self.connection, self.client_address = self.sock.accept()
            print('[socketStream] Connection from ', self.client_address)
            testThrd = threading.Thread(target=self.runReceiver, args = ())
            testThrd.daemon = True
            self.connection_exist = True
            testThrd.start()
            testThrd.join()
    
    
                
            # except KeyboardInterrupt:
            #     # if Ctrl+C is pressed in the keyboard, close the connections (if any) and exit
            #     if self.connection_exist:
            #         self.connection.close()
            #         self.connection_exist = False
            #         self.serverRunnig = False
            #     self.close_communication()
            #     break
            # finally:
            #     if not self.connection_exist:
            #         print('waiting for connections ... ')
            #     pass


    # def wait_connections(self):
    #     print('waiting for connections ... ')
    #     counter = 0
    #     while(self.serverRunnig):
    #         # print(counter)
    #         counter +=1
    #         try:
    #             # check if any connection inquire exists and accept it
    #             self.connection, self.client_address = self.sock.accept()
    #             print('connection from ', self.client_address)
    #             testThrd = threading.Thread(target=self.runReceiver, args = ())
    #             testThrd.daemon = True
    #             self.connection_exist = True
    #             testThrd.start()
    #             testThrd.join()
    #             # self.ReceiverThread.start()
                
                
    #         except KeyboardInterrupt:
    #             # if Ctrl+C is pressed in the keyboard, close the connections (if any) and exit
    #             if self.connection_exist:
    #                 self.connection.close()
    #                 self.connection_exist = False
    #                 self.serverRunnig = False
    #             self.close_communication()
    #             break
    #         finally:
    #             if not self.connection_exist:
    #                 print('waiting for connections ... ')
    #             pass