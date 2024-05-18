
def backoff_hdlr(details: dict) -> None:
    print(
        f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries "
        f"calling function {details['target'].__name__}\nDetails: {details}"
    )


def remove_nones(original: dict):
    return {k: v for k, v in original.items() if v is not None}


def n_chunks(ls, chunk_size=50):
    super_ls = []
    for i in range(0, len(ls), chunk_size):
        chunk = ls[i : i + chunk_size]
        super_ls.append(chunk)
    return super_ls
