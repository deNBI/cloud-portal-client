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


class Flavor(object):
    """
    This Struct defines a Flavor.

    Attributes:
     - vcpus: The vcpus of the flavor
     - ram: The ram of the flavor
     - disk: The disk of the flavor
     - name: The name of the flavor
     - openstack_id: The openstack_id of the flavor
     - description: The description of the flavor
    """

    thrift_spec = (
        None,  # 0
        (1, TType.I32, 'vcpus', None, None, ),  # 1
        (2, TType.I32, 'ram', None, None, ),  # 2
        (3, TType.I32, 'disk', None, None, ),  # 3
        (4, TType.STRING, 'name', 'UTF8', None, ),  # 4
        (5, TType.STRING, 'openstack_id', 'UTF8', None, ),  # 5
        (6, TType.STRING, 'description', 'UTF8', None, ),  # 6
    )

    def __init__(self, vcpus=None, ram=None, disk=None, name=None, openstack_id=None, description=None,):
        self.vcpus = vcpus
        self.ram = ram
        self.disk = disk
        self.name = name
        self.openstack_id = openstack_id
        self.description = description

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
            elif fid == 6:
                if ftype == TType.STRING:
                    self.description = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
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
        if self.description is not None:
            oprot.writeFieldBegin('description', TType.STRING, 6)
            oprot.writeString(self.description.encode('utf-8') if sys.version_info[0] == 2 else self.description)
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
    This Struct defines an Image.

    Attributes:
     - name: The name of the image
     - min_disk: The min_diks of the image
     - min_ram: The min_ram of the image
     - status: The status of the image
     - created_at: The creation time of the image
     - updated_at: The updated time of the image
     - openstack_id: The openstack_id the image
     - description: The description of the image
     - default_user: The defaut_user of the image
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
        (8, TType.STRING, 'description', 'UTF8', None, ),  # 8
        (9, TType.STRING, 'default_user', 'UTF8', None, ),  # 9
    )

    def __init__(self, name=None, min_disk=None, min_ram=None, status=None, created_at=None, updated_at=None, openstack_id=None, description=None, default_user=None,):
        self.name = name
        self.min_disk = min_disk
        self.min_ram = min_ram
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.openstack_id = openstack_id
        self.description = description
        self.default_user = default_user

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
            elif fid == 8:
                if ftype == TType.STRING:
                    self.description = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 9:
                if ftype == TType.STRING:
                    self.default_user = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
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
        if self.description is not None:
            oprot.writeFieldBegin('description', TType.STRING, 8)
            oprot.writeString(self.description.encode('utf-8') if sys.version_info[0] == 2 else self.description)
            oprot.writeFieldEnd()
        if self.default_user is not None:
            oprot.writeFieldBegin('default_user', TType.STRING, 9)
            oprot.writeString(self.default_user.encode('utf-8') if sys.version_info[0] == 2 else self.default_user)
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
    This Struct defines a VirtualMachine.

    Attributes:
     - flav: The flavor of the VM
     - img: The image of the VM
     - status: The status of the VM
     - metadata: The metadata of the VM
     - project_id: The project_id of the VM
     - keyname: The keyname from the public key of the VM
     - openstack_id: The openstack_id of the VM
     - name: The name of the VM
     - created_at: The the creation time of the VM
     - floating_ip: The floating ip of the VM
     - fixed_ip: The fixed ips of the VM
    """

    thrift_spec = (
        None,  # 0
        (1, TType.STRUCT, 'flav', (Flavor, Flavor.thrift_spec), None, ),  # 1
        (2, TType.STRUCT, 'img', (Image, Image.thrift_spec), None, ),  # 2
        (3, TType.STRING, 'status', 'UTF8', None, ),  # 3
        (4, TType.MAP, 'metadata', (TType.STRING, 'UTF8', TType.STRING, 'UTF8', False), None, ),  # 4
        (5, TType.STRING, 'project_id', 'UTF8', None, ),  # 5
        (6, TType.STRING, 'keyname', 'UTF8', None, ),  # 6
        (7, TType.STRING, 'openstack_id', 'UTF8', None, ),  # 7
        (8, TType.STRING, 'name', 'UTF8', None, ),  # 8
        (9, TType.STRING, 'created_at', 'UTF8', None, ),  # 9
        (10, TType.STRING, 'floating_ip', 'UTF8', None, ),  # 10
        (11, TType.STRING, 'fixed_ip', 'UTF8', None, ),  # 11
    )

    def __init__(self, flav=None, img=None, status=None, metadata=None, project_id=None, keyname=None, openstack_id=None, name=None, created_at=None, floating_ip=None, fixed_ip=None,):
        self.flav = flav
        self.img = img
        self.status = status
        self.metadata = metadata
        self.project_id = project_id
        self.keyname = keyname
        self.openstack_id = openstack_id
        self.name = name
        self.created_at = created_at
        self.floating_ip = floating_ip
        self.fixed_ip = fixed_ip

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
                if ftype == TType.STRING:
                    self.status = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 4:
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
            elif fid == 5:
                if ftype == TType.STRING:
                    self.project_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 6:
                if ftype == TType.STRING:
                    self.keyname = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 7:
                if ftype == TType.STRING:
                    self.openstack_id = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 8:
                if ftype == TType.STRING:
                    self.name = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 9:
                if ftype == TType.STRING:
                    self.created_at = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 10:
                if ftype == TType.STRING:
                    self.floating_ip = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
                else:
                    iprot.skip(ftype)
            elif fid == 11:
                if ftype == TType.STRING:
                    self.fixed_ip = iprot.readString().decode('utf-8') if sys.version_info[0] == 2 else iprot.readString()
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
            oprot.writeFieldBegin('status', TType.STRING, 3)
            oprot.writeString(self.status.encode('utf-8') if sys.version_info[0] == 2 else self.status)
            oprot.writeFieldEnd()
        if self.metadata is not None:
            oprot.writeFieldBegin('metadata', TType.MAP, 4)
            oprot.writeMapBegin(TType.STRING, TType.STRING, len(self.metadata))
            for kiter7, viter8 in self.metadata.items():
                oprot.writeString(kiter7.encode('utf-8') if sys.version_info[0] == 2 else kiter7)
                oprot.writeString(viter8.encode('utf-8') if sys.version_info[0] == 2 else viter8)
            oprot.writeMapEnd()
            oprot.writeFieldEnd()
        if self.project_id is not None:
            oprot.writeFieldBegin('project_id', TType.STRING, 5)
            oprot.writeString(self.project_id.encode('utf-8') if sys.version_info[0] == 2 else self.project_id)
            oprot.writeFieldEnd()
        if self.keyname is not None:
            oprot.writeFieldBegin('keyname', TType.STRING, 6)
            oprot.writeString(self.keyname.encode('utf-8') if sys.version_info[0] == 2 else self.keyname)
            oprot.writeFieldEnd()
        if self.openstack_id is not None:
            oprot.writeFieldBegin('openstack_id', TType.STRING, 7)
            oprot.writeString(self.openstack_id.encode('utf-8') if sys.version_info[0] == 2 else self.openstack_id)
            oprot.writeFieldEnd()
        if self.name is not None:
            oprot.writeFieldBegin('name', TType.STRING, 8)
            oprot.writeString(self.name.encode('utf-8') if sys.version_info[0] == 2 else self.name)
            oprot.writeFieldEnd()
        if self.created_at is not None:
            oprot.writeFieldBegin('created_at', TType.STRING, 9)
            oprot.writeString(self.created_at.encode('utf-8') if sys.version_info[0] == 2 else self.created_at)
            oprot.writeFieldEnd()
        if self.floating_ip is not None:
            oprot.writeFieldBegin('floating_ip', TType.STRING, 10)
            oprot.writeString(self.floating_ip.encode('utf-8') if sys.version_info[0] == 2 else self.floating_ip)
            oprot.writeFieldEnd()
        if self.fixed_ip is not None:
            oprot.writeFieldBegin('fixed_ip', TType.STRING, 11)
            oprot.writeString(self.fixed_ip.encode('utf-8') if sys.version_info[0] == 2 else self.fixed_ip)
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
        if self.openstack_id is None:
            raise TProtocolException(message='Required field openstack_id is unset!')
        if self.name is None:
            raise TProtocolException(message='Required field name is unset!')
        if self.created_at is None:
            raise TProtocolException(message='Required field created_at is unset!')
        if self.fixed_ip is None:
            raise TProtocolException(message='Required field fixed_ip is unset!')
        return

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not (self == other)


class otherException(TException):
    """
    Exceptions inherit from language-specific base exceptions.

    Attributes:
     - Reason: @ Name already used.
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
        oprot.writeStructBegin('otherException')
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


class ressourceException(TException):
    """
    Attributes:
     - Reason: @ Name already used.
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
        oprot.writeStructBegin('ressourceException')
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


class nameException(TException):
    """
    Attributes:
     - Reason: @ Name already used.
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
        oprot.writeStructBegin('nameException')
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


class serverNotFoundException(TException):
    """
    Attributes:
     - Reason: @ Server not found.
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
        oprot.writeStructBegin('serverNotFoundException')
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


class networkNotFoundException(TException):
    """
    Attributes:
     - Reason: @ Network not found.
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
        oprot.writeStructBegin('networkNotFoundException')
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


class imageNotFoundException(TException):
    """
    Attributes:
     - Reason: @ Image not found.
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
        oprot.writeStructBegin('imageNotFoundException')
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


class flavorNotFoundException(TException):
    """
    Attributes:
     - Reason: @ flavor not found.
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
        oprot.writeStructBegin('flavorNotFoundException')
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


class authenticationException(TException):
    """
    Attributes:
     - Reason: @ Authentication failed
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
        oprot.writeStructBegin('authenticationException')
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
