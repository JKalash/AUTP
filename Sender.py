import sys
import getopt

import Checksum
import BasicSender

class Sender(BasicSender.BasicSender):
    
    
    packets = [None] * 5                    #Allocate an array of size 5 to serve as the fixed window
    packetsfilled = 0                       #track the number of packets created and inserted in the window
    seqno =0                                #Unique sequence number for every packet
    msg_type =""                            #Type of the packet to be sent
    
    def __init__(self, dest, port, filename, debug=False):
        super(Sender, self).__init__(dest, port, filename, debug)
            
    # Main sending loop.
    def start(self):
        global packets
        global packetsfilled 
        global msg_type
        global seqno
        
        packets = [None] * 5                #Re-initialize variables
        packetsfilled = 0                   ##
        seqno =0                            ##
        msg_type =""                        ##
        
        while not msg_type == 'end':        #Loop until the last packet sent is of type 'end' where the transfer would be complete
            
            #Use Helper method described below to 
            #Create the necessary packets and fill them into the array servin
            #as our windo...
            self.fill_array()
            
            
            #Everytime we immediately send all 5 packets
            #Since this is an implementation of the sliding window
            #Again, we use a helper method implemented & described below for that                                           
            self.send_packets_from_to(frm=0, to=packetsfilled)  
            
            
            completedWindow = False                                             #Keep track of when the WINDOW transfer is complete
            while not completedWindow == True:                                  #Keep on checking until entire window is successfully sent
            
                received_acks = [None] * 5                                      #Allocate space for 5 Messages to analyze
                for x in range (0, packetsfilled):                              #Call the receive with default timeout of 500msec
                    received_acks[x]= self.receive(timeout=0.5)                 #and do so to all packets and save answer in an array
                
                if msg_type == 'end':                                           #Check for end message where the transfer would be complete
                    print "Transfer Complete!"
                    break
                    
                    ################################################################################################
                    #### The technique adopted here is Go-Back-N. The procedure is to parse our acks and check  ####
                    #### their sequence number to see if there is any abnormality in the received acks. Then we ####
                    #### try to resolve the abnormality into an error and deal with the problem according to    ####
                    ####             what is supposed to be done in a regular Go-Back-N algorithm               ####
                    ################################################################################################
                
                #Parse our received acks using a helper method implemented below
                #to simplify the analysis of errors
                self.parse_acks(acks=received_acks)                             
                
                #Keep track of an error occurred
                #Trick here used is to encore the ERROR+location of the error
                #into an integer that would then be used here to attempt to 
                #resolve the error 
                error = self.check_for_error(acks = received_acks)  
                            
                if not error == -1:                                             # -1 encodes a NO ERROR
                    print "ERROR!"
                    if error < 10:  
                        
                        #Error resolved into a timeout
                        #We re-send all packets inside the window whose index is equal to or greater
                        #than the index of the occurred timeout     
                        print "Resolved into timeout"
                        self.send_packets_from_to(frm = error, to = packetsfilled)
                    else:
                        
                        #Error resolved into a duplicated ACK
                        #We re-send all packets inside the window whose index is equal to or greater
                        #then the index of the occurred duplicate
                        index = error - 10                                                      # De-code the error to fetch the index
                        print "Resolved into duplicate is at index %d" % index
                        if not int(received_acks[index])==seqno:                                #Make sure the duplicate is not on a normally expected message
                            self.send_packets_from_to(frm = error-10, to = packetsfilled)
                        else:
                            
                            #No error occurred, Consequently we can safely
                            #Conclude that the entire window was normally sent
                            completedWindow = True
                elif self.completed_window(acks = received_acks) == True:
                    completedWindow = True
            
        self.infile.close()
        
        
    #Helper Method 1: A function that checks AND encodes any found
    #abnormality into an error that it returns
    #We encode a timeout into a direct integer indicating the location of the timout 
    #We encode a duplicate into an integer indicating the location of the timout with an OFFSET OF 10
    def check_for_error(self, acks=[]):
        for i in range(4):
            if acks[i] is None:
                return i
            elif acks[i+1] is None:
                return i+1
            else:
                first = int(acks[i])
                second = int(acks[i+1])
                if(first == second):
                    return 10+i
        return -1
    
    
    #Helper Method 2: A function that returns true IFF no 
    #element of the array is of NoneType
    #used to make the algorithm faster
    def completed_window(self, acks = []):
        for i in range(5):
            if acks[i] == None:
                return False
        return True


    #Helper Method 3: A function that replaces every RAW
    #ack in the array of acks into a string containing the only
    #element of interest in our ack: its sequence number
    def parse_acks(self, acks=[]):
        for i in range(5):
            if(acks[i] is not None):
                msg_type, acknb, data, checksum  = self.split_packet(message = acks[i])
                acks[i] = acknb 
            
    #Helper Method 4: A function that reads from the file of interest
    #and creates 5 packets that is adds into the window after clearing it.
    #it also notifies our main function of the number of packetsfilled, the reached
    #sequence number as well as the last message type added in the array
    def fill_array(self):
        global packets
        global msg_type
        global seqno
        global packetsfilled
        
        
        packetsfilled = 0       #Reset packets filled
        packets = [None] * 5    #Empty the window
        #LOOP and create 5 packets and add them to the window
        for x in range (0, 5):
            if msg_type == 'end':                                   #Handle the end of the file where we do not require 5 packets to finish the file
                break
            msg = self.infile.read(1450)                            #Fill the packet with maximal payload
            msg_type = 'data'
            if seqno == 0:                                          #Adjust the message type depending on the sequence
                msg_type = 'start'
            elif msg == "":
                msg_type = 'end'
            packet = self.make_packet(msg_type,seqno,msg)           #Create the Packet  
            packets[x] = packet                                     #Add it to the array and increment the values
            seqno += 1                                              ##
            packetsfilled += 1                                      ##

   #Helper Method 5: A function that takes our window
   #and sends all packets whose index is included between
   #the 'frm' to the 'to' indexes
    def send_packets_from_to(self, frm, to):
        global packets
        for i in range (frm, to):
            msg_type, s, data, checksum  = self.split_packet(message = packets[i])
            self.send(packets[i])
   
    def log(self, msg):
        if self.debug:
            print msg

'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "AUTP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:d", ["file=", "port=", "address=", "debug="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True

    s = Sender(dest,port,filename,debug)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
