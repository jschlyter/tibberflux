FROM python:3.9
WORKDIR /tmp
COPY dist/tibberflux-*.whl ./
RUN pip3 install tibberflux-*.whl
RUN rm tibberflux-*.whl
CMD ["tibberflux"]
