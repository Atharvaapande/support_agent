# Computer Network

### HTTP/HTTPS \- 

1. HTTP is the hyper text transfer protocol, it is the protocol used by the client browser to communicate with the server in the plain text, this HTTP is vulnerable to the middle man attack and is not secure because it communicates in plain text.  
     
2. HTTPS is the hyper text transfer protocol secure, it is the same as HTTP just with an additional secure layer, these help us to encrypt the communication to avoid the man in the middle attacks.

### Types of encryption \-

1. Symmetric encryption \- in this there is only one public key which is used to encrypt the data and decrypt the data, so during the handshake this key can be accessed by the hacker and the communication can be breached.  
2. Asymmetric encryption \- in this there are two keys involved to encrypt and decrypt the data, one is public key which is transferred over the network so that the client can use it to encrypt the data he is sending to the server, and the server user the another key private key to decrypt this received data, once the data is encrypted using the public key it can only be decrypted using the private key and nothing else.

### UDP

1. UDP is a user datagram protocol, which is mostly used in real time applications like game, live streaming.  
2. UDP have less header than TCP and don’t have retransmission for lost data  
3. UDP header is very simple and contains \- source IP 16 bits, destination IP 16 bits, length (data \+ header) 16 bits, checksum length 16 bits total of 8 bytes   
4. It is also in the transport layer

### 

### 

### 

### TCP/IP – Transmission Control Protocol / Internet Protocol 20 bytes header

1. **TCP responsibilities**  
   * TCP ensures reliable and ordered delivery of data between applications.  
   * It detects lost or corrupted data and can retransmit missing data.  
   * It provides flow control and congestion control.  
   * IP handles addressing and routing packets to their destination.  
2. **TCP Three-Way Handshake**  
   * Client → Server: Client sends SYN with SEQ \= x.  
   * Server → Client: Server sends SYN \+ ACK with SEQ \= y, ACK \= x \+ 1\.  
   * Client → Server: Client sends ACK with SEQ \= x \+ 1, ACK \= y \+ 1\.  
3. **Sequence Number (SEQ) and Acknowledgment Number (ACK)**  
   * SEQ identifies the byte position of the first data byte in a TCP segment.  
   * ACK indicates the next byte expected from the other side.  
   * TCP maintains independent sequence number spaces for each direction.  
   * SYN and FIN each consume one sequence number. ACK does not consume one.  
4. **Example of TCP Data Transfer**  
   Initial handshake:  
   * Client: SEQ \= 100\.  
   * Server: SEQ \= 500, ACK \= 101\.  
   * Client: SEQ \= 101, ACK \= 501\.  
5. Client sends data:  
   * Segment 1: SEQ \= 101, ACK \= 501, data \= 101–200.  
   * Segment 2: SEQ \= 201, ACK \= 501, data \= 201–300.  
   * Segment 3: SEQ \= 301, ACK \= 501, data \= 301–400.  
6. Server acknowledges:  
   * SEQ \= 501, ACK \= 401\.  
7. Server sends data:  
   * Segment 1: SEQ \= 501, ACK \= 401, data \= 501–600.  
   * Segment 2: SEQ \= 601, ACK \= 401, data \= 601–700.  
8. Client acknowledges:  
   * SEQ \= 401, ACK \= 701\.  
9. **TCP Retransmission**  
   * If a segment is lost, the receiver continues acknowledging the first missing byte.  
   * Duplicate ACKs can trigger Fast Retransmit (commonly after three duplicate ACKs).  
   * If Fast Retransmit does not occur, a retransmission timeout (RTO) can trigger retransmission.  
   * TCP can buffer out-of-order segments and deliver the byte stream to the application in order.  
10. IP is an internet protocol, which simply defines the source and destination while communication, it tells where to send the data.

### SSL (Secure Sockets Layer)

SSL stands for **Secure Sockets Layer**. It is an obsolete cryptographic protocol originally developed to secure communication over networks by providing encryption, authentication and data integrity.

