## JSONIC: the decorator
class jsonic(object):
    def __init__(self, **deckeywords):
        self.deckeywords = deckeywords
        self.dic = {}
        self.key = None
        self.thedic = None
        self.recurse_limit = 2

    def __call__(self, fn):
        def include_handler(thefields, include):
            if type(include) == type([]):
                thefields.extend(include)
            else:
                thefields.append(include)

        def skip_handler(thefields, skip):
            if type(skip) == type([]):
                for skipper in skip:
                    if skipper in thefields:
                        thefields.remove(skipper)
            else:
                if skip in thefields:
                    thefields.remove(skip)

        def get_thedic(obj, field):
            try:
                self.thedic = getattr(obj, "%s_set" % field)
            except AttributeError:
                try:
                    self.thedic = getattr(obj, field)
                except AttributeError:
                    pass
                else:
                    self.key = str(field)
            except ObjectDoesNotExist:
                pass
            else:
                self.key = "%s_set" % field

        def key_handler(recurse, kwargs):
            if (
                hasattr(self.thedic, "__class__")
                and hasattr(self.thedic, "all")
                and callable(self.thedic.all)
                and hasattr(self.thedic.all(), "json")
            ):
                if recurse < self.recurse_limit:
                    kwargs["recurse"] = recurse + 1
                    self.dic[self.key] = self.thedic.all().json(**kwargs)
                elif hasattr(self.thedic, "json"):
                    if recurse < self.recurse_limit:
                        kwargs["recurse"] = recurse + 1
                        self.dic[self.key] = self.thedic.json(**kwargs)
                    else:
                        try:
                            theuni = self.thedic.__str__()
                        except UnicodeEncodeError:
                            theuni = self.thedic.encode("utf-8")
                            self.dic[self.key] = theuni

        def check_imagekit(obj):
            if (
                hasattr(obj, "_ik")
                and hasattr(obj, obj._ik.image_field)
                and hasattr(getattr(obj, obj._ik.image_field), "size")
                and getattr(obj, obj._ik.image_field)
            ):
                for ikaccessor in [getattr(obj, s.access_as) for s in obj._ik.specs]:
                    key = ikaccessor.spec.access_as
                    self.dic[key] = {
                        "url": ikaccessor.url,
                        "width": ikaccessor.width,
                        "height": ikaccessor.height,
                    }

        def jsoner(obj, **kwargs):
            thefields = obj._meta.get_all_field_names()
            kwargs.update(self.deckeywords)
            recurse = kwargs.get("recurse", 0)
            include = kwargs.get("include")
            skip = kwargs.get("skip")
            if include:
                include_handler(thefields, include)
            if skip:
                skip_handler(thefields, skip)
            for field in thefields:
                get_thedic(obj, field)
                if self.key:
                    key_handler(recurse)
            check_imagekit(obj)
            return fn(obj, json=self.dic, **kwargs)

        return jsoner
