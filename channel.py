import socket
import random
import sys
import pickle
import select
import struct
import packet

"""The channel relays packets from sender to receiver and vice versa with
a packet loss probability. Port numbers are taken from the command line.
For testing the port numbers used are:

c_s_in : 7000
c_s_out: 7001
c_r_in : 7002
c_r_out: 7003

s_in : 5000
r_in : 6000
"""

magicno = 0x497E
packet_size = 1024
ip = 'localhost'


def close_sockets():
    c_s_in.close()
    c_s_out.close()
    c_r_in.close()
    c_r_out.close()  

def check_port_number(address):    
    """checks if a port number of an address is valid
       and terminates the program if it is not"""
    port = address[1]
    if (not isinstance( port, int )) or (port < 1024) or (port > 64000):
        sys.exit("Invalid port number: {}\nPort numbers must be integers between 1024 and 64000.".format(port))


# get adresses using ports passed in from the command line
print("Reading port numbers...")

try:
    c_s_in_address = (ip, int(sys.argv[1])) #incoming from sender
    c_s_out_address = (ip, int(sys.argv[2])) #outgoing to sender
    c_r_in_address = (ip, int(sys.argv[3])) #incoming from reciever
    c_r_out_address = (ip, int(sys.argv[4])) #outgoing to reciever

    s_in_address = (ip, int(sys.argv[5])) #outgoing to sender
    r_in_address = (ip, int(sys.argv[6])) #outgoing to reciever
except:
    sys.exit("Error: 6 port numbers must be supplied.")


# check the ports are valid
print("Checking port numbers...")
check_port_number(c_s_in_address)
check_port_number(c_s_out_address)
check_port_number(c_r_in_address)
check_port_number(c_r_out_address)
check_port_number(s_in_address)
check_port_number(r_in_address)


# initialise all the sockets
print("Initialising Sockets...")
c_s_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #7000
c_s_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #7001
c_r_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #7002
c_r_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #7003

# bind the sockets to their ports
print("Binding sockets...")

try:
    c_s_in.bind(c_s_in_address)
    c_s_out.bind(c_s_out_address)
    c_r_in.bind(c_r_in_address)
    c_r_out.bind(c_r_out_address)
except:
    close_sockets()
    sys.exit("Error: Cannot bind sockets to the same port.")
    
    
# connect the outgoing sockets to their corresponding addresses
# at the sender and reciever
print("Connecting outgoing sockets...")
c_s_out.connect(s_in_address)
c_r_out.connect(r_in_address)




# Set the packet loss rate from command line argument
print("Reading Probability...")

try:
    packet_loss_rate = float(sys.argv[7])
except:
    close_sockets()
    sys.exit("Error: A probability must be supplied.")
    
if packet_loss_rate >= 1 or packet_loss_rate < 0:
    close_sockets()
    sys.exit("Invalid probability: {}\nProbability must be bewteen 0 and 1".format(packet_loss_rate))



def lose_packet():
    """randomly decides if a packet is lost"""
    randnum = random.random() % 1
    if randnum < packet_loss_rate:
        return True
    else:
        return False


def validate_packet(packet):
    """Check that a recieved packet is valid"""
    if packet.magicno != magicno:
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
    
  


listening = [c_s_in, c_r_in] # the sockets to listen on

# listen for incoming packets to relay
print("Listening for packets...") 
while True:
   
    # find which sockets have data waiting to be received
    ready, a, b = select.select(listening, [], [])
    
    for soc in ready:
        
        if soc == c_s_in:
            # packet recieved from sender
            print("Packet recieved from sender")
            
            obj = soc.recv(packet_size)
            magicno, packet_type, dataLen, seqno = struct.unpack('iiii', obj[:16])
            pack = packet.Packet(magicno, packet_type, dataLen, seqno)
            
            if validate_packet(pack):
                print_packet(pack)
                
                if not lose_packet():
                    #relay the packet to receiver
                    print("Relaying to reciever")
                    
                    try:
                        c_r_out.send(obj)
                    except:
                        close_sockets()
                        sys.exit("Connection failed, reciever may be offline.")
                else:
                    #drop the packet
                    print("Losing packet")
            else:
                print("Invalid packet")
                
        elif soc == c_r_in:
             # packet recieved from reciever
            print("Packet recieved from receiver")            
            
            obj = soc.recv(packet_size)
            magicno, packet_type, dataLen, seqno = struct.unpack('iiii', obj[:16])
            pack = packet.Packet(magicno, packet_type, dataLen, seqno)
            
            if validate_packet(pack):
                print_packet(pack)
                
                if not lose_packet():
                    #relay the packet to sender
                    print("Relaying to sender")
        
                    try:
                        c_s_out.send(obj)
                    except:
                        close_sockets()
                        sys.exit("Connection failed, sender may be offline.")                     
                else:
                    #drop the packet
                    print("Losing packet")
            else:
                print("Invalid packet")    
        
        else:
            print("Invalid socket")
        
