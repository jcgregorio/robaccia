import view
from wsgidispatcher import Dispatcher


urls = Dispatcher()

urls.add('/blog/', GET=view.index, POST=view.create)
urls.add('/blog/{id}/', view.member_get)
urls.add('/blog/{id}/edit_form', GET=view.member_edit_form, POST=view.member_update)

