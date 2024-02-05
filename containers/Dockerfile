FROM python:3-alpine

ADD ../*.sh /funtaxis-lite/
ADD ../containers/launcher.sh /funtaxis-lite/
ADD ../src/* /funtaxis-lite/src/
ADD ../input/add_files /data/input/

RUN apk add bash build-base \
   && python -m pip install --upgrade pip \
   && pip3 install Cython \
   && pip3 install beautifulsoup4 \
   && pip3 install Owlready2

ENTRYPOINT ["bash", "/funtaxis-lite/launcher.sh"]
