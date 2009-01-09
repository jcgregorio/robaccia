#!/usr/bin/env python

from wsgiref.handlers import CGIHandler
from urls import urls

def main():
  CGIHandler().run(urls)

if __name__ == '__main__':
  main()
  

