import socket
import packet
import pickle
import select
import os.path
import sys
import struct



"""The sender reads data from a file in blocks of up to 512 bytes. It creates
a packet for each block and sends it to the reciever via the channel and waits
for a response from the reciever for 1 second. After timeout the packet is
retransmitted. This is repeated until the receiver has recieved all packets
For testing, the port numbers used are:

s_in : 5000
s_out: 5001

c_s_in: 7000

"""

magicno = 0x497E
ip = 'localhost'
packet_size = 1024

def close_sockets():
    s_in.close()
    s_out.close()


def print_packet(packet):
    """prints out a packet for debugging purposes"""
    print("****PACKET****")
    print("Magic no: {}".format(packet.magicno))
    print("Type:     {}".format(packet.packet_type))
    print("Seqno:    {}".format(packet.seqno))
    print("Data len: {}".format(packet.dataLen))
    print("**************")
    

def check_port_number(address):    
    """checks if a port number of an address is valid
       and terminates the program if it is not"""
    port = address[1]
    if (not isinstance( port, int )) or (port < 1024) or (port > 64000):
        sys.exit("Invalid port number: {}\nPort numbers must be integers between 1024 and 64000.".format(port))


# get ports passed in from the command line
print("Reading port numbers...")

try:
    s_in_address = (ip, int(sys.argv[1])) # incoming from channel
    s_out_address = (ip, int(sys.argv[2])) # outgoing to channel
    c_s_in_address = (ip, int(sys.argv[3])) # outgoing to channel
except:
    sys.exit("Error: 3 port numbers must be supplied.")



# check the ports are valid
print("Checking ports are valid...")
check_port_number(s_in_address)
check_port_number(s_out_address)
check_port_number(c_s_in_address)


# initialise all the sockets
print("Initialising Sockets...")
s_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
s_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   

# bind sockets to their ports
print("Binding sockets...")

try:
    s_in.bind(s_in_address)
    s_out.bind(s_out_address)
except:
    close_sockets()
    sys.exit("Error: Cannot bind sockets to the same port.")

# connect the outgoing socket to its destination address
print("Connecting outgoing socket...")
s_out.connect(c_s_in_address)


# read filename from command line argument
print("Reading filename...")
try: 
    filename = sys.argv[4]
except:
    close_sockets()
    sys.exit("Error: A filename must be supplied")

#Check that the file exists
if not os.path.isfile(filename):
    close_sockets()
    sys.exit("Error: File not found '{}'".format(filename))

#open file for reading bytes
file = open(filename, 'rb')

sent = 0
_next = 0
exit_flag = False



def validate_packet(packet):
    """Check that a recieved packet is valid"""
    if packet.magicno != magicno:
        return False
    if packet.packet_type != 1:
        return False
    if packet.dataLen != 0:
        return False
    if packet.seqno != _next:
        return False
    return True   




print("Beginning transmission...")

while not exit_flag:
    
    
    #read up to 512 bytes
    data = file.read(512)
    #data = data.decode("utf-8")
    
    packet_buffer = None
    
    if len(data) == 0:

        #reached end of file
        
        pack = packet.Packet(0x497E, 0, 0, _next)

        exit_flag = True

        
    else:
    
        pack = packet.Packet(0x497E, 0, len(data), _next)

    bytePack = struct.pack('iiii', pack.magicno, pack.packet_type, pack.dataLen, pack.seqno)
    packet_buffer = bytePack + data
    while True:

        #send the packet
        
        try:
            print("Sending packet")
            s_out.send(packet_buffer)
            sent += 1
        except:
            file.close()
            close_sockets()
            print("Connection failed, channel may be offline.")
            sys.exit("Total packet transmissions: {}".format(sent))

        #wait up to 1 second for a response
        ready = select.select([s_in], [], [], 1.0)
        
     
        if ready[0]:
            
            #response recieved
            data = s_in.recv(packet_size)
            magicno, packet_type, dataLen, seqno = struct.unpack('iiii', data[:16])
            pack = packet.Packet(magicno, packet_type, dataLen, seqno)
            print("Packet received")
            print_packet(pack)
            if not validate_packet(pack):
                #response packet is invalid, try again
        
                continue
            else:

                _next = 1 - _next
                if exit_flag == True:
                    #all packets have been received
                    file.close()
                    close_sockets()
                    sys.exit("All packets transmitted.\nTotal packet transmissions: {}".format(sent))
                else:
                    #next packet
                    break
            
            
        else:
            #timeout, try again
            print("Timeout")
            
        