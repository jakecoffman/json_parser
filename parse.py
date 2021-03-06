# We need a signal
PARSING = object()


def loads(string):
    """ Just like json.loads!
    """
    ret = PARSING

    c = string[0]
    if c == "{":
        p = parse_hash()
        p.send(None)
    elif c == "[":
        p = parse_array()
        p.send(None)
    else:
        raise ValueError("JSON only supports hashes and arrays, not sure what you are doing.")

    for c in string:
        ret = p.send(c)

    if ret is PARSING:
        raise ValueError("Oops, I wasn't done but your JSON string was.")
    return ret


def get_generator(c):
    """ Decides what generator to get, primes it, and returns it
    """
    if c == "{":
        g = parse_hash()
        g.send(None)
        return g
    if c == "[":
        g = parse_array()
        g.send(None)
    if c == '"':
        g = parse_string()
        g.send(None)
        return g
    if c.isdigit():
        g = parse_int()
        g.send(None)
        return g
    raise ValueError("Unknown character alert: " + c)


def parse_hash():
    """ Generator that slowly parses a JSON hash
    """
    hsh = {}

    # Eat the {
    yield PARSING

    c = (yield PARSING)
    while c != "}":
        # json keys are strings, so lets use yet another generator
        key = PARSING
        g = parse_string()
        g.send(None)
        while key is PARSING:
            # so this is fun, send a character to be parsed
            key = g.send(c)
            # and then go back to the top to get another character
            c = (yield PARSING)

        if c != ":":
            raise ValueError("Missing a colon, it looks like this: :")

        # values can be more than just strings...
        value = PARSING
        c = (yield PARSING)
        g = get_generator(c)
        while 1:
            value = g.send(c)
            if value is not PARSING:
                break
            c = (yield PARSING)

        hsh[key] = value
        # Eat another character? I think this could be cleaner...
        if g.send(None):
            c = (yield PARSING)

    yield hsh
    yield True  # the final yield tells me if I need to clean up a character or not


def parse_string():
    """ Generator that slowly parses a string
    """
    string = []  # we have to use an array because python strings are immutable

    yield PARSING  # eat the ", execution can't get in here without one
    while True:
        c = (yield PARSING)
        if c == '"':
            break
        string.append(c)

    yield ''.join(string)
    yield True


def parse_int():
    """ Generator that slowly parses an integer
    """
    integer = []
    c = (yield PARSING)
    while c not in [',', '}', ']']:
        integer.append(c)
        c = (yield PARSING)

    yield int(''.join(integer))
    yield False


def parse_array():
    """ Generator that slowly parses an array
    """
    array = []

    c = (yield PARSING)
    while c != "]":
        value = PARSING
        c = (yield PARSING)
        if c == ']':
            break
        g = get_generator(c)
        while True:
            value = g.send(c)
            if value is not PARSING:
                break
            c = (yield PARSING)

        array.append(value)
        # Eat another character? I think this could be cleaner...
        if g.send(None):
            c = (yield PARSING)
    yield array