#include <stdio.h>
#include <stdlib.h>

#include <unistd.h>
#include <string.h>
#include <netdb.h>
#include <netinet/in.h>

#include <arpa/inet.h>

#define MAXDATASIZE 256 // max number of bytes we can get at once 

// get sockaddr, IPv4:
void *get_in_addr(struct sockaddr *sa)
{
    return &(((struct sockaddr_in*)sa)->sin_addr);
}

int main(int argc, char *argv[])
{
    int sockfd, numbytes;  
    char buf[MAXDATASIZE];
    struct addrinfo hints, *servinfo;
    char s[INET_ADDRSTRLEN];

    if (argc < 3) {
        fprintf(stderr,"usage: %s hostname port\n", argv[0]);
        return 1;
    }

    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

	int rv = getaddrinfo(argv[1], argv[2], &hints, &servinfo);
    if (rv != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv));
        return 1;
    }

    if (servinfo == NULL) {
        fprintf(stderr, "ERROR connection failed\n");
        return 1;
    }

	sockfd = socket(servinfo->ai_family, servinfo->ai_socktype, servinfo->ai_protocol);
    if (sockfd == -1) {
        perror("ERROR opening socket");
        return 1;
    }

    if (connect(sockfd, servinfo->ai_addr, servinfo->ai_addrlen) == -1) {
        close(sockfd);
        perror("ERROR connection failed");
        return 1;
    }

    inet_ntop(servinfo->ai_family, get_in_addr((struct sockaddr *)servinfo->ai_addr),
            s, sizeof s);
    printf("client: connecting to %s\n", s);

    freeaddrinfo(servinfo); // all done with this structure

    printf("Please enter the message: ");
    bzero(buf, 256);
    fgets(buf, 255, stdin);

	// Sending message to the server
	if (write(sockfd, buf, strlen(buf)) < 0) {
		perror("ERROR writing to socket");
		return 1;
	}
	numbytes = recv(sockfd, buf, MAXDATASIZE-1, 0);
	// Reading server response
    if (numbytes == -1) {
		perror("ERROR reading from socket");
		return 1;
    }

    buf[numbytes] = '\0';

    printf("client: received '%s'\n",buf);

    close(sockfd);

    return 0;
}
