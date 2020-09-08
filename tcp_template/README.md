This code written in C programming language and intended to be build with CMake tool.

To build:
```
$ mkdir build && cd build
$ cmake ..
$ cmake --build .
```

After build you will have two binaries in `build` directory:
* server_linux
* client_linux

To run from `build` directory run following commands (each in separate terminal):
```
$ ./server_linux
$ ./client_linux localhost 5001
```
