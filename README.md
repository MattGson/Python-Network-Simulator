# Python-Network-Simulator
A simple python application to simulate and packet loss and test solutions.

## About
This project is just a simple way to test solutions to, and the effect of, packet loss. This project has three modules. A Sender, a Channel and a Reciever. The modules a linked via Datagram sockets. The channel will drop transmitted packets with a specified probability. The Sender and reciever can be modified to use different Ack strategies.
