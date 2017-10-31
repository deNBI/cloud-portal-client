#
# Autogenerated by Thrift Compiler (0.10.0)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from thrift.Thrift import TType, TMessageType, TFrozenDict, TException, TApplicationException
from thrift.protocol.TProtocol import TProtocolException
import sys

from thrift.transport import TTransport


class serverStatus(object):
    ACTIVE = 1
    BUilding = 2
    DELETED = 3
    ERROR = 4
    HARD_REBOOT = 5
    PASSWORD = 6
    PAUSED = 7
    REBOOT = 8
    REBUILD = 9
    RESCUED = 10
    RESIZED = 11
    REVERT_RESIZE = 12
    SHUTOFF = 13
    SOFT_DELETED = 14
    STOPPED = 15
    SUSPENDED = 16
    UNKNOWN = 17
    VERIFY_RESIZE = 18

    _VALUES_TO_NAMES = {
        1: "ACTIVE",
        2: "BUilding",
        3: "DELETED",
        4: "ERROR",
        5: "HARD_REBOOT",
        6: "PASSWORD",
        7: "PAUSED",
        8: "REBOOT",
        9: "REBUILD",
        10: "RESCUED",
        11: "RESIZED",
        12: "REVERT_RESIZE",
        13: "SHUTOFF",
        14: "SOFT_DELETED",
        15: "STOPPED",
        16: "SUSPENDED",
        17: "UNKNOWN",
        18: "VERIFY_RESIZE",
    }

    _NAMES_TO_VALUES = {
        "ACTIVE": 1,
        "BUilding": 2,
        "DELETED": 3,
        "ERROR": 4,
        "HARD_REBOOT": 5,
        "PASSWORD": 6,
        "PAUSED": 7,
        "REBOOT": 8,
        "REBUILD": 9,
        "RESCUED": 10,
        "RESIZED": 11,
        "REVERT_RESIZE": 12,
        "SHUTOFF": 13,
        "SOFT_DELETED": 14,
        "STOPPED": 15,
        "SUSPENDED": 16,
        "UNKNOWN": 17,
        "VERIFY_RESIZE": 18,
    }


