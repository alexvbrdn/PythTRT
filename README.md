# PythTRT
*A Python Traffic Routing Tool*

## Prerequisites

To run the application you need Python3 and the following packages:
 - termcolor
 - pysocks

The application has currently only been tested on Linux, if you are using another operating system it would be great if you take time to tell me if everything works correctly.

## Introduction
With PythTRT you can distribute your traffic among multiple **links**.
A **link** can be a network interface (Ethernet, Wi-Fi, USB...) or a proxy server (SOCKS5).

PythTRT create a proxy server and by connecting your applications to it you make sure every request sent will be routed
according to the rules defined.

Among all the links you have configured you can set specific routing rules for requests based on the:
- Port number
- Domain pattern or IP range

You can also set a load balancing strategies to dynamically select the best link possible to handle a specific request. 

## How to use ?
First of all you need to precisely define how do you want to use this tool.

### Configuration

Let's see an example of configuration:
```json
{
  "balancer": {
    "links": [
      {
        "protocol": "socks5",
        "domain": "127.0.0.1",
        "port": 1081,
        "matchers": [
          {
            "domains_re": [
              "\\.intranet.com$"
            ],
            "policy": "forbid"
          }
        ]
      },
      {
        "matchers": [
          {
            "domains_re": [
              "\\.intranet.com$"
            ],
            "policy": "allow"
          }
        ]
      }
    ],
    "matchers": [
      {
        "policy": "allow",
        "ports": [
          80,
          443,
          8080
        ]
      }
    ]
  }
}
```
In this configuration all the requests not directed to the domain intranet.com are directed through the SOCKS5 proxy `127.0.0.1:1081`.
Only requests directed to the port 80 (HTTP), 443 (HTTPS) or 8080 (HTTP) are allowed.

### Starting the application
To start the application you have to run the following command:
```bash
$ python3 main.py -i config.json
```
With `config.json` the configuration file.

If you do not want the log to be shown in the console but in a file you can also define the parameter `-l filename`. 

You can now connect to the SOCKS5 server `127.0.0.1:1080` to start routing your traffic.

## Configuration structure

## `Server` *(The root entity)*

The server entity is made of the following entities:
 - `balancer`: [Balancer](#Balancer)
 - `domain`: string *(optional, default=0.0.0.0)*
 - `port`: int *(optional, default=1080)*
 - `timeout`: int *(optional, default=5)*
 - `max_threads`: int *(optional, default=200)*

### `Balancer`
The balancer entity is made of the following entities:
 - `links`: [Link](#Link)[]
 - `strategy`: [Strategy](#Stragegy) *(optional, default=round_robin)*
 - `matchers`: [RequestMatcher](#RequestMatcher)[] *(optional)*

### `Link`

The links are the core of the application, they are the different network interface or/and proxy server the application can connect to.
They are made of the following entities:
 - `timeout`: int *(optional, default=10)*
 - `weight`: int *(optional, default=1)*
 - `interface`: string *(optional, default=)*
 - `protocol`: [Protocol](#Protocol) *(optional, default=direct)*
 - `domain`: string *(optional, default=)*
 - `port`: int *(optional, default=0)*
 - `matchers`: [RequestMatcher](#RequestMatcher)[] *(optional)*

### `Stragegy`

When a request is a received by the application, it applied the specified strategy among the compatible links to decide which link should handle the connection.
Currently the application supports the following strategies:
 - `least_connections` : the application select the link with the least number of active connection
 - `random_link` : the application randomly choose which link handle each connection
 - `round_robin` : the application select the links in sequential order for each connection.

### `Protocol`

By default the protocol is defined as `direct`, if another protocol is chosen the domain and the port need to be defined.
The supported protocols are the following:
 - `direct`
 - `socks5`

### `RequestMatcher`

The request matcher entity is made of the following entities:
 - `policy`: [Policy](#Policy) *(optional, default=forbid)*
 - `domains_re`: string[] *(optional, default=[])*
 - `ports`: int[] *(optional, default=[])*
 

### `Policy`

The policy entity define what behavior the application needs to follow when the received request match the request matcher.
The supported policies are the following:
 - `allow`
    - **match:** the link/balancer can handle the request
    - **not match:** the link/balancer can not handle the request
 - `forbid`
    - **match:** the link/balancer can not handle the request
    - **not match:** the link/balancer can handle the request
 - `deprioritize`
    - **match:** the link can handle the request only if there is no other available link
    - **not match:** the link can handle the request
 - `prioritize`
    - **match:** the link has the priority to handle the request
    - **not match:** the link can handle the request