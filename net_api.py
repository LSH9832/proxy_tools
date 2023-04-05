import os


def get_now_proxy():

    proxy_map = {}

    for line in os.popen("netsh interface portproxy show v4tov4").read().split("\n")[5:-2]:
        _, port_to, ip_from, port_from = line.split()

        proxy_map[ip_from] = proxy_map.get(ip_from) or [[], []]
        proxy_map[ip_from][0].append(int(port_from))
        proxy_map[ip_from][1].append(int(port_to))

    ret = {}

    ports_used = []

    for k, v in proxy_map.items():
        groups = []
        ports_from, ports_to = v
        ports_used.extend(ports_to)

        count_start_from = -1
        count_start_to = -1
        this_group = []
        end_ = None
        for port_from, port_to in sorted(zip(ports_from, ports_to)):
            if count_start_from == -1:
                count_start_from = port_from
                count_start_to = port_to
                this_group.extend([count_start_from, count_start_to])
                end_ = None
            else:
                if port_from - count_start_from == port_to - count_start_to == 1:
                    end_ = [port_from, port_to]
                    count_start_from = port_from
                    count_start_to = port_to
                else:
                    if end_ is not None:
                        this_group.extend(end_)
                    groups.append(this_group)
                    count_start_from = port_from
                    count_start_to = port_to
                    this_group = [count_start_from, count_start_to]
                    end_ = None


        if end_ is not None:
            this_group.extend(end_)
        groups.append(this_group)

        ret[k] = groups

    print(ret, ports_used)
    return ret, ports_used


def add_rule(ip_from, port_from, port_to):
    command = f"netsh interface portproxy add v4tov4 " \
              f"listenport={port_to} listenaddress=0.0.0.0 connectport={port_from} connectaddress={ip_from}"

    os.popen(command)

    os.popen(
        f"netsh advfirewall firewall add rule "
        f"name=PROXY_TOOLS_{port_to} "
        f"dir=in "
        f"action=allow "
        f"protocol=TCP "
        f"localport={port_to}"
    )


def remove_rule(port_to):
    command = f"netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport={port_to}"
    os.popen(command)
    os.popen(f"netsh advfirewall firewall delete rule name=PROXY_TOOLS_{port_to}")


if __name__ == '__main__':
    print(get_now_proxy())
