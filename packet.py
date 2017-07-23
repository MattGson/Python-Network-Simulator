class Packet(object):
    """Packet class containing 
    - a magic number magicno = 0x497E
    - a type, 0 = dataPacket, 1 = acknowledgementPacket
    - a seqno, an int 0 or 1
    - datalen, an int 0 - 512, number of user databytes in packet, 0 for acknowledgement packets
    - data, the actual user data, length indicated by datalen"""
    
    def __init__(self, magicno, packet_type, datalen, seqno):
        self.magicno = magicno
        self.packet_type = packet_type
        self.seqno = seqno
        self.dataLen = datalen


        
    