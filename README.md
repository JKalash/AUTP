
AUTP. A simple reliable transport protocol. This protocol provides in-order, reliable delivery of UDP datagrams, and does so in the presence of packet loss, delay, corruption, duplication, and re-ordering.


Protocol Description
====================

The protocol has four message types: start, end, data, and ack. The start, end, and data messages all follow the same general format.

```
start|<sequence number>|<data>|<checksum>
data|<sequence number>|<data>|<checksum>
end|<sequence number>|<data>|<checksum>
```

To initiate a connection, send a start message. The receiver will use the sequence number provided as the initial sequence number for all packets in that connection. After sending the start message, send additional packets over the same connection using the data message type, adjusting the sequence number appropriately. Unsurprisingly, the last data in a connection should be transmitted with the end message type to signal the receiver that the transfer is complete.

Senders accept acknowledgements from the receiver in the format:

```
ack|<sequence number>|<checksum>
```

An important limitation is the maximum size of the packets. Since UDP/IP introduces a minimum of 28 Bytes of header, and since Ethernet has a maximum frame size of 1500 Bytes, this leaves 1472 Bytes for the entire packet (message type, sequence number, data, and checksum).

Receiver Specification
=======================

The AUTP receiver responds to data packets with cumulative acknowledgements. Upon receiving a message of type **start**, **data**, or **end**, the receiver generates an **ack** message with the sequence number it expects to receive next, which is the lowest sequence number not yet received.

In other words, if it expects a packet of sequence number N, the following two scenarios may occur:
1. If it receives a packet with sequence number not equal to N, it will send “ack|N”. 2. If it receives a packet with sequence number N, it will check for the highest sequence number (say M) of the in-order packets it has already received and send “ack|M+1”. For example, if it has already received packets N+1 and N+2 (i.e. M = N+2), but no others past N+2, then it will send “ack|N+3”.

Let’s illustrate this with an example. Suppose packets 0, 1, and 2 are sent, but packet 1 is lost before reaching the receiver. The receiver will send “ack |1” upon receiving packet 0, and then “ack |1” again upon receiving packet 2. As soon as the receiver receives packet 1 (due to retransmission from the sender), it will send “ack |3” (as it already has received 2), and upon receiving this acknowledgement the sender can assume all three packets were successfully received.If the next expected packet is N, the receiver will drop all packets with sequence number greater than N+4; that is, the receiver operates with a window size of five packets, and drops all packets that fall outside of that range. When the next unexpected packet is N+1 (due to N arriving), then the receiver will accept packet N+5.
We assume that once a packet has been acknowledged by the sender, it has been properly received. The receiver has a default timeout of 10 seconds; it will automatically close any connections for which it does not receive packets for that duration.

Sender Specification
====================

The sender reads an input file and transmit it to a specified receiver using UDP sockets. It splits the input file into appropriately sized chunks of data, specify an initial sequence number for the connection, and append a checksum to each packet. The sequence number increments by one for each additional packet in a connection. Functions for generating and validating packet checksums are provided in Checksum.py.
The sender implements a sliding windows algorithm. The receiver window size is five packets. Your sender accepts **ack** packets from the receiver. Any ack packets with an invalid checksum is ignored.

Sender provides reliable service under the following network conditions:

• Loss: arbitrary levels; you should be able to handle periods of 100% packet loss.• Corruption: arbitrary types and frequency.• Re-ordering: may arrive in any order, and• Duplication: you could see a packet any number of times.• Delay: packets may be delayed indefinitely (but generally not more than 10 secs).

**Invoking the sender:**

```
python Sender.py -f <input file> -a <destination address> -p <port>```

Some final notes about the sender:• The sender implements a 500 ms retransmission timer to automatically retransmit packets that were never acknowledged (potentially due to ack packets being lost). Adaptive timeouts are employed.• The sender supports a window size of five packets (i.e., 5 unacknowledged packets).• The sender roughly meets or exceeds the performance (in both time and number of packets required to complete a transfer) of a properly implemented sliding- windows-based AUTP sender.• The sender is able to handle arbitrary message data (i.e., it is able to send an image (binary) file just as easily as a ASCII text file). If no input file is provided, sender reads read input from STDIN.• Any packets received with an invalid checksum are ignored.

