FROM python:3-alpine

ADD ../*.sh /funtaxis-lite/
ADD ../add_files/ /funtaxis-lite/input/add_files/
ADD ../src/ /funtaxis-lite/src/

RUN apk add bash build-base \
   && python -m pip install --upgrade pip \
   && pip3 install Cython \
   && pip3 install beautifulsoup4 \
   && pip3 install Owlready2

ENTRYPOINT ["bash", "/funtaxis-lite/containers/launcher.sh"]