class Flavor(object):
    """
    structs are mapped by Thrift to classes or structs in your language of
    choice. This struct has two fields, an Identifier of type `id` and
    a Description of type `string`. The Identifier defaults to DEFAULT_ID.

    Attributes:
     - vcpus
     - ram
     - disk
     - name
     - openstack_id
    """

    thrift_spec = (
        None,  # 0
        (1, TType.I32, 'vcpus', None, None, ),  # 1
        (2, TType.I32, 'ram', None, None, ),  # 2
        (3, TType.I32, 'disk', None, None, ),  # 3
        (4, TType.STRING, 'name', 'UTF8', None, ),  # 4
        (5, TType.STRING, 'openstack_id', 'UTF8', None, ),  # 5
    )

    def __init__(self, vcpus=None, ram=None, disk=None, name=None, openstack_id=None,):
        self.vcpus = vcpus
        self.ram = ram
        self.disk = disk
        self.name = name
        self.openstack_id = openstack_id

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, (self.__class__, self.thrift_spec))
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.I32:
                    self.vcpus = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I32:
                    self.ram = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.disk = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.openstack_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('Flavor')
        if self.vcpus is not None:
            oprot.writeFieldBegin('vcpus', TType.I32, 1)
            oprot.writeI32(self.vcpus)
            oprot.writeFieldEnd()
        if self.ram is not None:
            oprot.writeFieldBegin('ram', TType.I32, 2)
            oprot.writeI32(self.ram)
            oprot.writeFieldEnd()
        if self.disk is not None:
            oprot.writeFieldBegin('disk', TType.I32, 3)
            oprot.writeI32(self.disk)
            oprot.writeFieldEnd()
        if self.name is not None:
            oprot.writeFieldBegin('name', TType.STRING, 4)
            oprot.writeString(self.name.encode('utf-8') if sys.version_info[0] == 2 else self.name)
            oprot.writeFieldEnd()
        if self.openstack_id is not None:
            oprot.writeFieldBegin('openstack_id', TType.STRING, 5)
            oprot.writeString(self.openstack_id.encode('utf-8') if sys.version_info[0] == 2 else self.openstack_id)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.vcpus is None:
            raise TProtocolException(message='Required field vcpus is unset!')
        if self.ram is None:
            raise TProtocolException(message='Required field ram is unset!')
        if self.disk is None:
            raise TProtocolException(message='Required field disk is unset!')
        if self.name is None:
            raise TProtocolException(message='Required field name is unset!')
        if self.openstack_id is None:
            raise TProtocolException(message='Required field openstack_id is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class Image(object):
    """
    Attributes:
     - name
     - min_disk
     - min_ram
     - status
     - created_at
     - updated_at
     - openstack_id
    """

    thrift_spec = (
        None,  # 0
        (1, TType.STRING, 'name', 'UTF8', None, ),  # 1
        (2, TType.I32, 'min_disk', None, None, ),  # 2
        (3, TType.I32, 'min_ram', None, None, ),  # 3
        (4, TType.STRING, 'status', 'UTF8', None, ),  # 4
        (5, TType.STRING, 'created_at', 'UTF8', None, ),  # 5
        (6, TType.STRING, 'updated_at', 'UTF8', None, ),  # 6
        (7, TType.STRING, 'openstack_id', 'UTF8', None, ),  # 7
    )

    def __init__(self, name=None, min_disk=None, min_ram=None, status=None, created_at=None, updated_at=None, openstack_id=None,):
        self.name = name
        self.min_disk = min_disk
        self.min_ram = min_ram
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.openstack_id = openstack_id

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, (self.__class__, self.thrift_spec))
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.I32:
                    self.min_disk = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.min_ram = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.status = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.created_at = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.STRING:
                    self.updated_at = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.STRING:
                    self.openstack_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('Image')
        if self.name is not None:
            oprot.writeFieldBegin('name', TType.STRING, 1)
            oprot.writeString(self.name.encode('utf-8') if sys.version_info[0] == 2 else self.name)
            oprot.writeFieldEnd()
        if self.min_disk is not None:
            oprot.writeFieldBegin('min_disk', TType.I32, 2)
            oprot.writeI32(self.min_disk)
            oprot.writeFieldEnd()
        if self.min_ram is not None:
            oprot.writeFieldBegin('min_ram', TType.I32, 3)
            oprot.writeI32(self.min_ram)
            oprot.writeFieldEnd()
        if self.status is not None:
            oprot.writeFieldBegin('status', TType.STRING, 4)
            oprot.writeString(self.status.encode('utf-8') if sys.version_info[0] == 2 else self.status)
            oprot.writeFieldEnd()
        if self.created_at is not None:
            oprot.writeFieldBegin('created_at', TType.STRING, 5)
            oprot.writeString(self.created_at.encode('utf-8') if sys.version_info[0] == 2 else self.created_at)
            oprot.writeFieldEnd()
        if self.updated_at is not None:
            oprot.writeFieldBegin('updated_at', TType.STRING, 6)
            oprot.writeString(self.updated_at.encode('utf-8') if sys.version_info[0] == 2 else self.updated_at)
            oprot.writeFieldEnd()
        if self.openstack_id is not None:
            oprot.writeFieldBegin('openstack_id', TType.STRING, 7)
            oprot.writeString(self.openstack_id.encode('utf-8') if sys.version_info[0] == 2 else self.openstack_id)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.name is None:
            raise TProtocolException(message='Required field name is unset!')
        if self.min_disk is None:
            raise TProtocolException(message='Required field min_disk is unset!')
        if self.min_ram is None:
            raise TProtocolException(message='Required field min_ram is unset!')
        if self.status is None:
            raise TProtocolException(message='Required field status is unset!')
        if self.openstack_id is None:
            raise TProtocolException(message='Required field openstack_id is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class VM(object):
    """
    Attributes:
     - flav: A unique identifier for this task.
     - img
     - status
     - image_id
     - flavor_id
     - metadata
     - project_id
     - keyname
    """

    thrift_spec = (
        None,  # 0
        (1, TType.STRUCT, 'flav', (Flavor, Flavor.thrift_spec), None, ),  # 1
        (2, TType.STRUCT, 'img', (Image, Image.thrift_spec), None, ),  # 2
        (3, TType.I32, 'status', None, None, ),  # 3
        (4, TType.STRING, 'image_id', 'UTF8', None, ),  # 4
        (5, TType.STRING, 'flavor_id', 'UTF8', None, ),  # 5
        (6, TType.MAP, 'metadata', (TType.STRING, 'UTF8', TType.STRING, 'UTF8', False), None, ),  # 6
        (7, TType.STRING, 'project_id', 'UTF8', None, ),  # 7
        (8, TType.STRING, 'keyname', 'UTF8', None, ),  # 8
    )

    def __init__(self, flav=None, img=None, status=None, image_id=None, flavor_id=None, metadata=None, project_id=None, keyname=None,):
        self.flav = flav
        self.img = img
        self.status = status
        self.image_id = image_id
        self.flavor_id = flavor_id
        self.metadata = metadata
        self.project_id = project_id
        self.keyname = keyname

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, (self.__class__, self.thrift_spec))
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRUCT:
                    self.flav = Flavor()
                    self.flav.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 2:
                if ftype == TType.STRUCT:
                    self.img = Image()
                    self.img.read(iprot)
                else:
                    iprot.skip(ftype)
            elif fid == 3:
                if ftype == TType.I32:
                    self.status = iprot.readI32()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
                if ftype == TType.STRING:
                    self.image_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 5:
                if ftype == TType.STRING:
                    self.flavor_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.MAP:
                    self.metadata = {}
                    (_ktype1, _vtype2, _size0) = iprot.readMapBegin()
                    for _i4 in range(_size0):
                        _key5 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        _val6 = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                        self.metadata[_key5] = _val6
                    iprot.readMapEnd()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.STRING:
                    self.project_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.STRING:
                    self.keyname = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('VM')
        if self.flav is not None:
            oprot.writeFieldBegin('flav', TType.STRUCT, 1)
            self.flav.write(oprot)
            oprot.writeFieldEnd()
        if self.img is not None:
            oprot.writeFieldBegin('img', TType.STRUCT, 2)
            self.img.write(oprot)
            oprot.writeFieldEnd()
        if self.status is not None:
            oprot.writeFieldBegin('status', TType.I32, 3)
            oprot.writeI32(self.status)
            oprot.writeFieldEnd()
        if self.image_id is not None:
            oprot.writeFieldBegin('image_id', TType.STRING, 4)
            oprot.writeString(self.image_id.encode('utf-8') if sys.version_info[0] == 2 else self.image_id)
            oprot.writeFieldEnd()
        if self.flavor_id is not None:
            oprot.writeFieldBegin('flavor_id', TType.STRING, 5)
            oprot.writeString(self.flavor_id.encode('utf-8') if sys.version_info[0] == 2 else self.flavor_id)
            oprot.writeFieldEnd()
        if self.metadata is not None:
            oprot.writeFieldBegin('metadata', TType.MAP, 6)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.metadata))
            for kiter7, viter8 in self.metadata.items():
                oprot.writeString(kiter7.encode('utf-8') if sys.version_info[0] == 2 else kiter7)
                oprot.writeString(viter8.encode('utf-8') if sys.version_info[0] == 2 else viter8)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        if self.project_id is not None:
            oprot.writeFieldBegin('project_id', TType.STRING, 7)
            oprot.writeString(self.project_id.encode('utf-8') if sys.version_info[0] == 2 else self.project_id)
            oprot.writeFieldEnd()
        if self.keyname is not None:
            oprot.writeFieldBegin('keyname', TType.STRING, 8)
            oprot.writeString(self.keyname.encode('utf-8') if sys.version_info[0] == 2 else self.keyname)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        if self.flav is None:
            raise TProtocolException(message='Required field flav is unset!')
        if self.img is None:
            raise TProtocolException(message='Required field img is unset!')
        if self.status is None:
            raise TProtocolException(message='Required field status is unset!')
        if self.keyname is None:
            raise TProtocolException(message='Required field keyname is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class instanceException(TException):
    """
    Exceptions inherit from language-specific base exceptions.

    Attributes:
     - Reason: @ The reason for this exception.
    """

    thrift_spec = (
        None,  # 0
        (1, TType.STRING, 'Reason', 'UTF8', None, ),  # 1
    )

    def __init__(self, Reason=None,):
        self.Reason = Reason

    def read(self, iprot):
        if iprot._fast_decode is not None and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None:
            iprot._fast_decode(self, iprot, (self.__class__, self.thrift_spec))
            return
        iprot.readStructBegin()
        while True:
            (fname, ftype, fid) = iprot.readFieldBegin()
            if ftype == TType.STOP:
                break
            if fid == 1:
                if ftype == TType.STRING:
                    self.Reason = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            else:
                iprot.skip(ftype)
            iprot.readFieldEnd()
        iprot.readStructEnd()

    def write(self, oprot):
        if oprot._fast_encode is not None and self.thrift_spec is not None:
            oprot.trans.write(oprot._fast_encode(self, (self.__class__, self.thrift_spec)))
            return
        oprot.writeStructBegin('instanceException')
        if self.Reason is not None:
            oprot.writeFieldBegin('Reason', TType.STRING, 1)
            oprot.writeString(self.Reason.encode('utf-8') if sys.version_info[0] == 2 else self.Reason)
            oprot.writeFieldEnd()
        oprot.writeFieldStop()
        oprot.writeStructEnd()

    def validate(self):
        return

    def __str__(self):
        return repr(self)

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)
