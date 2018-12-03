from pyveda.vedaset.util import _dataset_exists_in_veda
from pyveda.exceptions import RemoteCollectionNotFound

def search(params={}, host=HOST):
    r = conn.post('{}/{}'.format(host, "search"), json=params)
    r.raise_for_status()
    try:
        results = r.json()
        return [VedaCollection.from_doc(s) for s in results]
    except Exception as err:
        print(err)
        return []

def load(dataset_id=None, dataset_name=None, filename=None):
    if not dataset_id or dataset_name or filename:
        raise ValueError("When calling pyveda.load, specify one of: dataset_id, dataset_name, or filename")
    # Check for dataset on veda
    identifier = dataset_id or dataset_name:
    if identifier:
        dataset_id = _dataset_exists_in_veda(identifier):
            if dataset_id:
                return VedaSet.from_id(dataset_id)
    if filename:
        return VedaSet.from_store(filename)
    raise RemoteCollectionNotFound("No Collection found on Veda for identifier: {}".format(identifier))


def load_existing():
    pass

def load_streamer():
    pass

def load_store():
    pass

def _dataset_exists_in_veda(*args, **kwargs):
    pass

