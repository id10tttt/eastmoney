FROM registry.cn-shanghai.aliyuncs.com/odoo-1di0t/odoo:15
MAINTAINER 1di0t

USER root
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple/

USER odoo
