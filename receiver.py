import socket
import packet
import pickle
import os.path
import sys
import struct


"""The reciever receives packets from the sender via the channel 
and sends acknowledgement packets back through the channel. It writes the
contents of the packets to a file.
For testing the port numbers used are:

r_in : 6000
r_out: 6001

c_r_in: 7002

"""

magicno = 0x497E
ip = 'localhost'
packet_size = 1024


def close_sockets():
    r_in.close()
    r_out.close()


def check_port_number(address):    
    """checks if a port number of an address is valid
       and terminates the program if it is not"""
    port = address[1]
    if (not isinstance( port, int )) or (port < 1024) or (port > 64000):
        sys.exit("Invalid port number: {}\nPort numbers must be integers between 1024 and 64000.".format(port))


# get adresses using ports passed in from the command line
print("Reading port numbers...")

try:
    r_in_address = (ip, int(sys.argv[1])) # incoming from channel
    r_out_address = (ip, int(sys.argv[2])) # outgoing to channel
    c_r_in_address = (ip, int(sys.argv[3])) # outgoing to channel
except:
    sys.exit("Error: 3 port numbers must be supplied.")



# check the ports are valid
print("Checking ports are valid...")

check_port_number(r_in_address)
check_port_number(r_out_address)
check_port_number(c_r_in_address)



# initialise all the sockets
print("Initialising Sockets...")
r_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #6000
r_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #6001

# bind sockets to their ports
print("Binding sockets...")

try:
    r_in.bind(r_in_address)
    r_out.bind(r_out_address)
except:
    close_sockets()
    sys.exit("Error: Cannot bind sockets to the same port.")

# connect the outgoing socket to its destination address
print("Connecting outgoing socket...")
r_out.connect(c_r_in_address)


# read filename from command line argument
print("Reading filename...")
try: 
    filename = sys.argv[4]
except:
    close_sockets()
    sys.exit("Error: A filename must be supplied")


#Check that the filename doesn't already exist
if os.path.isfile(filename):
    close_sockets()
    sys.exit("A file named '{}' already exists. Aborting as a precaution.".format(filename))

# open the file for writing
print("Opening file for writing...")
file = open(filename,'wb')


expected = 0


def validate_packet(packet):
    """Check that a recieved packet is valid"""
    if packet.magicno != magicno:
        return False
    if packet.packet_type != 0:
        return False
    return True   


    
    

def print_packet(packet):
    """prints out a packet for debugging purposes"""
    print("****PACKET****")
    print("Magic no: {}".format(packet.magicno))
    print("Type:     {}".format(packet.packet_type))
    print("Seqno:    {}".format(packet.seqno))
    print("Data len: {}".format(packet.dataLen))
    print("**************")   



#handle incoming packets
print("Listening for incoming packets")
while True:
    
    obj = r_in.recv(packet_size)
    print("Recieved Packet")

    magicno, packet_type, dataLen, seqno = struct.unpack('iiii', obj[:16])
    pack = packet.Packet(magicno, packet_type, dataLen, seqno)
    if validate_packet(pack):
        print_packet(pack)
        
        if pack.seqno != expected:
            # unexpected sequence number
          
            ack = packet.Packet(0x497E, 1, 0, pack.seqno)
            byteAck = struct.pack('iiii', ack.magicno, ack.packet_type, ack.dataLen, ack.seqno)
            
            # send response
            try:
                r_out.send(byteAck)
            except:
                close_sockets()
                sys.exit("Connection failed, channel may be offline.")             
            
        elif pack.seqno == expected:
            # expected sequence number

            ack = packet.Packet(0x497E, 1, 0, pack.seqno)
            byteAck = struct.pack('iiii', pack.magicno, 1, 0, pack.seqno)

            
            # send response
            try:
                r_out.send(byteAck)
            except:
                close_sockets()
                sys.exit("Connection failed, channel may be offline.") 
                
            expected = 1 - expected
            
            # write the data to the file
            if pack.dataLen > 0:
                print("Writing to file")
                file.write(obj[16:])
            elif pack.dataLen == 0:
                file.close()
                close_sockets()
                sys.exit(0)
    else:
        print("Invalid packet")
        
    

            

