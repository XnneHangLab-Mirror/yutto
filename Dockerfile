FROM alpine:3.24
LABEL maintainer="XnneHangLab-Mirror" \
      version="0.3.0rc1" \
      description="light-weight container based on alpine for uiya-yutto"

RUN set -x \
    && sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories \
    && apk add -q --progress --update --no-cache ffmpeg python3 tzdata \
    && python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --compile --pre uiya-yutto \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

WORKDIR /app

ENTRYPOINT ["/opt/venv/bin/yutto", "-d", "/app"]
