FROM ubuntu:22.04

# 更改 Ubuntu 镜像源为中国境内源
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list

# 设置环境变量
ENV TERM xterm
ENV TZ Etc/UTC
ENV DEBIAN_FRONTEND noninteractive

# 安装所需软件包
RUN apt-get update && \
    apt-get install -y whiptail apt-utils curl sudo systemd python2 python3 python3-pip xxd lsof && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /opt/hiddify-manager/
COPY . .

# 运行安装脚本
RUN chmod +x install.sh && \
    bash install.sh install-docker

# 下载 systemctl 替代脚本
RUN curl -L https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/master/files/docker/systemctl.py -o /usr/bin/systemctl && \
    chmod +x /usr/bin/systemctl

# 安装 Python 依赖
RUN pip3 install -r requirements.txt

# 暴露端口
EXPOSE 80 443

# 设置默认的入口点和命令
ENTRYPOINT ["/bin/bash", "-c", "./apply_configs.sh && tail -f /opt/hiddify-manager/log/system/*"]
CMD ["flask", "run", "--port", "443"]
