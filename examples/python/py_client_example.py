#!/usr/bin/env python
"""
    developer: Iason Batzianoulis
    maintaner: Iason Batzianoulis
    email: iasonbatz@gmail.com
    description: 
    This scripts is an example on how to use the socketStream server for listening to inputs from a client
"""

import argparse
import numpy as np
from socketStream_py import socketStream


def main(args):
    sockClient = socketStream.socketStream(svrIP = args.host, svrPort = args.port, socketStreamMode = 0)

    sockClient.set_clientName("py_example")

    sockClient.initialize_msgStruct(["name","data"])

    sockClient.updateMSG("name","Mary")

    sockClient.updateMSG("data", [[2.4,5.6,783.01],[34,55.6,1.2]])

    everything_ok = False
    if sockClient.initialize_socketStream() == 0:
        if sockClient.make_connection() == 0:
            everything_ok = True

    if everything_ok:
        sockClient.sendMsg()
    
    sockClient.closeCommunication()




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TCP server for receiving inputs from a client with socketStream')
    parser.add_argument('--host', type=str, help= 'the IP of the server', default='localhost')
    parser.add_argument('--port', type=int, help= 'the port on which the server is listening', default=10352)
    parser.add_argument('--buffersize', type=int, help= 'the size of the buffer for pakets receiving', default=16)
    args=parser.parse_args()
    main(args)