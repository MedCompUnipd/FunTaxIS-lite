FROM python:3-alpine

ADD ../*.sh /funtaxis-lite/
ADD ../input/add_files /funtaxis-lite/input/
ADD ../src/* /funtaxis-lite/src/
ADD ../containers/launcher.sh /funtaxis-lite/containers/

RUN apk add bash build-base \
   && python -m pip install --upgrade pip \
   && pip3 install Cython \
   && pip3 install beautifulsoup4 \
   && pip3 install Owlready2

ENTRYPOINT ["bash", "/funtaxis-lite/containers/launcher.sh"]
