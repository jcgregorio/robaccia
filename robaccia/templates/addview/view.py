from robaccia.defaultcollection import DefaultCollection
from robaccia import render


class Collection(DefaultCollection):

    # GET /{view}/
    def list(self, environ, start_response):
        pass

    # GET /{view}/{id}
    def retrieve(self, environ, start_response):
        pass

    # PUT /{view}/{id}
    def update(self, environ, start_response):
        pass

    # DELETE /{view}/{id}
    def delete(self, environ, start_response):
        pass

    # POST /{view}/
    def create(self, environ, start_response):
        pass

app = Collection('html', render)


