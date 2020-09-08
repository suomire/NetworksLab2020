cmake_minimum_required(VERSION 2.8)
project(tcp_template)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra")

set(SERVER_SOURCE_FILES src/server.c)
set(CLIENT_SOURCE_FILES src/client.c)
add_executable(server_linux ${SERVER_SOURCE_FILES})
add_executable(client_linux ${CLIENT_SOURCE_FILES})
