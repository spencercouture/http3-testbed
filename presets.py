# the dictionary of name->functions to choose from CLI
PRESETS = {}


def register_preset(name):
    def wrapper(func):
        PRESETS[name] = func
        return func
    return wrapper


@register_preset("full_run")
def full_run():
    print("full run!")
