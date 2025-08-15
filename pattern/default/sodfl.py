from ..common import two_pin as tp


def build(pattern, element):
    housing = element['housing']
    housing['sodfl'] = True
    tp.build(pattern, element)

