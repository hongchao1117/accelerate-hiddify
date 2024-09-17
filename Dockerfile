FROM ubuntu:22.04

# 将 Ubuntu 镜像源更改为中国境内源
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list
# 添加其他构建步骤，例如安装软件包、设置环境变量等
EXPOSE 80
EXPOSE 443

RUN apt-get update && apt-get install -y whiptail apt-utils curl sudo systemd python2 xxd lsof

ENV TERM xterm
ENV TZ Etc/UTC
ENV DEBIAN_FRONTEND noninteractive

USER root
WORKDIR /opt/hiddify-manager/
COPY . .
# RUN mkdir -p ~/.ssh && echo "StrictHostKeyChecking no " > ~/.ssh/config
RUN bash install.sh install-docker
RUN curl -L https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/master/files/docker/systemctl.py -o /usr/bin/systemctl
RUN pip install -r requirements.txt
ENTRYPOINT ["/bin/bash","-c", "./apply_configs.sh && tail -f /opt/hiddify-manager/log/system/*"]
CMD [ "flask", "run", "--port", "443" ]