import os
from collections import OrderedDict, defaultdict
import numpy as np
from skimage.io import imread
import tables
import ujson as json
from pyveda.utils import mktempfilename, _atom_from_dtype, from_bounds
from pyveda.exceptions import LabelNotSupported, FrameworkNotSupported
from pyveda.labels import ClassificationLabel, SegmentationLabel, ObjDetectionLabel
from pyveda.vedaset.abstract import BaseVedaSequence
from tempfile import NamedTemporaryFile

class WrappedDataArray(BaseVedaSequence):
    def __init__(self, array, trainer, output_transform=lambda x: x):
        self._arr = array
        self._trainer = trainer
        self._read_transform = output_transform

    @staticmethod
    def _batch_transform(items):
        return np.array(items)

    def _input_fn(self, item):
        return item

    def _output_fn(self, item):
        return item

    def __iter__(self, spec=slice(None)):
        if isinstance(spec, slice):
            for rec in self._arr.iterrows(spec.start, spec.stop, spec.step):
                yield self._read_transform(self._output_fn(rec))
        else:
            for rec in self._arr[spec]:
                yield self._read_transform(self._output_fn(rec))

    def __getitem__(self, spec):
        if isinstance(spec, slice):
            return list(self.__iter__(spec))
        elif isinstance(spec, int):
            return self._read_transform(self._output_fn(self._arr[spec]))
        else:
            return self._arr[spec] # let pytables throw the error

    def __setitem__(self, key, value):
        raise NotSupportedException("For your protection, overwriting raw data in ImageTrainer is not supported.")

    def __len__(self):
        return len(self._arr)

    def append(self, item):
        self._arr.append(self._input_fn(item))

    def append_batch(self, items):
        self.append(items)

    @classmethod
    def create_array(cls, *args, **kwargs):
        raise NotImplementedError


class ImageArray(WrappedDataArray):
    _default_dtype = np.float32

    @staticmethod
    def on_fail(shape=(3, 256, 256), dtype=np.uint8):
        return np.zeros(shape, dtype=dtype)

    @staticmethod
    def bytes_to_array(bstring):
        if bstring is None:
            return on_fail()
        try:
            fd = NamedTemporaryFile(prefix='veda', suffix='.tif', delete=False)
            fd.file.write(bstring)
            fd.file.flush()
            fd.close()
            arr = imread(fd.name)
            if len(arr.shape) == 3:
                arr = np.rollaxis(arr, 2, 0)
            else:
                arr = np.expand_dims(arr, axis=0)
        except Exception as e:
            arr = ImageArray.on_fail()
        finally:
            fd.close()
            os.remove(fd.name)
        return arr

    def _input_fn(self, item):
        dims = item.shape
        if len(dims) == 4:
            return item # for batch append stacked arrays
        elif len(dims) in (2, 3): # extend single image array along axis 0
            return item.reshape(1, *dims)
        return item # what could this thing be, let it fail

    @classmethod
    def create_array(cls, trainer, group, dtype):
        shape = list(trainer.image_shape)
        shape.insert(0,0)
        trainer._fileh.create_earray(group, "images",
                                     atom = _atom_from_dtype(dtype),
                                     shape = tuple(shape))


class LabelArray(WrappedDataArray):
    def __init__(self, hit_table, *args, **kwargs):
        self._table = hit_table
        super(LabelArray, self).__init__(*args, **kwargs)
        self.imshape = self._trainer.image_shape

    def _add_records(self, labels):
        records = [tuple([self._hit_test(label[klass]) for klass in label]) for label in labels]
        self._table.append(records)
        self._table.flush()

    def _hit_test(self, record):
        if isinstance(record, int) and record in (0, 1):
            return record
        elif isinstance(record, list):
            return len(record)
        else:
            raise ValueError("say something")

    def _get_transform(self, bounds, height, width):
        return from_bounds(*bounds, width, height)

    def append(self, label):
        super(LabelArray, self).append(label)
        #self._add_records(label)

    def append_batch(self, labels):
        return self.append(labels)
        #self._add_records(labels)

class ClassificationArray(LabelArray, ClassificationLabel):
    _default_dtype = np.uint8

    def _input_fn(self, item):
        dims = item.shape
        if len(dims) == 2:
            return item # for batch append stacked arrays
        return item.reshape(1, *dims)

    @classmethod
    def create_array(cls, trainer, group, dtype):
        trainer._fileh.create_earray(group, "labels",
                                     atom = tables.UInt8Atom(),
                                     shape = (0, len(trainer.klasses)))


class SegmentationArray(LabelArray, SegmentationLabel):
    _default_dtype = np.float32

    @classmethod
    def create_array(cls, trainer, group, dtype):
        if not dtype:
            dtype = cls._default_dtype
        trainer._fileh.create_earray(group, "labels",
                                     atom = _atom_from_dtype(dtype),
                                     shape = tuple([s if idx > 0 else 0 for idx, s in enumerate(trainer.image_shape)]))


class ObjDetectionArray(LabelArray, ObjDetectionLabel):
    _default_dtype = np.float32

    @staticmethod
    def _batch_transform(items):
        return items

    def _input_fn(self, item):
        assert isinstance(item, list)
        return np.fromstring(json.dumps(item), dtype=np.uint8)

    def _output_fn(self, item):
        return json.loads(item.tostring())

    def append_batch(self, items):
        for item in items:
            self.append(item)

    @classmethod
    def create_array(cls, trainer, group, dtype):
        if not dtype:
            dtype = cls._default_dtype
        trainer._fileh.create_vlarray(group, "labels",
                                      atom = tables.UInt8Atom(),
                                      filters=tables.Filters(complevel=0))