SSL was replaced by TLS (Transport Layer Security), which is the modern protocol used to secure HTTPS communication.

**Historical SSL 3.0 handshake (RSA key transport):**

1. Client sends a `ClientHello` message containing supported protocol versions, cipher suites and a random value.  
2. Server responds with `ServerHello` and its digital certificate.  
3. Client validates the server's certificate by checking:  
   * Domain name.  
   * Certificate validity period.  
   * Certificate chain leading to a trusted Root CA.  
   * Certificate signatures.  
4. In the historical RSA key-transport method, the client generates a pre-master secret and encrypts it using the server's public key.  
5. The server decrypts the pre-master secret using its private key.  
6. Both client and server independently derive matching symmetric session keys using the pre-master secret and handshake random values.  
7. Both sides exchange Finished messages and begin encrypted communication.

**Note:** This describes a historical SSL 3.0 handshake using RSA key transport. Modern TLS 1.3 generally uses ephemeral Diffie-Hellman (ECDHE) instead.

### 

### Modern TLS 1.3 with ECDHE:

1. Client sends `ClientHello` with supported versions, cipher suites and an ephemeral ECDHE public key share.  
2. Server responds with `ServerHello` and its own ephemeral ECDHE public key share.  
3. Server sends its certificate and proves possession of its certificate's private key through `CertificateVerify`.  
4. Client validates the server certificate and verifies the handshake messages.  
5. Both sides combine their own ephemeral private key with the peer's public key share to independently derive matching shared secret material.  
6. Both derive symmetric encryption keys using HKDF.  
7. They exchange Finished messages to verify the handshake.  
8. Encrypted application data communication begins.

### DNS Resolution (Domain Name System)

DNS resolution is the process of converting a human-readable domain name into an IP address so that a device can communicate with the destination server.

![][image1]

**Example:** `google.com` → IP address.

**Components involved:**

1. **DNS Resolver:** Receives the DNS query from the client and finds the requested record.  
2. **Root DNS Server:** Directs the resolver towards the appropriate TLD nameserver.  
3. **TLD DNS Server:** Directs the resolver towards the authoritative nameserver for the domain.  
4. **Authoritative DNS Server:** Provides the actual DNS record for the requested domain.

**DNS resolution process:**

1. User enters a domain name in the browser.  
2. Browser and operating system check their DNS caches and local hosts file.  
3. If no valid answer exists, the device sends a DNS query to its recursive resolver.  
4. The recursive resolver checks its cache.  
5. If there is a cache miss, it queries a Root DNS server.  
6. Root DNS server refers it to the appropriate TLD server.  
7. TLD server refers it to the domain's authoritative nameserver.  
8. Authoritative DNS server returns the requested DNS record, such as an A record containing an IPv4 address.  
9. Recursive resolver caches the response according to its TTL and returns it to the client.  
10. The browser can now use the IP address to establish a connection with the destination server.

**Important DNS record types:**

* A: IPv4 address.  
* AAAA: IPv6 address.  
* CNAME: Alias of another domain.  
* MX: Mail server.  
* NS: Authoritative nameserver.  
* TXT: Text information.

**DNS transport protocols:**

* UDP port 53: Common DNS queries.  
* TCP port 53: Truncated responses and zone transfers.  
* DoT: DNS over TLS.  
* DoH: DNS over HTTPS.

**DNS caching:** DNS records are cached to reduce repeated lookups. TTL (Time To Live) determines how long a record can be cached.

### REST APIs

REST stands for representational state transfer, it is the set of rules for communication over internet.

It have \- GET, PUT, POST, Delete  
And have status code like \-  
![][image2]

### Bandwidth, latency and throughput

Bandwidth defines the capacity of the network, it tell max data that can be transfer over internet per unit time

Throughput defines the actual data being transferred over the internet per unit time

Latency is the time taken to transfer that data from source to destination. Measured in ms

Round trip time is the time taken for the data to travel from source to destination and back to source